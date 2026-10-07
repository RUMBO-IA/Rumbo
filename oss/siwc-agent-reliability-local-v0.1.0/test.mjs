import test from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { DYNAMIC, API, pkce, hostId, authUrl, verifyIdToken } from "./client.mjs";

test("PKCE and stable host ID", () => {
  const a=pkce(), b=pkce();
  assert.notEqual(a.verifier,b.verifier);
  assert.ok(a.verifier.length>=43);
  const d=fs.mkdtempSync(path.join(os.tmpdir(),"rumbo-siwc-"));
  assert.equal(hostId(d),hostId(d));
});

test("dynamic registration request shape", () => {
  const u=new URL(authUrl({
    redirectUri:"http://127.0.0.1:1455/auth/callback",
    state:"s",nonce:"n",challenge:"c",
    extAgentHostId:"urn:uuid:00000000-0000-4000-8000-000000000001"
  }));
  assert.equal(u.searchParams.get("client_id"),DYNAMIC);
  assert.equal(u.searchParams.get("resource"),API);
  assert.equal(u.searchParams.get("redirect_uri"),"http://127.0.0.1:1455/auth/callback");
  assert.equal(u.searchParams.get("code_challenge_method"),"S256");
  assert.ok(u.searchParams.get("scope").includes("chatgpt.tokens.use.direct"));
  assert.equal(u.searchParams.has("client_secret"),false);
});

test("RS256 ID token verification", () => {
  const {publicKey,privateKey}=crypto.generateKeyPairSync("rsa",{modulusLength:2048});
  const jwk=publicKey.export({format:"jwk"}); Object.assign(jwk,{kid:"k1",kty:"RSA",alg:"RS256"});
  const h=Buffer.from(JSON.stringify({alg:"RS256",kid:"k1"})).toString("base64url");
  const p=Buffer.from(JSON.stringify({
    iss:"https://auth.openai.com",aud:"oaiapp_test",sub:"s",nonce:"n",
    exp:Math.floor(Date.now()/1000)+3600
  })).toString("base64url");
  const s=crypto.sign("RSA-SHA256",Buffer.from(`${h}.${p}`),privateKey).toString("base64url");
  assert.equal(verifyIdToken(`${h}.${p}.${s}`,{keys:[jwk]},"oaiapp_test","n").sub,"s");
});
