import fs from 'node:fs';
import crypto from 'node:crypto';
const support = fs.readFileSync('openai-support.html', 'utf8');
const home = fs.readFileSync('index.html', 'utf8');
const required = [
  'RUMBO OpenAI Support',
  'sebastian@rumbo.verso.fans',
  'Do not send passwords',
  'openai-privacy',
  'openai-terms',
  'support'
];
const forbidden = [
  'Turn customer conversations into',
  'available for direct conversations about controlled pilots'
];
const missing = required.filter((token) => !support.includes(token));
const leakedHome = forbidden.filter((token) => support.includes(token));
const sha = (text) => crypto.createHash('sha256').update(text).digest('hex');
if (missing.length) throw new Error(`SUPPORT_REQUIRED_MARKERS_MISSING:${missing.join(',')}`);
if (leakedHome.length) throw new Error(`SUPPORT_HOMEPAGE_CONTENT_PRESENT:${leakedHome.join(',')}`);
if (sha(support) === sha(home)) throw new Error('SUPPORT_EQUALS_HOMEPAGE');
console.log(JSON.stringify({supportSemantic:'PASS', supportSha256:sha(support), homeSha256:sha(home)}));
