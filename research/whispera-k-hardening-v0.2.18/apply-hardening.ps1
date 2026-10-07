param(
  [Parameter(Mandatory=$true)][string]$Root
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path $Root).Path
$nl = [Environment]::NewLine

function FilePath([string]$rel) { Join-Path $Root $rel }
function Read-Text([string]$rel) { Get-Content -LiteralPath (FilePath $rel) -Raw }
function Write-Text([string]$rel,[string]$text) {
  Set-Content -LiteralPath (FilePath $rel) -Value $text -Encoding utf8NoBOM -NoNewline
}
function Replace-Exact([string]$rel,[string]$old,[string]$new) {
  $text = Read-Text $rel
  if (-not $text.Contains($old)) { throw "Expected source fragment not found in $rel" }
  Write-Text $rel ($text.Replace($old,$new))
}
function Replace-Regex([string]$rel,[string]$pattern,[string]$replacement) {
  $text = Read-Text $rel
  $rx = [regex]::new($pattern,[Text.RegularExpressions.RegexOptions]::Singleline)
  $matches = $rx.Matches($text)
  if ($matches.Count -ne 1) { throw "Expected exactly one regex match in $rel, got $($matches.Count): $pattern" }
  Write-Text $rel ($rx.Replace($text,$replacement,1))
}

# Tauri versions and updater policy.
$pkgPath = 'apps/desktop/package.json'
$pkg = (Read-Text $pkgPath) | ConvertFrom-Json
$pkg.dependencies.'@tauri-apps/api' = '2.12.0'
$pkg.devDependencies.'@tauri-apps/cli' = '2.12.0'
$pkg.dependencies.PSObject.Properties.Remove('ffmpeg-static')
if (-not $pkg.PSObject.Properties['overrides']) { $pkg | Add-Member -NotePropertyName overrides -NotePropertyValue ([pscustomobject]@{}) }
$pkg.overrides | Add-Member -NotePropertyName 'source-map-js' -NotePropertyValue '1.2.2' -Force
Write-Text $pkgPath (($pkg | ConvertTo-Json -Depth 100) + $nl)

$cargoPath = 'apps/desktop/src-tauri/Cargo.toml'
Replace-Exact $cargoPath 'tauri = { version = "2", features = ["tray-icon", "image-png", "protocol-asset"] }' 'tauri = { version = ">=2.11.6, <3", features = ["tray-icon", "image-png", "protocol-asset"] }'
Replace-Exact $cargoPath 'tauri-plugin-updater = "2"' 'tauri-plugin-updater = "=2.12.0"'
Replace-Exact $cargoPath 'tauri = { version = "2", features = ["test"] }' 'tauri = { version = ">=2.11.6, <3", features = ["test"] }'
Replace-Exact $cargoPath '"Win32_System_Com", "Win32_System_LibraryLoader"' '"Win32_System_Com", "Win32_System_Com_StructuredStorage", "Win32_System_Variant", "Win32_System_LibraryLoader"'

$configPath = 'apps/desktop/src-tauri/tauri.conf.json'
$config = (Read-Text $configPath) | ConvertFrom-Json
$config.plugins.updater | Add-Member -NotePropertyName requireSignedVersion -NotePropertyValue $true -Force
$config.plugins.updater | Add-Member -NotePropertyName allowDowngrades -NotePropertyValue $false -Force
$config.bundle.windows | Add-Member -NotePropertyName allowDowngrades -NotePropertyValue $false -Force
$config.bundle.resources.PSObject.Properties.Remove('../node_modules/ffmpeg-static/ffmpeg.exe')
$config.bundle.resources.PSObject.Properties.Remove('../node_modules/ffmpeg-static/ffmpeg.exe.LICENSE')
$config.bundle.resources.PSObject.Properties.Remove('../node_modules/ffmpeg-static/ffmpeg.exe.README')
$config.bundle.resources | Add-Member -NotePropertyName '../vendor/ffmpeg/ffmpeg.exe' -NotePropertyValue 'bin/ffmpeg.exe' -Force
$config.bundle.resources | Add-Member -NotePropertyName '../vendor/ffmpeg/ffmpeg.LICENSE' -NotePropertyValue 'bin/ffmpeg.LICENSE' -Force
$config.bundle.resources | Add-Member -NotePropertyName '../vendor/ffmpeg/ffmpeg.README' -NotePropertyValue 'bin/ffmpeg.README' -Force
Write-Text $configPath (($config | ConvertTo-Json -Depth 100) + $nl)

# Privacy defaults: explicit capture only, no background video STT by default.
Replace-Exact 'apps/desktop/src/LibrarySettings.tsx' 'const defaults:Preferences = {captureGlobal:true,incognito:false,historyLimit:250,autoDeleteHours:48,clearUnpinnedOnRestart:false,transcribeVideo:true,videoTranscriptAttachment:true};' 'const defaults:Preferences = {captureGlobal:false,incognito:false,historyLimit:250,autoDeleteHours:48,clearUnpinnedOnRestart:false,transcribeVideo:false,videoTranscriptAttachment:false};'
Replace-Exact 'apps/desktop/vendor/edge-drop/browser-preview/native.ts' "stickPosition:'left',captureGlobal:true,hoverActivation:false" "stickPosition:'left',captureGlobal:false,hoverActivation:false"
Replace-Exact 'apps/desktop/src-tauri/src/library.rs' 'json!({"captureGlobal":true,"autoDeleteHours":48,"historyLimit":250,"incognito":false,"toggleHotkey":"Alt+C"})' 'json!({"captureGlobal":false,"autoDeleteHours":48,"historyLimit":250,"incognito":false,"clearUnpinnedOnRestart":false,"transcribeVideo":false,"videoTranscriptAttachment":false,"toggleHotkey":"Alt+C"})'
Replace-Exact 'apps/desktop/src-tauri/src/video_transcript.rs' '.unwrap_or(true)' '.unwrap_or(false)'
Replace-Exact 'apps/desktop/src-tauri/src/storage.rs' 'incremental_transcription: true,' 'incremental_transcription: false,'
Replace-Exact 'apps/desktop/src-tauri/src/storage.rs' '#[derive(Clone, Serialize, Deserialize)]' '#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]'

# Restore upstream dictionary compare-and-swap + previous revision.
$replaceRules = @'
impl Store {
    pub fn replace_rules(&self, rules: &[Rule], expected: &[Rule]) -> Result<(), String> {
        let mut conn = self.0.lock().map_err(|_| "Base de datos ocupada")?;
        let tx = conn.transaction().map_err(|e| e.to_string())?;
        let old: Option<String> = match tx.query_row("SELECT value FROM kv WHERE key='rules'", [], |r| r.get(0)) {
            Ok(value) => Some(value),
            Err(rusqlite::Error::QueryReturnedNoRows) => None,
            Err(error) => return Err(error.to_string()),
        };
        let current: Vec<Rule> = match old.as_deref() {
            Some(value) => serde_json::from_str(value).map_err(|e| e.to_string())?,
            None => Vec::new(),
        };
        if current != expected {
            return Err("El diccionario cambio desde que abriste esta pantalla. Se actualizaron las reglas; revisa y volve a guardar.".into());
        }
        if let Some(old) = old {
            tx.execute("INSERT INTO kv VALUES('rules_previous',?1) ON CONFLICT(key) DO UPDATE SET value=excluded.value", [old]).map_err(|e| e.to_string())?;
        }
        let json = serde_json::to_string(rules).map_err(|e| e.to_string())?;
        tx.execute("INSERT INTO kv VALUES('rules',?1) ON CONFLICT(key) DO UPDATE SET value=excluded.value", [json]).map_err(|e| e.to_string())?;
        tx.commit().map_err(|e| e.to_string())
    }

    pub fn update_transcript
'@
Replace-Regex 'apps/desktop/src-tauri/src/storage.rs' 'impl Store \{\r?\n    pub fn update_transcript' $replaceRules

$dictTest = @'
    #[test]
    fn stale_dictionary_cannot_replace_newer_rules_and_previous_revision_is_retained() {
        let store = Store::open(Path::new(":memory:")).unwrap();
        let old = vec![Rule { id: "existing".into(), source: "wispara".into(), target: "Whispera".into(), enabled: true }];
        store.put("rules", &old).unwrap();
        let new = vec![Rule { id: "new".into(), source: "groc".into(), target: "Groq".into(), enabled: true }];
        assert!(store.replace_rules(&new, &[]).is_err());
        assert_eq!(store.get::<Vec<Rule>>("rules").unwrap(), old);
        let mut merged = old.clone();
        merged.extend(new);
        store.replace_rules(&merged, &old).unwrap();
        assert_eq!(store.get::<Vec<Rule>>("rules_previous").unwrap(), old);
        assert_eq!(store.get::<Vec<Rule>>("rules").unwrap(), merged);
    }

    #[test]
    fn settings_roundtrip
'@
Replace-Regex 'apps/desktop/src-tauri/src/storage.rs' '    #\[test\]\r?\n    fn settings_roundtrip' $dictTest

$oldSaveRules = @'
#[tauri::command]
fn save_rules(rules: Vec<Rule>, store: State<Store>) -> Result<(), String> {
    groq::validate_rules(&rules)?;
    store.put("rules", &rules)
}
'@
$newSaveRules = @'
#[tauri::command]
fn read_rules(store: State<Store>) -> Result<Vec<Rule>, String> {
    store.get("rules")
}
#[tauri::command]
fn save_rules(rules: Vec<Rule>, expected_rules: Vec<Rule>, store: State<Store>) -> Result<(), String> {
    groq::validate_rules(&rules)?;
    store.replace_rules(&rules, &expected_rules)
}
'@
Replace-Exact 'apps/desktop/src-tauri/src/main.rs' $oldSaveRules $newSaveRules
Replace-Exact 'apps/desktop/src-tauri/src/main.rs' '            save_rules,' ('            read_rules,' + $nl + '            save_rules,')

$oldClient = @'
export async function saveRules(rules: Rule[]) {
  const seen = new Set<string>();
  for(const r of rules){const key=r.source.trim().toLowerCase(); if(!key||!r.target.trim())throw Error('Completá ambos campos.'); if(key===r.target.trim().toLowerCase())throw Error('La corrección debe cambiar la palabra.'); if(seen.has(key))throw Error('Ya existe una regla para esa palabra.'); seen.add(key);}
  if (native) await invoke("save_rules", { rules }); else { preview.rules = rules; persist(); }
}
'@
$newClient = @'
export async function readRules(): Promise<Rule[]> { return native ? invoke('read_rules') : structuredClone(preview.rules); }
export async function saveRules(rules: Rule[], expectedRules: Rule[]) {
  const seen = new Set<string>();
  for(const r of rules){const key=r.source.trim().toLowerCase(); if(!key||!r.target.trim())throw Error('Completá ambos campos.'); if(key===r.target.trim().toLowerCase())throw Error('La corrección debe cambiar la palabra.'); if(seen.has(key))throw Error('Ya existe una regla para esa palabra.'); seen.add(key);}
  if (native) await invoke("save_rules", { rules, expectedRules }); else { preview.rules = rules; persist(); }
}
'@
Replace-Exact 'apps/desktop/src/client.ts' $oldClient $newClient

$dictionaryEffect = @'
  useEffect(() => { refresh().catch(e => setMessage(String(e))); }, []);
  useEffect(() => {
    if (route !== 'dictionary') return;
    let alive = true;
    const reload = () => void api.readRules().then(rules => {
      if (alive) setData(data => data ? { ...data, rules } : data);
    }).catch(error => { if (alive) setMessage(String(error)); });
    reload();
    window.addEventListener('focus', reload);
    return () => { alive = false; window.removeEventListener('focus', reload); };
  }, [route]);
'@
Replace-Exact 'apps/desktop/src/main.tsx' '  useEffect(() => { refresh().catch(e => setMessage(String(e))); }, []);' $dictionaryEffect.TrimEnd()

$oldRun = '  const run = async (work: () => Promise<unknown>, success: string) => { setBusy(true); try { await work(); await refresh(); setMessage(success); return true; } catch (error) { setMessage(String(error)); return false; } finally { setBusy(false); } };'
$newRun = @'
  const run = async (work: () => Promise<unknown>, success: string) => {
    setBusy(true);
    try { await work(); await refresh(); setMessage(success); return true; }
    catch (error) {
      if (route === 'dictionary') {
        try { const rules = await api.readRules(); setData(data => data ? { ...data, rules } : data); }
        catch { /* Keep last loaded rules if refresh also fails. */ }
      }
      setMessage(String(error)); return false;
    } finally { setBusy(false); }
  };
'@
Replace-Exact 'apps/desktop/src/main.tsx' $oldRun $newRun.TrimEnd()
Replace-Exact 'apps/desktop/src/main.tsx' 'await api.saveRules(editingRule?data.rules.map(r=>r.id===editingRule?updated:r):[...data.rules,updated]);' 'await api.saveRules(editingRule?data.rules.map(r=>r.id===editingRule?updated:r):[...data.rules,updated], data.rules);'
Replace-Exact 'apps/desktop/src/main.tsx' 'api.saveRules(data.rules.map(r => r.id === rule.id ? { ...r, enabled: e.target.checked } : r)), "Regla actualizada"' 'api.saveRules(data.rules.map(r => r.id === rule.id ? { ...r, enabled: e.target.checked } : r), data.rules), "Regla actualizada"'
Replace-Exact 'apps/desktop/src/main.tsx' 'api.saveRules(data.rules.filter(r => r.id !== rule.id)), "Regla eliminada"' 'api.saveRules(data.rules.filter(r => r.id !== rule.id), data.rules), "Regla eliminada"'

# Reduce renderer authority for arbitrary file transcription.
$oldTranscribeSig = @'
async fn transcribe_file(
    path: String,
    app: tauri::AppHandle,
'@
$newTranscribeSig = @'
async fn transcribe_file(
    path: String,
    window: tauri::WebviewWindow,
    app: tauri::AppHandle,
'@
Replace-Exact 'apps/desktop/src-tauri/src/main.rs' $oldTranscribeSig $newTranscribeSig
$oldTranscribeStart = @'
) -> Result<String, String> {
    let _updating = updates::work(&app)?;
'@
$newTranscribeStart = @'
) -> Result<String, String> {
    if window.label() != "import" {
        return Err("La transcripcion de archivos solo esta autorizada desde la ventana de importacion".into());
    }
    let _updating = updates::work(&app)?;
'@
Replace-Exact 'apps/desktop/src-tauri/src/main.rs' $oldTranscribeStart $newTranscribeStart

# Updater: manual-only checks + bounded DB backups.
Replace-Exact 'apps/desktop/src-tauri/src/updates.rs' 'use std::time::{Duration,Instant};' ('use std::time::{Duration,Instant};' + $nl + 'use std::path::Path;')

$prune = @'
fn prune_backups(dir:&Path)->Result<(),String>{
    if !dir.is_dir(){return Ok(());}
    let mut files:Vec<_>=std::fs::read_dir(dir).map_err(|e|e.to_string())?
        .filter_map(Result::ok)
        .map(|e|e.path())
        .filter(|p|p.extension().is_some_and(|e|e.eq_ignore_ascii_case("sqlite")))
        .collect();
    files.sort_by_key(|p|std::fs::metadata(p).and_then(|m|m.modified()).ok());
    while files.len()>=3 {
        let old=files.remove(0);
        std::fs::remove_file(old).map_err(|e|e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub fn updater_status
'@
Replace-Regex 'apps/desktop/src-tauri/src/updates.rs' '#\[tauri::command\]\r?\npub fn updater_status' $prune
Replace-Exact 'apps/desktop/src-tauri/src/updates.rs' '            std::fs::create_dir_all(&backup_dir).map_err(|e|e.to_string())?;' ('            std::fs::create_dir_all(&backup_dir).map_err(|e|e.to_string())?;' + $nl + '            prune_backups(&backup_dir)?;')

$manualStart = @'
pub fn start(_app:&tauri::AppHandle) {
    // Hardened RUMBO profile: update checks are explicit user actions.
    // This avoids periodic network traffic and surprise UI while work is active.
}
#[cfg(test)]
'@
Replace-Regex 'apps/desktop/src-tauri/src/updates.rs' 'pub fn start\(app:&tauri::AppHandle\)\{.*?\r?\n\}\r?\n#\[cfg\(test\)\]' $manualStart

$marker = @"
# RUMBO hardening overlay

Base repository: https://github.com/kazu00001/Whispera-K
Base tag: v0.2.18
Base SHA: 3bbd712e0391287a01d264af6bcac43023965ac6

This source tree was generated by the RUMBO hardening workflow. It is not an upstream release.
"@
Write-Text 'RUMBO_HARDENING.md' $marker
Write-Host 'Hardening overlay applied.'
