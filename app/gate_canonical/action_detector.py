"""Canonical action detection from HTTP request.

Implementa detecção canônica baseada em templates de path com:
- Normalização de prefixo (/api/v1 removido)
- Colapso de parâmetros dinâmicos para templates
- Mapeamento explícito (path_template, method) → action

Correção C1: Contempla paths reais com parâmetros (ex: /preferences/{user_id})
Correção C2: Formaliza lógica "auto-detect" já existente em módulo canônico

Part of FASE 11 - Gate Engine Consolidation.
"""
from fastapi import Request

# Template-based action mapping (path normalizado, method) → action
ACTION_MAP = {
    ("/process", "POST"): "process",
    ("/preferences/{user_id}", "GET"): "preferences.get",
    ("/preferences/{user_id}", "PUT"): "preferences.put",
    ("/preferences/{user_id}", "DELETE"): "preferences.delete",
    # Futuro: ("/plan", "POST"): "plan.create", etc.
}


def normalize_path(raw_path: str) -> str:
    """Normalize request path for action detection.
    
    Rules:
    1. Remove /api/v1 prefix (standard API prefix)
    2. Collapse dynamic parameters to {param_name} template
       - UUID-like segments → {user_id}, {operation_id}, etc.
       - Preserve path structure for matching
    
    Examples:
        /api/v1/preferences/test-user-f99a → /preferences/{user_id}
        /api/v1/process → /process
        /preferences/abc123 → /preferences/{user_id}
    
    Returns:
        normalized_path (str): template path for ACTION_MAP lookup
    """
    # Remove /api/v1 prefix
    path = raw_path
    if path.startswith("/api/v1"):
        path = path[7:]  # len("/api/v1") = 7
    
    # Collapse dynamic segments to templates
    # Pattern: /preferences/<qualquer-coisa> → /preferences/{user_id}
    # Pattern: /operation/<uuid> → /operation/{operation_id}
    
    if path.startswith("/preferences/"):
        # Qualquer /preferences/<algo> vira /preferences/{user_id}
        return "/preferences/{user_id}"
    
    # Outros patterns futuros aqui
    # if path.startswith("/operation/"):
    #     return "/operation/{operation_id}"
    
    # Path sem parâmetros dinâmicos (ex: /process)
    return path


def detect_action(request: Request) -> str:
    """Detect action from request path and method.
    
    Process:
    1. Normalize path (remove /api/v1, collapse params)
    2. Lookup in ACTION_MAP by (normalized_path, method)
    3. If not found, raise GateError(G8_UNKNOWN_ACTION)
    
    Returns:
        action_id (str): canonical action identifier
    
    Raises:
        GateError: if no mapping found (G8_UNKNOWN_ACTION)
    
    Resposta R3 (Arquiteto): G8 retorna 500 (bug interno) pois gate roda
    antes do roteamento. Se path chegou até o gate, deveria ter mapping.
    404 seria para "rota não existe" (fora do gate).
    """
    normalized_path = normalize_path(request.url.path)
    key = (normalized_path, request.method)
    action = ACTION_MAP.get(key)
    
    if action is None:
        from app.gate_errors import GateError, ReasonCode
        raise GateError(
            reason_code=ReasonCode.G8_UNKNOWN_ACTION,
            message=f"No action mapping for {request.method} {request.url.path} (normalized: {normalized_path})",
            http_status=500  # Bug interno (gate deveria ter mapping)
        )
    
    return action
