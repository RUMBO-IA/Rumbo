"""Offline, fail-closed structural gate for the v0.1.6 RUMBO Grok adapter.

Does not certify licensing, in-client execution, security, or marketplace acceptance.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

EXPECTED_SKILLS = frozenset({
    "audit-final-state", "canonical-state-recovery", "deep-research-reconcile",
    "execute-verify-close", "goal-loop-controller",
})
PLUGIN_REL = Path("openai-publication/agent-reliability/plugin")
FORBIDDEN_COMPONENTS = (".mcp.json", "mcp.json", ".lsp.json", "hooks/hooks.json")


def validate(root: Path) -> list[str]:
    plugin = root / PLUGIN_REL
    errors: list[str] = []
    manifests = {}
    for kind, filename in (("grok", ".grok-plugin/plugin.json"), ("codex", ".codex-plugin/plugin.json")):
        path = plugin / filename
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{kind}_manifest_unreadable:{type(exc).__name__}")
            continue
        if not isinstance(manifest, dict):
            errors.append(f"{kind}_manifest_not_object")
        else:
            manifests[kind] = manifest

    grok, codex = manifests.get("grok"), manifests.get("codex")
    if grok:
        if grok.get("name") != "rumbo-coding-agent-reliability":
            errors.append("unexpected_plugin_identity")
        if grok.get("version") != "0.1.6":
            errors.append("unexpected_release_version")
        if grok.get("skills") != "./skills":
            errors.append("unexpected_skills_path")
        author = grok.get("author")
        if not isinstance(author, dict) or author.get("name") != "RUMBO IA":
            errors.append("unrecognized_author")
        keywords = grok.get("keywords")
        if not isinstance(keywords, list) or not keywords or any(
            not isinstance(k, str) or "rumbo" not in k.lower() for k in keywords
        ):
            errors.append("keywords_not_brand_scoped")
        if any(key in grok for key in ("mcpServers", "hooks", "commands", "agents", "postinstall")):
            errors.append("unexpected_executable_or_network_component")
    if grok and codex:
        if (grok.get("name"), grok.get("version")) != (codex.get("name"), codex.get("version")):
            errors.append("grok_codex_identity_mismatch")
    actual = {p.parent.name for p in (plugin / "skills").glob("*/SKILL.md")}
    if actual != EXPECTED_SKILLS:
        errors.append(f"unexpected_skill_inventory:{','.join(sorted(actual))}")
    for skill in EXPECTED_SKILLS:
        p = plugin / "skills" / skill / "SKILL.md"
        if not p.is_file() or p.stat().st_size == 0:
            errors.append(f"missing_or_empty_skill:{skill}")
    for name in FORBIDDEN_COMPONENTS:
        if (plugin / name).exists():
            errors.append(f"forbidden_component:{name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    print(json.dumps({"structural_status": "PASS" if not errors else "FAIL",
                      "external_distribution": "NO_GO_UNTIL_LICENSE_AND_CLIENT_TEST",
                      "scope": "static five-skill adapter only", "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
