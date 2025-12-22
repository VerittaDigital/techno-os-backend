from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Set, Tuple

from app.contracts.gate_v1 import (
    GateDecision,
    GateInput,
    GateReason,
    GateReasonCode,
    GateResult,
)
from app.gate_artifacts import profiles_fingerprint_sha256
from app.gate_profiles import PolicyProfile, get_profile

FORBIDDEN_ADMIN_KEYS_BASELINE: Set[str] = {
    "admin_signal",
    "admin",
    "root",
    "override",
    "system_prompt",
}


@dataclass(frozen=True)
class Rule:
    name: str
    fn: Callable[[GateInput, PolicyProfile], Tuple[bool, List[GateReason], List[str]]]


def _deny(code: GateReasonCode, message: str, evidence: dict | None = None) -> List[GateReason]:
    return [GateReason(code=code, message=message, evidence=evidence or {})]


def _effective_allow_external(inp: GateInput, profile: PolicyProfile) -> bool:
    # Fail-closed: só permite se AMBOS permitirem
    return bool(inp.allow_external and profile.allow_external)


def _effective_deny_unknown_fields(inp: GateInput, profile: PolicyProfile) -> bool:
    # Fail-closed: se QUALQUER um exigir deny, aplica deny
    return bool(inp.deny_unknown_fields or profile.deny_unknown_fields)


def rule_profile_presence(inp: GateInput, profile: PolicyProfile) -> Tuple[bool, List[GateReason], List[str]]:
    # Este rule existe apenas para garantir que o engine opera com profile resolvido.
    return True, [], []


def rule_forbidden_admin_keys(inp: GateInput, profile: PolicyProfile) -> Tuple[bool, List[GateReason], List[str]]:
    keys = set(inp.payload.keys())
    forbidden = set(FORBIDDEN_ADMIN_KEYS_BASELINE).union(set(profile.forbidden_keys))
    hit = sorted(keys.intersection(forbidden))
    if hit:
        return (
            False,
            _deny(
                GateReasonCode.ADMIN_SIGNAL_FORBIDDEN,
                "Administrative keys are forbidden.",
                {"keys": hit, "profile": profile.name},
            ),
            hit,
        )
    return True, [], []


def rule_external_fields_policy(inp: GateInput, profile: PolicyProfile) -> Tuple[bool, List[GateReason], List[str]]:
    present = [k for k in ("external_id", "external_source") if k in inp.payload]
    if present and not _effective_allow_external(inp, profile):
        return (
            False,
            _deny(
                GateReasonCode.EXTERNAL_FIELDS_NOT_ALLOWED,
                "External fields not allowed by policy.",
                {
                    "present": present,
                    "profile": profile.name,
                    "effective_allow_external": False,
                },
            ),
            present,
        )
    return True, [], present


def rule_unknown_fields_fail_closed(inp: GateInput, profile: PolicyProfile) -> Tuple[bool, List[GateReason], List[str]]:
    allow = set(profile.allowlist)
    keys = set(inp.payload.keys())
    unknown = sorted(keys.difference(allow))

    if unknown and _effective_deny_unknown_fields(inp, profile):
        return (
            False,
            _deny(
                GateReasonCode.UNKNOWN_FIELDS_PRESENT,
                "Unknown fields present (fail-closed).",
                {
                    "unknown": unknown,
                    "profile": profile.name,
                    "effective_deny_unknown_fields": True,
                },
            ),
            unknown,
        )
    return True, [], sorted(keys)


DEFAULT_RULES: Sequence[Rule] = (
    Rule("profile_presence", rule_profile_presence),
    Rule("forbidden_admin_keys", rule_forbidden_admin_keys),
    Rule("external_fields_policy", rule_external_fields_policy),
    Rule("unknown_fields_fail_closed", rule_unknown_fields_fail_closed),
)


def evaluate_gate(inp: GateInput, rules: Iterable[Rule] = DEFAULT_RULES) -> GateResult:
    """
    Determinístico e fail-closed.
    - Resolve profile por action (se não existir => DENY)
    - Avalia regras em ordem com short-circuit
    - Qualquer exceção => DENY (com evidência do exception type)
    - P1.5: Retorna profile_hash e matched_rules (regras que casaram)
    """
    evaluated_keys: List[str] = []
    reasons: List[GateReason] = []
    matched_rules: List[str] = []  # ← P1.5: Track which rules matched
    
    # P1.5: Always compute profile_hash (never empty)
    profile_hash = profiles_fingerprint_sha256()

    profile = get_profile(inp.action)
    if profile is None:
        reasons.extend(
            _deny(
                GateReasonCode.UNKNOWN_ACTION,
                "Action is not recognized.",
                {"action": inp.action},
            )
        )
        matched_rules.append("UNKNOWN_ACTION")  # ← P1.5: Mark which rule triggered denial
        return GateResult(
            decision=GateDecision.DENY,
            reasons=reasons,
            action=inp.action,
            evaluated_keys=evaluated_keys,
            profile_hash=profile_hash,
            matched_rules=matched_rules,
        )

    try:
        for rule in rules:
            ok, r_reasons, r_keys = rule.fn(inp, profile)

            for k in r_keys:
                if k not in evaluated_keys:
                    evaluated_keys.append(k)

            if not ok:
                # P1.5: Track which rule caused denial
                matched_rules.append(rule.name)
                reasons.extend(r_reasons)
                return GateResult(
                    decision=GateDecision.DENY,
                    reasons=reasons,
                    action=inp.action,
                    evaluated_keys=evaluated_keys,
                    profile_hash=profile_hash,
                    matched_rules=matched_rules,
                )

        reasons.append(GateReason(code=GateReasonCode.OK, message="Gate passed.", evidence={"action": inp.action, "profile": profile.name}))
        return GateResult(
            decision=GateDecision.ALLOW,
            reasons=reasons,
            action=inp.action,
            evaluated_keys=evaluated_keys,
            profile_hash=profile_hash,
            matched_rules=matched_rules,  # ← Empty for ALLOW (no rules blocked)
        )

    except Exception as exc:
        reasons.extend(
            _deny(
                GateReasonCode.RULE_EXCEPTION_FAIL_CLOSED,
                "Exception during rule evaluation; fail-closed.",
                {"exception": exc.__class__.__name__, "profile": profile.name},
            )
        )
        matched_rules.append("RULE_EXCEPTION")  # ← P1.5: Mark exception as matched reason
        return GateResult(
            decision=GateDecision.DENY,
            reasons=reasons,
            action=inp.action,
            evaluated_keys=evaluated_keys,
            profile_hash=profile_hash,
            matched_rules=matched_rules,
        )

