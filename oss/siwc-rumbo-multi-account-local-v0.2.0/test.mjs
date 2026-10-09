import test from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { DYNAMIC, API, SCOPES, AGENT_NAME, pkce, hostId, authUrl, verifyIdToken, home } from "./client.mjs";

test("PKCE and stable host ID",()=>{
  const a=pkce(),b=pkce();assert.notEqual(a.verifier,b.verifier);assert.ok(a.verifier.length>=43);
  const d=fs.mkdtempSync(path.join(os.tmpdir(),"rumbo-siwc-"));assert.equal(hostId(d),hostId(d));assert.match(hostId(d),/^urn:uuid:/);
});

test("dynamic registration request has exact plan scopes and loopback",()=>{
  const u=new URL(authUrl({redirectUri:"http://127.0.0.1:1455/auth/callback",state:"s",nonce:"n",challenge:"c",extAgentHostId:"urn:uuid:00000000-0000-4000-8000-000000000001"}));
  assert.equal(u.searchParams.get("client_id"),DYNAMIC);assert.equal(u.searchParams.get("agent_name_hint"),AGENT_NAME);assert.equal(u.searchParams.get("resource"),API);assert.equal(u.searchParams.get("redirect_uri"),"http://127.0.0.1:1455/auth/callback");assert.equal(u.searchParams.get("code_challenge_method"),"S256");
  for(const scope of ["openid","profile","email","offline_access","resource.invoke","chatgpt.tokens.use.direct"]) assert.ok(u.searchParams.get("scope").split(" ").includes(scope));
  assert.equal(u.searchParams.has("client_secret"),false);assert.equal(SCOPES.includes("chatgpt.tokens.use.direct"),true);
});

test("returning registration omits agent_name_hint and keeps client",()=>{
  const u=new URL(authUrl({redirectUri:"http://127.0.0.1:54321/auth/callback",state:"s",nonce:"n",challenge:"c",extAgentHostId:"urn:uuid:00000000-0000-4000-8000-000000000001",clientId:"oaiapp_saved",loginHint:"user@example.com",idTokenHint:"jwt"}));
  assert.equal(u.searchParams.get("client_id"),"oaiapp_saved");assert.equal(u.searchParams.has("agent_name_hint"),false);assert.equal(u.searchParams.get("login_hint"),"user@example.com");assert.equal(u.searchParams.get("id_token_hint"),"jwt");
});

test("RS256 ID token verification",()=>{
  const {publicKey,privateKey}=crypto.generateKeyPairSync("rsa",{modulusLength:2048});
  const jwk=publicKey.export({format:"jwk"});Object.assign(jwk,{kid:"k1",kty:"RSA",alg:"RS256"});
  const h=Buffer.from(JSON.stringify({alg:"RS256",kid:"k1"})).toString("base64url");
  const p=Buffer.from(JSON.stringify({iss:"https://auth.openai.com",aud:"oaiapp_test",sub:"s",nonce:"n",exp:Math.floor(Date.now()/1000)+3600})).toString("base64url");
  const s=crypto.sign("RSA-SHA256",Buffer.from(`${h}.${p}`),privateKey).toString("base64url");
  assert.equal(verifyIdToken(`${h}.${p}.${s}`,{keys:[jwk]},"oaiapp_test","n").sub,"s");
  assert.throws(()=>verifyIdToken(`${h}.${p}.${s}`,{keys:[jwk]},"other","n"),/Audience/);
});

test("default home is RUMBO scoped and contains no account identifier",()=>{
  const h=home();assert.match(h,/RUMBO/);assert.match(h,/SIWC/);assert.doesNotMatch(h,/@/);
});

test("refresh path honors earliest_refresh_at and serialized rotation",()=>{
  const source=fs.readFileSync(new URL("./client.mjs",import.meta.url),"utf8");
  assert.ok(source.includes("earliest_refresh_at"));
  assert.ok(source.includes("refreshAllowed"));
  assert.ok(source.includes("withRefreshLock"));
  assert.ok(source.includes("currentAllowed"));
});

test("source never embeds API keys, client secrets, or token literals",()=>{
  const source=fs.readFileSync(new URL("./client.mjs",import.meta.url),"utf8");
  assert.equal(/sk-[A-Za-z0-9_-]{16,}/.test(source),false);
  assert.equal(/client_secret\s*[:=]\s*["'][^"']+/i.test(source),false);
  assert.equal(/access_token\s*[:=]\s*["'][A-Za-z0-9._-]{20,}/i.test(source),false);
  assert.ok(source.includes("ProtectedData"));
  assert.ok(source.includes("dpapi-current-user-v1"));
});
