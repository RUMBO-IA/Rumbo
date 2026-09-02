from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "rumbo-coding-agent-reliability"
MANIFEST = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
MARKETPLACE = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))

assert MANIFEST["name"] == "rumbo-coding-agent-reliability"
assert MANIFEST["version"] == "0.1.5"
assert MANIFEST["skills"] == "./skills/"
assert len(MANIFEST["interface"]["defaultPrompt"]) == 3
assert not MANIFEST.get("apps")
assert not MANIFEST.get("mcpServers")

skill_names = [p.name for p in (PLUGIN / "skills").iterdir() if p.is_dir()]
expected = {
    "canonical-state-recovery",
    "deep-research-reconcile",
    "goal-loop-controller",
    "execute-verify-close",
    "audit-final-state",
}
assert set(skill_names) == expected
for name in expected:
    text = (PLUGIN / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\nname:")

assert (PLUGIN / "privacy.html").exists()
assert (PLUGIN / "terms.html").exists()

entry = MARKETPLACE["plugins"][0]
assert entry["name"] == "rumbo-coding-agent-reliability"
assert entry["source"]["path"] == "./plugins/rumbo-coding-agent-reliability"
assert entry["policy"]["installation"] == "AVAILABLE"
assert entry["policy"]["authentication"] == "ON_INSTALL"

print("RUMBO_PLUGIN_MANIFEST_PASS")
print("RUMBO_SKILLS_5_PASS")
print("RUMBO_LEGAL_FILES_PASS")
print("RUMBO_MARKETPLACE_PASS")
