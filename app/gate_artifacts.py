from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from app.gate_profiles import DEFAULT_PROFILES, PolicyProfile


def _sorted_list(xs: List[str]) -> List[str]:
    return sorted(xs)


def export_profiles_dict() -> Dict[str, Any]:
    """
    Export determinístico do catálogo de profiles.

    Retorna estrutura canônica (ordenada) para:
    - auditoria
    - evidência de governança
    - hashing / versioning
    """
    items = []
    for action in sorted(DEFAULT_PROFILES.keys()):
        p: PolicyProfile = DEFAULT_PROFILES[action]
        items.append(
            {
                "action": action,
                "name": p.name,
                "deny_unknown_fields": bool(p.deny_unknown_fields),
                "allow_external": bool(p.allow_external),
                "allowlist": _sorted_list(list(p.allowlist)),
                "forbidden_keys": _sorted_list(list(p.forbidden_keys)),
            }
        )
    return {"profiles": items}


def export_profiles_json() -> str:
    """
    JSON canônico determinístico: sort_keys=True + separators fixos.
    """
    data = export_profiles_dict()
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def profiles_fingerprint_sha256() -> str:
    """
    Fingerprint estável do catálogo de profiles.
    """
    blob = export_profiles_json().encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
