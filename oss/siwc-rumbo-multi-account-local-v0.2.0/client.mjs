#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { execFile, spawn } from "node:child_process";

export const AUTH = "https://auth.openai.com/api/accounts/authorize";
export const TOKEN = "https://auth.openai.com/api/accounts/oauth/token";
export const JWKS = "https://auth.openai.com/.well-known/jwks.json";
export const OIDC = "https://auth.openai.com/.well-known/openid-configuration";
export const API = "https://api.openai.com/v1";
export const DYNAMIC = "dynamic_agent_client";
export const SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct";
export const AGENT_NAME = "RUMBO Multi-Account Local";

export const home = () => process.env.RUMBO_SIWC_HOME || path.join(
  process.platform === "win32"
    ? (process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"))
    : (process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config")),
  "RUMBO", "SIWC"
);

const b64u = b => Buffer.from(b).toString("base64url");
export const pkce = () => {
  const verifier = b64u(crypto.randomBytes(48));
  return { verifier, challenge: b64u(crypto.createHash("sha256").update(verifier).digest()) };
};
export const random = () => b64u(crypto.randomBytes(32));

function atomicJson(file, value, mode = 0o600) {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const tmp = `${file}.${process.pid}.${crypto.randomBytes(4).toString("hex")}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + "\n", { mode });
  fs.renameSync(tmp, file);
  try { fs.chmodSync(file, mode); } catch {}
}
const readJson = file => fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) : null;

function indexFile(dir = home()) { return path.join(dir, "accounts.json"); }
function activeFile(dir = home()) { return path.join(dir, "active.json"); }
function secretDir(dir = home()) { return path.join(dir, "secrets"); }

export function hostId(dir = home()) {
  const file = path.join(dir, "host.json");
  const saved = readJson(file);
  if (saved?.ext_agent_host_id) return saved.ext_agent_host_id;
  const value = `urn:uuid:${crypto.randomUUID()}`;
  atomicJson(file, { ext_agent_host_id: value }, 0o600);
  return value;
}

export function authUrl({ redirectUri, state, nonce, challenge, extAgentHostId, clientId = DYNAMIC, loginHint, idTokenHint }) {
  const u = new URL(AUTH);
  const p = u.searchParams;
  p.set("client_id", clientId);
  if (clientId === DYNAMIC) p.set("agent_name_hint", AGENT_NAME);
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
  const [h,p,s] = String(jwt || "").split(".");
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
  if (body.nbf && body.nbf > now + 30) throw new Error("ID token not active");
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

function runPowerShell(script, input) {
  return new Promise((resolve, reject) => {
    const p = spawn("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", script], {
      stdio: ["pipe", "pipe", "pipe"], windowsHide: true
    });
    let out="", err="";
    p.stdout.setEncoding("utf8"); p.stderr.setEncoding("utf8");
    p.stdout.on("data", d => out += d); p.stderr.on("data", d => err += d);
    p.on("error", reject);
    p.on("close", code => code === 0 ? resolve(out.trim()) : reject(new Error(`DPAPI helper failed (${code})`)));
    p.stdin.end(input, "utf8");
  });
}

async function protectSecret(value) {
  const text = JSON.stringify(value);
  if (process.platform !== "win32") return { format: "json-v1", payload: text };
  const script = '$s=[Console]::In.ReadToEnd();$b=[Text.Encoding]::UTF8.GetBytes($s);$e=[Security.Cryptography.ProtectedData]::Protect($b,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser);[Convert]::ToBase64String($e)';
  return { format: "dpapi-current-user-v1", payload: await runPowerShell(script, text) };
}

async function unprotectSecret(envelope) {
  if (envelope?.format === "json-v1") return JSON.parse(envelope.payload);
  if (envelope?.format !== "dpapi-current-user-v1" || process.platform !== "win32") throw new Error("Unsupported protected credential format on this host");
  const script = '$s=[Console]::In.ReadToEnd();$e=[Convert]::FromBase64String($s.Trim());$b=[Security.Cryptography.ProtectedData]::Unprotect($e,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser);[Text.Encoding]::UTF8.GetString($b)';
  return JSON.parse(await runPowerShell(script, envelope.payload));
}

function loadIndex(dir = home()) {
  const x = readJson(indexFile(dir));
  return x?.schema === "rumbo.siwc.accounts/v2" && Array.isArray(x.accounts) ? x : { schema:"rumbo.siwc.accounts/v2", accounts:[] };
}
function saveIndex(index, dir = home()) { atomicJson(indexFile(dir), index, 0o600); }
function accountById(id, dir = home()) {
  const a = loadIndex(dir).accounts.find(x => x.id === id);
  if (!a) throw new Error(`Unknown account id: ${id}`);
  return a;
}
function activeId(dir = home()) { return readJson(activeFile(dir))?.account_id || null; }
function setActive(id, dir = home()) { accountById(id, dir); atomicJson(activeFile(dir), {account_id:id}, 0o600); }
function secretPath(id, dir = home()) { return path.join(secretDir(dir), `${id}.secret.json`); }
async function writeSecret(id, secret, dir = home()) {
  fs.mkdirSync(secretDir(dir), {recursive:true, mode:0o700});
  atomicJson(secretPath(id, dir), await protectSecret(secret), 0o600);
}
async function readSecret(id, dir = home()) {
  const env = readJson(secretPath(id, dir));
  if (!env) throw new Error(`Credentials unavailable for account: ${id}`);
  return unprotectSecret(env);
}
function deleteSecret(id, dir = home()) { try { fs.rmSync(secretPath(id, dir), {force:true}); } catch {} }

export function sanitizeAccount(account) {
  return {
    id: account.id,
    label: account.label,
    email: account.email || null,
    client_id: account.client_id,
    subject: account.subject,
    plan_usage_enabled: Boolean(account.plan_usage_enabled),
    signed_in: fs.existsSync(secretPath(account.id)),
    active: activeId() === account.id
  };
}

function parseFlags(args) {
  const out = { _: [] };
  for (let i=0;i<args.length;i++) {
    if (args[i].startsWith("--")) {
      const k=args[i].slice(2); const v=args[i+1] && !args[i+1].startsWith("--") ? args[++i] : true; out[k]=v;
    } else out._.push(args[i]);
  }
  return out;
}

async function signIn({ accountId, label }) {
  const dir=home();
  const returning = accountId ? accountById(accountId, dir) : null;
  const previousSecret = returning && fs.existsSync(secretPath(returning.id,dir)) ? await readSecret(returning.id,dir) : null;
  const clientId = returning?.client_id || DYNAMIC;
  const state=random(), nonce=random(), {verifier,challenge}=pkce();
  const server=http.createServer();
  await new Promise((resolve,reject)=>{server.once("error",reject);server.listen(0,"127.0.0.1",resolve);});
  const redirectUri=`http://127.0.0.1:${server.address().port}/auth/callback`;
  const url=authUrl({
    redirectUri,state,nonce,challenge,extAgentHostId:hostId(dir),clientId,
    loginHint:returning?.email || undefined,
    idTokenHint:previousSecret?.id_token || undefined
  });
  console.log(`Continue with ChatGPT for ${returning?.label || label || "new account"}.`);
  console.log(url.replace(/id_token_hint=[^&]+/,"id_token_hint=<redacted>"));
  open(url);
  const callback=await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error("OAuth callback timeout")),300000);
    server.on("request",(req,res)=>{
      const u=new URL(req.url,redirectUri);
      if(u.pathname!=="/auth/callback") return res.writeHead(404).end();
      if(u.searchParams.get("state")!==state) return res.writeHead(400).end("state mismatch");
      if(u.searchParams.get("error")){clearTimeout(timer);res.writeHead(400).end("Authorization declined.");return reject(new Error(`OAuth error: ${u.searchParams.get("error")}`));}
      const code=u.searchParams.get("code");
      const issued=u.searchParams.get("client_id") || (clientId!==DYNAMIC?clientId:null);
      if(!code||!issued){clearTimeout(timer);return reject(new Error("Missing code/client_id"));}
      if(clientId!==DYNAMIC&&issued!==clientId){clearTimeout(timer);return reject(new Error("Client ID mismatch"));}
      clearTimeout(timer);res.writeHead(200,{"content-type":"text/plain"}).end("Connected. You may close this window.");resolve({code,issued});
    });
  }).finally(()=>server.close());

  const tokens=await form(TOKEN,{grant_type:"authorization_code",client_id:callback.issued,code:callback.code,code_verifier:verifier,redirect_uri:redirectUri,resource:API});
  const jr=await fetch(JWKS); if(!jr.ok) throw new Error(`JWKS HTTP ${jr.status}`);
  const identity=verifyIdToken(tokens.id_token,await jr.json(),callback.issued,nonce);
  if(returning && returning.subject!==identity.sub) throw new Error("Returning account identity mismatch");
  const scopes=String(tokens.scope||"").split(/\s+/).filter(Boolean).sort();
  const index=loadIndex(dir);
  let account=returning;
  if(!account){
    account={
      id:crypto.randomUUID(),
      label:String(label||identity.email||`ChatGPT ${index.accounts.length+1}`).slice(0,80),
      email:identity.email||null,
      subject:identity.sub,
      client_id:callback.issued,
      ext_agent_host_id:hostId(dir),
      created_at:new Date().toISOString(),
      plan_usage_enabled:scopes.includes("chatgpt.tokens.use.direct")
    };
    if(index.accounts.some(x=>x.client_id===account.client_id)) throw new Error("Issued client already registered locally");
    index.accounts.push(account);
  } else {
    account.email=identity.email||account.email||null;
    account.plan_usage_enabled=scopes.includes("chatgpt.tokens.use.direct");
    account.updated_at=new Date().toISOString();
  }
  const now=Date.now();
  await writeSecret(account.id,{
    id_token:tokens.id_token,
    access_token:tokens.access_token,
    refresh_token:tokens.refresh_token,
    expires_at:now+(Number(tokens.expires_in||3600)*1000),
    earliest_refresh_at:tokens.earliest_refresh_at||null,
    scopes,
    saved_at:new Date(now).toISOString()
  },dir);
  saveIndex(index,dir); setActive(account.id,dir);
  console.log(JSON.stringify({connected:true,...sanitizeAccount(account)},null,2));
}

async function withRefreshLock(accountId, fn, dir=home()) {
  const file=path.join(dir,"locks",`${accountId}.refresh.lock`); fs.mkdirSync(path.dirname(file),{recursive:true});
  let fd;
  try { fd=fs.openSync(file,"wx",0o600); } catch(e) { if(e.code==="EEXIST") throw new Error("Refresh already in progress for this account"); throw e; }
  try { return await fn(); } finally { try{fs.closeSync(fd);}catch{} try{fs.rmSync(file,{force:true});}catch{} }
}

async function credential(accountId = activeId(), dir = home()) {
  if(!accountId) throw new Error("No active account. Run list/use/signin first.");
  const account=accountById(accountId,dir);
  let secret=await readSecret(accountId,dir);
  const now=Date.now();
  const earliest = secret.earliest_refresh_at ? Date.parse(secret.earliest_refresh_at) : 0;
  const refreshAllowed = !earliest || Number.isNaN(earliest) || now >= earliest;
  if(Number(secret.expires_at||0)-now <= 5*60*1000 && secret.refresh_token && refreshAllowed){
    secret=await withRefreshLock(accountId, async()=>{
      let current=await readSecret(accountId,dir);
      const currentNow=Date.now();
      const currentEarliest=current.earliest_refresh_at ? Date.parse(current.earliest_refresh_at) : 0;
      const currentAllowed=!currentEarliest || Number.isNaN(currentEarliest) || currentNow >= currentEarliest;
      if(Number(current.expires_at||0)-currentNow>5*60*1000 || !currentAllowed) return current;
      const t=await form(TOKEN,{grant_type:"refresh_token",client_id:account.client_id,refresh_token:current.refresh_token,resource:API});
      const scopes=String(t.scope||current.scopes?.join(" ")||"").split(/\s+/).filter(Boolean).sort();
      const next={...current,access_token:t.access_token,refresh_token:t.refresh_token||current.refresh_token,id_token:t.id_token||current.id_token,expires_at:Date.now()+(Number(t.expires_in||3600)*1000),earliest_refresh_at:t.earliest_refresh_at||current.earliest_refresh_at||null,scopes,saved_at:new Date().toISOString()};
      await writeSecret(accountId,next,dir); return next;
    },dir);
  }
  return {account,secret};
}

async function listAccounts() {
  const index=loadIndex(); console.log(JSON.stringify({host_id:hostId(),active_account_id:activeId(),accounts:index.accounts.map(sanitizeAccount)},null,2));
}
async function status(accountId=activeId()) {
  if(!accountId) return console.log(JSON.stringify({connected:false,reason:"NO_ACTIVE_ACCOUNT"},null,2));
  const a=accountById(accountId); console.log(JSON.stringify(sanitizeAccount(a),null,2));
}
async function useAccount(id) { setActive(id); await status(id); }

async function models() {
  const {secret}=await credential();
  const r=await fetch(`${API}/models`,{headers:{authorization:`Bearer ${secret.access_token}`}});
  const body=await r.json(); if(!r.ok) throw new Error(`Models HTTP ${r.status}`);
  console.log(JSON.stringify((body.models||[]).filter(m=>m.visibility==="list").map(m=>({slug:m.slug,display_name:m.display_name})),null,2));
}

async function ask(model,prompt) {
  const {account,secret}=await credential();
  if(!secret.scopes?.includes("chatgpt.tokens.use.direct")) throw new Error("Plan usage not authorized for active account");
  const r=await fetch(`${API}/responses`,{
    method:"POST",headers:{authorization:`Bearer ${secret.access_token}`,"content-type":"application/json"},
    body:JSON.stringify({model,input:[{role:"user",content:prompt}],instructions:"RUMBO local runtime: evidence-first; fail closed on material ambiguity; no consequential writes without explicit authorization.",store:false,stream:true})
  });
  if(!r.ok) throw new Error(`Responses HTTP ${r.status}: ${await r.text()}`);
  let buf="",done=false;const decoder=new TextDecoder();
  for await(const chunk of r.body){buf+=decoder.decode(chunk,{stream:true});for(;;){const i=buf.indexOf("\n\n");if(i<0)break;const block=buf.slice(0,i);buf=buf.slice(i+2);for(const line of block.split("\n")){if(!line.startsWith("data:"))continue;const raw=line.slice(5).trim();if(!raw||raw==="[DONE]")continue;let e;try{e=JSON.parse(raw)}catch{continue}if(e.type==="response.output_text.delta")process.stdout.write(e.delta||"");if(e.type==="response.failed")throw new Error(`Response failed: ${e.response?.error?.code||"unknown"}`);if(e.type==="response.completed")done=true;}}}
  if(!done) throw new Error("Stream ended without response.completed");
  process.stdout.write(`\n[account:${account.label}]\n`);
}

async function codexServer() {
  const {account,secret}=await credential();
  if(!secret.scopes?.includes("chatgpt.tokens.use.direct")) throw new Error("Plan usage not authorized for active account");
  const args=["app-server","--listen","stdio://","-c",'model_provider="openai_chatgpt_plan"',"-c",'model_providers.openai_chatgpt_plan.name="ChatGPT plan"',"-c",'model_providers.openai_chatgpt_plan.base_url="https://api.openai.com/v1"',"-c",'model_providers.openai_chatgpt_plan.env_key="ACCESS_TOKEN"',"-c",'model_providers.openai_chatgpt_plan.wire_api="responses"',"-c",'model_providers.openai_chatgpt_plan.requires_openai_auth=false',"-c",'model_providers.openai_chatgpt_plan.supports_websockets=false'];
  console.error(`Starting Codex app-server for account: ${account.label}`);
  const child=spawn("codex",args,{stdio:"inherit",env:{...process.env,ACCESS_TOKEN:secret.access_token}});
  child.on("exit",code=>process.exitCode=code??1);
}

async function logout(accountId=activeId()) {
  if(!accountId) throw new Error("No active account");
  const a=accountById(accountId); let confirmed=false;
  if(fs.existsSync(secretPath(accountId))){
    const s=await readSecret(accountId);
    if(s.refresh_token){
      try{
        const d=await fetch(OIDC); if(!d.ok) throw new Error(`OIDC HTTP ${d.status}`);
        const discovery=await d.json(); const rev=discovery.revocation_endpoint;
        if(!rev) throw new Error("No revocation endpoint");
        const rr=await fetch(rev,{method:"POST",headers:{"content-type":"application/x-www-form-urlencoded"},body:new URLSearchParams({token:s.refresh_token,token_type_hint:"refresh_token",client_id:a.client_id})});
        confirmed=rr.ok;
      }catch{confirmed=false;}
    }
  }
  deleteSecret(accountId);
  if(activeId()===accountId) try{fs.rmSync(activeFile(),{force:true});}catch{}
  console.log(JSON.stringify({signed_out:true,account_id:accountId,remote_revocation_confirmed:confirmed,registration_retained:true},null,2));
}

async function main() {
  const [cmd,...rest]=process.argv.slice(2); const f=parseFlags(rest);
  if(cmd==="signin") return signIn({accountId:f.account===true?undefined:f.account,label:f.label===true?undefined:f.label});
  if(cmd==="list") return listAccounts();
  if(cmd==="status") return status(f.account===true?undefined:f.account||activeId());
  if(cmd==="use") { const id=f._[0]; if(!id) throw new Error("account id required"); return useAccount(id); }
  if(cmd==="logout") return logout(f.account===true?undefined:f.account||activeId());
  if(cmd==="models") return models();
  if(cmd==="ask") { const model=f.model===true?null:f.model; const prompt=f._.join(" ").trim(); if(!model)throw new Error("--model required");if(!prompt)throw new Error("prompt required");return ask(model,prompt); }
  if(cmd==="codex-server") return codexServer();
  console.log("Usage:\n  node client.mjs signin [--label NAME] [--account ID]\n  node client.mjs list\n  node client.mjs use <ID>\n  node client.mjs status [--account ID]\n  node client.mjs logout [--account ID]\n  node client.mjs models\n  node client.mjs ask --model <slug> <prompt>\n  node client.mjs codex-server");
}
if(import.meta.url===`file://${process.argv[1]}`) main().catch(e=>{console.error(e.message);process.exitCode=1});
