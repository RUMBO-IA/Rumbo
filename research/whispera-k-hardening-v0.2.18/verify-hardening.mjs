import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2] || '.');
const read = rel => fs.readFileSync(path.join(root, rel), 'utf8');
const checks = [];
const expect = (name, ok, detail='') => checks.push({name, ok:Boolean(ok), detail});

const pkg = JSON.parse(read('apps/desktop/package.json'));
const config = JSON.parse(read('apps/desktop/src-tauri/tauri.conf.json'));
const cargo = read('apps/desktop/src-tauri/Cargo.toml');
const storage = read('apps/desktop/src-tauri/src/storage.rs');
const main = read('apps/desktop/src-tauri/src/main.rs');
const client = read('apps/desktop/src/client.ts');
const mainTsx = read('apps/desktop/src/main.tsx');
const library = read('apps/desktop/src-tauri/src/library.rs');
const librarySettings = read('apps/desktop/src/LibrarySettings.tsx');
const native = read('apps/desktop/vendor/edge-drop/browser-preview/native.ts');
const video = read('apps/desktop/src-tauri/src/video_transcript.rs');
const updates = read('apps/desktop/src-tauri/src/updates.rs');

expect('Tauri CLI >= 2.12.0', pkg.devDependencies?.['@tauri-apps/cli'] === '2.12.0', pkg.devDependencies?.['@tauri-apps/cli']);
expect('Tauri API aligned', pkg.dependencies?.['@tauri-apps/api'] === '2.12.0', pkg.dependencies?.['@tauri-apps/api']);
expect('ffmpeg-static npm dependency removed', !pkg.dependencies?.['ffmpeg-static']);
expect('Pinned FFmpeg resource uses RUMBO vendor path', config.bundle?.resources?.['../vendor/ffmpeg/ffmpeg.exe'] === 'bin/ffmpeg.exe');
expect('source-map-js patched to 1.2.2', pkg.overrides?.['source-map-js'] === '1.2.2', pkg.overrides?.['source-map-js']);
expect('Rust Tauri excludes <=2.11.5', cargo.includes('version = ">=2.11.6, <3"'));
expect('Windows COM audio features explicit', cargo.includes('Win32_System_Com_StructuredStorage') && cargo.includes('Win32_System_Variant'));
expect('Updater crate pinned 2.12.0', cargo.includes('tauri-plugin-updater = "=2.12.0"'));
expect('Updater binds signed version', config.plugins?.updater?.requireSignedVersion === true);
expect('Updater rejects downgrade manifests', config.plugins?.updater?.allowDowngrades === false);
expect('Windows installer rejects downgrade installs', config.bundle?.windows?.allowDowngrades === false);
expect('Global clipboard capture defaults OFF', library.includes('"captureGlobal":false'));
expect('Library UI clipboard default OFF', librarySettings.includes('captureGlobal:false'));
expect('Vendor library clipboard default OFF', native.includes('captureGlobal:false'));
expect('Video transcription defaults OFF', library.includes('"transcribeVideo":false') && librarySettings.includes('transcribeVideo:false'));
expect('Video transcript attachment defaults OFF', library.includes('"videoTranscriptAttachment":false') && librarySettings.includes('videoTranscriptAttachment:false'));
expect('Missing video settings fail closed', video.includes('.unwrap_or(false)'));
expect('Incremental transcription defaults OFF', storage.includes('incremental_transcription: false'));
expect('Dictionary compare-and-swap restored', storage.includes('pub fn replace_rules') && storage.includes('current != expected'));
expect('Dictionary Rule supports CAS equality tests', storage.includes('#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]'));
expect('Dictionary previous revision retained', storage.includes("rules_previous"));
expect('Dictionary native command receives expected rules', main.includes('expected_rules: Vec<Rule>') && main.includes('store.replace_rules(&rules, &expected_rules)'));
expect('Dictionary read command restored', main.includes('fn read_rules') && main.includes('read_rules,'));
expect('Frontend sends expected rules', client.includes('saveRules(rules: Rule[], expectedRules: Rule[])') && client.includes('{ rules, expectedRules }'));
expect('Dictionary refreshes on focus', mainTsx.includes("if (route !== 'dictionary') return") && mainTsx.includes("window.addEventListener('focus', reload)"));
expect('Transcribe-file restricted to import window', main.includes('window.label() != "import"'));
expect('Automatic updater polling disabled', updates.includes('pub fn start(_app:&tauri::AppHandle)') && !updates.includes('Duration::from_secs(5*60)'));
expect('Updater backups bounded', updates.includes('fn prune_backups') && updates.includes('prune_backups(&backup_dir)?'));

let failed = 0;
for (const c of checks) {
  const mark = c.ok ? 'PASS' : 'FAIL';
  console.log(`${mark}: ${c.name}${c.detail ? ` (${c.detail})` : ''}`);
  if (!c.ok) failed++;
}
console.log(`HARDENING_CHECKS=${checks.length} FAILED=${failed}`);
process.exit(failed ? 1 : 0);
