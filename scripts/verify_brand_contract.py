from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = pathlib.Path("docs/brand/identity_registry_v1.json")
PRODUCTION_LOCK_PATH = pathlib.Path("docs/brand/production_lock_v1.json")
DISTRIBUTION_LOCK_PATH = pathlib.Path("docs/brand/distribution_lock_v1.json")
PRIMARY = pathlib.Path("index.html")
README = pathlib.Path("README.md")
SECONDARY_REQUIRED = (
    pathlib.Path("apps/landing-publica/index.html"),
    pathlib.Path("apps/landing-publica/index-es.html"),
    pathlib.Path("apps/landing-publica/index-en-openai.html"),
)
SECONDARY_README = pathlib.Path("apps/landing-publica/README.md")
PUBLIC_GLOBS = ("apps/landing-publica/*.html",)
LEGAL_EXEMPT_NAMES = {"privacy.html", "terms.html"}

REQUIRED_PRIMARY_COLORS = {
    "#080c12", "#101722", "#141e2c", "#263246", "#f7f9fc",
    "#9aa8ba", "#ff7a45", "#63ddb0", "#7aa7ff", "#ff7b88",
}
FORBIDDEN_PUBLIC_CLAIMS = (
    "100% secure", "guaranteed roi", "roi guaranteed",
    "guaranteed revenue", "fully autonomous",
)
FORBIDDEN_ALIASES = ("Rumbo AI", "RUMBO.AI", "RumboIA")
HUMAN_CONTROL = re.compile(
    r"human[- ]controlled|human control|control humano|persona aprobando|una persona aprueba",
    re.I,
)


def _normalize(text: str) -> str:
    text = text.casefold().replace("%", " percent ")
    return re.sub(r"[^a-z0-9áéíóúüñ]+", " ", text).strip()


def load_registry(root: pathlib.Path = ROOT) -> dict:
    path = root / REGISTRY_PATH
    if not path.is_file():
        raise ValueError(f"missing brand identity registry: {REGISTRY_PATH}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported brand identity registry schema_version")
    roles = data.get("roles")
    identities = data.get("identities")
    non_canonical = data.get("non_canonical")
    if not isinstance(roles, list) or not roles or len(set(roles)) != len(roles):
        raise ValueError("registry roles must be a non-empty unique list")
    if not all(isinstance(role, str) and role.strip() for role in roles):
        raise ValueError("registry roles must be non-empty strings")
    if not isinstance(identities, dict) or not identities:
        raise ValueError("registry identities must be a non-empty object")
    if not isinstance(non_canonical, list) or not all(isinstance(v, str) and v.strip() for v in non_canonical):
        raise ValueError("registry non_canonical must be a list of non-empty strings")
    role_set = set(roles)
    for name, allowed in identities.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("registry identity names must be non-empty strings")
        if not isinstance(allowed, list) or not allowed or len(set(allowed)) != len(allowed):
            raise ValueError(f"invalid roles for identity: {name}")
        if not set(allowed) <= role_set:
            raise ValueError(f"unknown role binding for identity: {name}")
    overlap = {name.casefold() for name in identities} & {name.casefold() for name in non_canonical}
    if overlap:
        raise ValueError(f"canonical/non-canonical overlap: {sorted(overlap)}")
    return data


def load_production_lock(root: pathlib.Path = ROOT) -> dict:
    path = root / PRODUCTION_LOCK_PATH
    if not path.is_file():
        raise ValueError(f"missing production authority lock: {PRODUCTION_LOCK_PATH}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported production lock schema_version")
    if data.get("registry_issue") != "RUMBO-IA/Rumbo#72":
        raise ValueError("production lock must bind canonical registry RUMBO-IA/Rumbo#72")
    comment_id = data.get("owner_authorization_comment_id")
    if not isinstance(comment_id, int) or comment_id <= 0:
        raise ValueError("production lock owner authorization comment id invalid")
    app_sha = data.get("application_sha")
    if not isinstance(app_sha, str) or re.fullmatch(r"[0-9a-f]{40}", app_sha) is None:
        raise ValueError("production lock application_sha must be lowercase 40-hex")
    deployment_id = data.get("deployment_id")
    if not isinstance(deployment_id, str) or re.fullmatch(r"dpl_[A-Za-z0-9]+", deployment_id) is None:
        raise ValueError("production lock deployment_id invalid")
    domain = data.get("domain")
    if not isinstance(domain, str) or re.fullmatch(r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}", domain) is None:
        raise ValueError("production lock domain invalid")
    if data.get("status") != "AUTHORIZED":
        raise ValueError("production lock status must be AUTHORIZED")
    if data.get("invariant") != "MAIN_ADVANCE != PRODUCTION_AUTHORITY":
        raise ValueError("production lock invariant invalid")
    return data


def load_distribution_lock(root: pathlib.Path = ROOT) -> dict:
    path = root / DISTRIBUTION_LOCK_PATH
    if not path.is_file():
        raise ValueError(f"missing distribution lock: {DISTRIBUTION_LOCK_PATH}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1 or data.get("registry_issue") != "RUMBO-IA/Rumbo#72":
        raise ValueError("distribution lock must bind schema v1 and canonical registry")
    required = data.get("required_channels")
    channels = data.get("channels")
    if not isinstance(required, list) or not required or not isinstance(channels, dict):
        raise ValueError("distribution lock required_channels/channels invalid")
    if any(name not in channels for name in required):
        raise ValueError("distribution lock missing required channel")
    status = data.get("overall_status")
    if status not in {"PARTIAL_PASS", "PASS"}:
        raise ValueError("distribution lock overall_status invalid")
    if status == "PASS":
        for name in required:
            state = channels[name]
            if any(state.get(field) != "PASS" for field in ("binding", "profile_alignment", "readback")):
                raise ValueError(f"distribution PASS forbidden while required channel incomplete: {name}")
    if data.get("invariant") != "DISTRIBUTION_PASS_REQUIRES_ALL_REQUIRED_CHANNELS_PASS":
        raise ValueError("distribution lock invariant invalid")
    return data


def admit_identity(name: str, role: str, root: pathlib.Path = ROOT) -> tuple[str, str]:
    try:
        data = load_registry(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return "SAFE_STOP", f"registry_invalid:{exc}"
    if role not in data["roles"]:
        return "SAFE_STOP", "unknown_role"
    if name.casefold() in {value.casefold() for value in data["non_canonical"]}:
        return "SAFE_STOP", "non_canonical"
    canonical_name = next((key for key in data["identities"] if key.casefold() == name.casefold()), None)
    if canonical_name is None:
        return "SAFE_STOP", "unknown_identity"
    if role not in data["identities"][canonical_name]:
        return "SAFE_STOP", "role_not_allowed"
    return "PASS", "authorized_identity_role"


def _read_required(root: pathlib.Path, rel: pathlib.Path, errors: list[str]) -> str:
    path = root / rel
    if not path.is_file():
        errors.append(f"required public surface missing: {rel.as_posix()}")
        return ""
    return path.read_text(encoding="utf-8-sig")


def _public_surfaces(root: pathlib.Path) -> list[pathlib.Path]:
    rels = [PRIMARY, README, *SECONDARY_REQUIRED, SECONDARY_README]
    seen = set(rels)
    for pattern in PUBLIC_GLOBS:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root)
            if rel not in seen:
                rels.append(rel)
                seen.add(rel)
    return [root / rel for rel in rels if (root / rel).is_file()]


def _check_surface(
    root: pathlib.Path,
    path: pathlib.Path,
    text: str,
    registry: dict,
    errors: list[str],
    *,
    require_human_control: bool,
) -> None:
    rel = path.relative_to(root).as_posix()
    low = text.casefold()
    normalized = _normalize(text)
    if "rumbo ia" not in low:
        errors.append(f"canonical name RUMBO IA missing: {rel}")
    if require_human_control and not HUMAN_CONTROL.search(text):
        errors.append(f"human-control positioning missing: {rel}")
    for alias in FORBIDDEN_ALIASES:
        if alias.casefold() in low:
            errors.append(f"non-canonical public alias present in {rel}: {alias}")
    for denied in registry["non_canonical"]:
        if denied.casefold() in low:
            errors.append(f"non-canonical brand present in {rel}: {denied}")
    for claim in FORBIDDEN_PUBLIC_CLAIMS:
        if _normalize(claim) in normalized:
            errors.append(f"unsupported public claim present in {rel}: {claim}")


def verify(root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_registry(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"brand identity registry invalid: {exc}"]
    try:
        production_lock = load_production_lock(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"production authority lock invalid: {exc}"]
    try:
        load_distribution_lock(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"distribution lock invalid: {exc}"]

    required = [PRIMARY, README, *SECONDARY_REQUIRED, SECONDARY_README]
    texts = {rel: _read_required(root, rel, errors) for rel in required}
    if errors:
        return errors

    for path in _public_surfaces(root):
        require_human_control = path.name.casefold() not in LEGAL_EXEMPT_NAMES
        _check_surface(
            root,
            path,
            path.read_text(encoding="utf-8-sig"),
            registry,
            errors,
            require_human_control=require_human_control,
        )

    primary = texts[PRIMARY]
    missing_colors = sorted(color for color in REQUIRED_PRIMARY_COLORS if color not in primary.casefold())
    if missing_colors:
        errors.append(f"primary site missing canonical colors: {missing_colors}")
    if "datos simulados" not in primary.casefold() and "demo" not in primary.casefold():
        errors.append("primary site must visibly label demonstration/simulated data")

    readme = texts[README].casefold()
    if "main" not in readme or "production" not in readme:
        errors.append("README must preserve main-vs-production release posture")
    for field in ("domain", "application_sha", "deployment_id"):
        value = str(production_lock[field]).casefold()
        if value not in readme:
            errors.append(f"README production release posture does not match authorized lock: {field}")

    secondary_readme = texts[SECONDARY_README].casefold()
    if "producción" not in secondary_readme and "production" not in secondary_readme:
        errors.append("secondary landing README must state publication/production authority boundary")
    if "recibo" not in secondary_readme and "receipt" not in secondary_readme:
        errors.append("secondary landing README must bind promotion to a publication receipt")

    return errors


if __name__ == "__main__":
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        sys.exit(1)
    print("PASS: RUMBO brand contract")
