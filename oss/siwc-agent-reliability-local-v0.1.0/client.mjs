#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { execFile } from "node:child_process";

export const AUTH = "https://auth.openai.com/api/accounts/authorize";
export const TOKEN = "https://auth.openai.com/api/accounts/oauth/token";
export const JWKS = "https://auth.openai.com/.well-known/jwks.json";
export const API = "https://api.openai.com/v1";
export const DYNAMIC = "dynamic_agent_client";
export const SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct";

const home = () => process.env.RUMBO_SIWC_HOME || path.join(
  process.platform === "win32"
    ? (process.env.APPDATA || path.join(os.homedir(), "AppData", "Roaming"))
    : (process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config")),
  "rumbo-agent-reliability-local"
);

const b64u = b => Buffer.from(b).toString("base64url");
export const pkce = () => {
  const verifier = b64u(crypto.randomBytes(48));
  return { verifier, challenge: b64u(crypto.createHash("sha256").update(verifier).digest()) };
};
export const random = () => b64u(crypto.randomBytes(32));

function privateWrite(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + "\n", { mode: 0o600 });
  fs.renameSync(tmp, file);
  try { fs.chmodSync(file, 0o600); } catch {}
}
const read = file => fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) : null;

export function hostId(dir = home()) {
  const file = path.join(dir, "host.json");
  const saved = read(file);
  if (saved?.ext_agent_host_id) return saved.ext_agent_host_id;
  const value = `urn:uuid:${crypto.randomUUID()}`;
  privateWrite(file, { ext_agent_host_id: value });
  return value;
}

export function authUrl({ redirectUri, state, nonce, challenge, extAgentHostId, clientId = DYNAMIC, loginHint, idTokenHint }) {
  const u = new URL(AUTH);
  const p = u.searchParams;
  p.set("client_id", clientId);
  if (clientId === DYNAMIC) p.set("agent_name_hint", "RUMBO Agent Reliability Local");
  p.set("ext_agent_host_id", extAgentHostId);
  p.set("response_type", "code");
  p.set("redirect_uri", redirectUri);
  p.set("scope", SCOPES);
  p.set("resource", API);
  p.set("state", state);
  p.set("nonce", nonce);
  p.set("code_challenge_method", "S256");
  p.set("code_challenge", challenge);
  if (loginHint) p.set("login_hint", loginHint);
  if (idTokenHint) p.set("id_token_hint", idTokenHint);
  return u.toString();
}

function jwtPart(x) { return JSON.parse(Buffer.from(x, "base64url").toString("utf8")); }

export function verifyIdToken(jwt, jwks, audience, nonce, now = Date.now()/1000) {
  const [h,p,s] = jwt.split(".");
  if (!h || !p || !s) throw new Error("Malformed ID token");
  const header = jwtPart(h), body = jwtPart(p);
  if (header.alg !== "RS256") throw new Error("Unexpected ID token algorithm");
  const jwk = (jwks.keys || []).find(k => k.kid === header.kid && k.kty === "RSA");
  if (!jwk) throw new Error("JWKS key not found");
  const key = crypto.createPublicKey({ key: jwk, format: "jwk" });
  if (!crypto.verify("RSA-SHA256", Buffer.from(`${h}.${p}`), key, Buffer.from(s, "base64url")))
    throw new Error("Bad ID token signature");
  if (body.iss !== "https://auth.openai.com") throw new Error("Issuer mismatch");
  const aud = Array.isArray(body.aud) ? body.aud : [body.aud];
  if (!aud.includes(audience)) throw new Error("Audience mismatch");
  if (body.nonce !== nonce) throw new Error("Nonce mismatch");
  if (!body.exp || body.exp <= now) throw new Error("Expired ID token");
  if (!body.sub) throw new Error("Missing subject");
  return body;
}

async function form(url, fields) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(fields)
  });
  const text = await r.text();
  let body; try { body = JSON.parse(text) } catch { body = { raw: text } }
  if (!r.ok) throw Object.assign(new Error(`HTTP ${r.status}`), { body });
  return body;
}

function open(url) {
  const cmd = process.platform === "win32"
    ? ["cmd", ["/c", "start", "", url]]
    : process.platform === "darwin"
    ? ["open", [url]]
    : ["xdg-open", [url]];
  try { const c = execFile(cmd[0], cmd[1], { windowsHide: true }); c.unref(); } catch {}
}

const credFile = () => path.join(home(), "credentials.json");

async function signin() {
  const saved = read(credFile());
  const clientId = saved?.client_id || DYNAMIC;
  const state = random(), nonce = random(), { verifier, challenge } = pkce();
  const server = http.createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const redirectUri = `http://127.0.0.1:${server.address().port}/auth/callback`;
  const url = authUrl({
    redirectUri, state, nonce, challenge,
    extAgentHostId: hostId(),
    clientId,
    loginHint: saved?.email,
    idTokenHint: saved?.id_token
  });
  console.log("Continue with ChatGPT:");
  console.log(url.replace(/id_token_hint=[^&]+/, "id_token_hint=<redacted>"));
  open(url);

  const callback = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("OAuth callback timeout")), 300000);
    server.on("request", (req, res) => {
      const u = new URL(req.url, redirectUri);
      if (u.pathname !== "/auth/callback") return res.writeHead(404).end();
      if (u.searchParams.get("state") !== state) return res.writeHead(400).end("state mismatch");
      if (u.searchParams.get("error")) return reject(new Error(`OAuth error: ${u.searchParams.get("error")}`));
      const code = u.searchParams.get("code");
      const issued = u.searchParams.get("client_id") || (clientId !== DYNAMIC ? clientId : null);
      if (!code || !issued) return reject(new Error("Missing code/client_id"));
      if (clientId !== DYNAMIC && issued !== clientId) return reject(new Error("Client ID mismatch"));
      clearTimeout(timer);
      res.writeHead(200, { "content-type": "text/plain" }).end("Connected. You may close this window.");
      resolve({ code, issued });
    });
  }).finally(() => server.close());

  const tokens = await form(TOKEN, {
    grant_type: "authorization_code",
    client_id: callback.issued,
    code: callback.code,
    code_verifier: verifier,
    redirect_uri: redirectUri,
    resource: API
  });
  const jr = await fetch(JWKS); if (!jr.ok) throw new Error(`JWKS HTTP ${jr.status}`);
  const identity = verifyIdToken(tokens.id_token, await jr.json(), callback.issued, nonce);
  const scopes = String(tokens.scope || "").split(/\s+/).filter(Boolean).sort();
  privateWrite(credFile(), {
    email: identity.email || null,
    subject: identity.sub,
    issuer: identity.iss,
    client_id: callback.issued,
    ext_agent_host_id: hostId(),
    id_token: tokens.id_token,
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token,
    expires_in: tokens.expires_in,
    scopes,
    saved_at: new Date().toISOString()
  });
  console.log(JSON.stringify({
    connected: true,
    email: identity.email || null,
    client_id: callback.issued,
    plan_usage_enabled: scopes.includes("chatgpt.tokens.use.direct")
  }, null, 2));
}

async function credential() {
  let c = read(credFile());
  if (!c) throw new Error("Run signin first");
  if (Date.now() - Date.parse(c.saved_at) > 45*60*1000 && c.refresh_token) {
    const t = await form(TOKEN, {
      grant_type: "refresh_token",
      client_id: c.client_id,
      refresh_token: c.refresh_token,
      resource: API
    });
    c = {
      ...c,
      access_token: t.access_token,
      refresh_token: t.refresh_token || c.refresh_token,
      id_token: t.id_token || c.id_token,
      expires_in: t.expires_in,
      scopes: String(t.scope || c.scopes.join(" ")).split(/\s+/).filter(Boolean).sort(),
      saved_at: new Date().toISOString()
    };
    privateWrite(credFile(), c);
  }
  return c;
}

async function models() {
  const c = await credential();
  const r = await fetch(`${API}/models`, { headers: { authorization: `Bearer ${c.access_token}` }});
  const body = await r.json(); if (!r.ok) throw new Error(`Models HTTP ${r.status}`);
  console.log(JSON.stringify((body.models || []).filter(m=>m.visibility==="list").map(m=>({slug:m.slug,display_name:m.display_name})), null, 2));
}

async function ask(model, prompt) {
  const c = await credential();
  if (!c.scopes.includes("chatgpt.tokens.use.direct")) throw new Error("Plan usage not authorized");
  const r = await fetch(`${API}/responses`, {
    method: "POST",
    headers: { authorization: `Bearer ${c.access_token}`, "content-type": "application/json" },
    body: JSON.stringify({
      model,
      input: [{ role: "user", content: prompt }],
      instructions: "RUMBO Agent Reliability Local: evidence-first; fail closed on material ambiguity; no consequential writes without explicit authorization.",
      store: false,
      stream: true
    })
  });
  if (!r.ok) throw new Error(`Responses HTTP ${r.status}: ${await r.text()}`);
  let buf="", done=false; const decoder=new TextDecoder();
  for await (const chunk of r.body) {
    buf += decoder.decode(chunk,{stream:true});
    for (;;) {
      const i=buf.indexOf("\n\n"); if(i<0) break;
      const block=buf.slice(0,i); buf=buf.slice(i+2);
      for (const line of block.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const raw=line.slice(5).trim(); if(!raw || raw==="[DONE]") continue;
        let e; try { e=JSON.parse(raw) } catch { continue }
        if(e.type==="response.output_text.delta") process.stdout.write(e.delta || "");
        if(e.type==="response.failed") throw new Error(`Response failed: ${e.response?.error?.code || "unknown"}`);
        if(e.type==="response.completed") done=true;
      }
    }
  }
  if(!done) throw new Error("Stream ended without response.completed");
  process.stdout.write("\n");
}

async function main() {
  const [cmd,...args]=process.argv.slice(2);
  if(cmd==="signin") return signin();
  if(cmd==="status") {
    const c=read(credFile());
    return console.log(JSON.stringify(c ? {
      connected:true,email:c.email,client_id:c.client_id,
      plan_usage_enabled:c.scopes?.includes("chatgpt.tokens.use.direct"),
      access_token_present:Boolean(c.access_token),refresh_token_present:Boolean(c.refresh_token)
    } : {connected:false}, null, 2));
  }
  if(cmd==="models") return models();
  if(cmd==="ask") {
    const i=args.indexOf("--model"); if(i<0 || !args[i+1]) throw new Error("--model required");
    const model=args[i+1], prompt=args.filter((_,j)=>j!==i&&j!==i+1).join(" ").trim();
    if(!prompt) throw new Error("prompt required");
    return ask(model,prompt);
  }
  console.log("Usage: node client.mjs signin|status|models|ask --model <slug> <prompt>");
}
if (import.meta.url === `file://${process.argv[1]}`) main().catch(e=>{console.error(e.message);process.exitCode=1});
