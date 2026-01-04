from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet


@dataclass(frozen=True)
class PolicyProfile:
    """
    Profile canônico por ação.

    - allowlist: campos permitidos no payload
    - deny_unknown_fields: se True, qualquer chave fora do allowlist => DENY (fail-closed)
    - allow_external: se True, permite external_id/external_source quando presentes
    - forbidden_keys: chaves proibidas (além do baseline do engine)
    """
    name: str
    allowlist: FrozenSet[str]
    deny_unknown_fields: bool = True
    allow_external: bool = False
    forbidden_keys: FrozenSet[str] = frozenset()


ACTION_AGENT_RUN = "AGENT.RUN"
ACTION_ARCONTE_SIGNAL = "ARCONTE.SIGNAL"
ACTION_PROCESS = "process"

# FASE 11: Actions de preferences
ACTION_PREFERENCES_GET = "preferences.get"
ACTION_PREFERENCES_PUT = "preferences.put"
ACTION_PREFERENCES_DELETE = "preferences.delete"

DEFAULT_PROFILES: Dict[str, PolicyProfile] = {
    ACTION_AGENT_RUN: PolicyProfile(
        name="agent_run.v1",
        allowlist=frozenset({"agent_id", "task", "external_id", "external_source"}),
        deny_unknown_fields=True,
        allow_external=False,
        forbidden_keys=frozenset(),
    ),
    ACTION_ARCONTE_SIGNAL: PolicyProfile(
        name="arconte_signal.v1",
        allowlist=frozenset({"signal", "external_id", "external_source"}),
        deny_unknown_fields=True,
        allow_external=False,
        forbidden_keys=frozenset(),
    ),
    ACTION_PROCESS: PolicyProfile(
        name="process.v1",
        allowlist=frozenset({"text"}),
        deny_unknown_fields=True,
        allow_external=False,
        forbidden_keys=frozenset(),
    ),
    # FASE 11: Profiles para preferences endpoints
    ACTION_PREFERENCES_GET: PolicyProfile(
        name="preferences_get.v1",
        allowlist=frozenset({"user_id"}),
        deny_unknown_fields=True,
        allow_external=False,
        forbidden_keys=frozenset(),
    ),
    ACTION_PREFERENCES_PUT: PolicyProfile(
        name="preferences_put.v1",
        allowlist=frozenset({"user_id", "tone_preference", "output_format", "language"}),
        deny_unknown_fields=True,
        allow_external=False,
        forbidden_keys=frozenset(),
    ),
    ACTION_PREFERENCES_DELETE: PolicyProfile(
        name="preferences_delete.v1",
        allowlist=frozenset({"user_id"}),
        deny_unknown_fields=True,
        allow_external=False,
        forbidden_keys=frozenset(),
    ),
}


def get_profile(action: str) -> PolicyProfile | None:
    return DEFAULT_PROFILES.get(action)


def get_profiles_version() -> str:
    from app.gate_artifacts import profiles_fingerprint_sha256
    return profiles_fingerprint_sha256()
