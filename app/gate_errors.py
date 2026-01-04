"""Gate-specific exceptions with reason codes.

Correção C5: reason_code padronizado em detail["reason_code"]
para garantir que audit logger consome sempre da mesma fonte.

Part of FASE 11 - Gate Engine Consolidation.
"""
from enum import Enum
from fastapi import HTTPException


class ReasonCode(str, Enum):
    """Canonical reason codes for gate failures.
    
    These codes are stable and must not change, as they are used for:
    - Audit trail
    - Metrics/alerting
    - Client error handling
    """
    G0_AUTH_NOT_CONFIGURED = "G0_AUTH_NOT_CONFIGURED"
    G8_UNKNOWN_ACTION = "G8_UNKNOWN_ACTION"
    G9_MISSING_PROFILE = "G9_MISSING_PROFILE"
    G10_BODY_PARSE_ERROR = "G10_BODY_PARSE_ERROR"
    G11_INVALID_PAYLOAD = "G11_INVALID_PAYLOAD"


class GateError(HTTPException):
    """Exception for gate failures (fail-closed).
    
    Correção C5: reason_code padronizado em detail["reason_code"]
    para garantir que audit logger consome sempre da mesma fonte.
    
    Attributes:
        reason_code: canonical reason code (for audit)
        message: human-readable message
        http_status: HTTP status code to return
    
    Example:
        raise GateError(
            reason_code=ReasonCode.G8_UNKNOWN_ACTION,
            message="No mapping for POST /unknown",
            http_status=500
        )
    """
    def __init__(self, reason_code: ReasonCode, message: str, http_status: int = 403):
        # Armazenar reason_code como atributo (compatibilidade)
        self.reason_code = reason_code
        
        # CRÍTICO: reason_code deve estar em detail["reason_code"]
        # para ser consumido pelo audit logger (fonte canônica)
        super().__init__(status_code=http_status, detail={
            "reason_code": reason_code.value,  # Fonte canônica para audit
            "message": message,
            "type": "gate_error"
        })
