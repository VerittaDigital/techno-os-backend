"""
Integration test for 1:1 mapping between action_matrix and gate_profiles.

Correção C7: Valida apenas PUBLIC_ACTIONS (não full DEFAULT_PROFILES).

Objetivo:
Garantir que toda action em action_matrix.allowed_actions tenha um
PolicyProfile correspondente em gate_profiles.DEFAULT_PROFILES.

Rationale:
Falha neste teste indica drift de governança:
- Action foi adicionada ao matrix sem criar PolicyProfile
- Profile foi removido sem atualizar matrix

Part of FASE 11 - Gate Engine Consolidation.
"""
from app.action_matrix import get_action_matrix
from app.gate_profiles import get_profile


def test_action_matrix_and_profiles_are_1_to_1():
    """
    Validate 1:1 mapping between action_matrix and gate_profiles.
    
    For each action in action_matrix.allowed_actions:
    - Must have a corresponding PolicyProfile
    - Profile must be retrievable via get_profile(action)
    
    Correção C7: Test only validates PUBLIC_ACTIONS (matrix allowed_actions),
    not all profiles in DEFAULT_PROFILES (some profiles may be private/internal).
    """
    matrix = get_action_matrix()
    allowed_actions = matrix.allowed_actions
    
    # Must have at least 1 action (fail-closed)
    assert len(allowed_actions) > 0, "action_matrix.allowed_actions cannot be empty"
    
    missing_profiles = []
    
    for action in allowed_actions:
        profile = get_profile(action)
        if profile is None:
            missing_profiles.append(action)
    
    # If missing_profiles is not empty, fail with clear message
    if missing_profiles:
        raise AssertionError(
            f"\n"
            f"╔════════════════════════════════════════════════════════════════╗\n"
            f"║ GATE INTEGRITY VIOLATION — 1:1 MAPPING                        ║\n"
            f"╠════════════════════════════════════════════════════════════════╣\n"
            f"║ The following actions in action_matrix.allowed_actions        ║\n"
            f"║ do NOT have corresponding PolicyProfile in gate_profiles:     ║\n"
            f"║                                                                ║\n"
            f"║ Missing profiles for actions:                                 ║\n"
            f"║ {', '.join(missing_profiles):<61} ║\n"
            f"║                                                                ║\n"
            f"║ REQUIRED ACTION:                                              ║\n"
            f"║ 1) Add PolicyProfile for each missing action in               ║\n"
            f"║    app/gate_profiles.py (DEFAULT_PROFILES)                    ║\n"
            f"║ 2) Ensure action name matches exactly                         ║\n"
            f"║ 3) Define allowlist with required fields                      ║\n"
            f"║                                                                ║\n"
            f"║ Example:                                                      ║\n"
            f"║   ACTION_MY_ACTION = \"my_action\"                             ║\n"
            f"║   DEFAULT_PROFILES[ACTION_MY_ACTION] = PolicyProfile(...)    ║\n"
            f"╚════════════════════════════════════════════════════════════════╝\n"
        )
    
    # Success: all actions have profiles
    print(f"✅ Gate integrity check passed: {len(allowed_actions)} actions mapped to profiles")

