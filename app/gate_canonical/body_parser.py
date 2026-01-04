"""HTTP body parsing by method (fail-closed).

Correção C4: Lançar GateError com reason_code estável (G10_BODY_PARSE_ERROR)
para garantir audit trail consistente.

Resposta Q2 (Arquiteto): GET/DELETE ignoram body (tolerante), mas registram
warning leve em audit se Content-Length > 0 (não mascara totalmente).

Part of FASE 11 - Gate Engine Consolidation.
"""
from fastapi import Request
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def parse_body_by_method(request: Request) -> Dict[str, Any]:
    """Parse request body according to HTTP method.
    
    Rules:
    - GET/DELETE: body is optional, return {} (ignore body if present)
      - Se Content-Length > 0, registra warning em audit (não deny)
    - POST/PUT/PATCH: body is required, parse JSON
      - Se ausente ou inválido: GateError(G10_BODY_PARSE_ERROR, 422)
    - OPTIONS/HEAD: return {} (skip parsing)
    
    Returns:
        dict: parsed body or empty dict
    
    Raises:
        GateError(G10_BODY_PARSE_ERROR): if required body is missing/invalid
    """
    from app.gate_errors import GateError, ReasonCode
    
    if request.method in ("GET", "DELETE"):
        # Body opcional para GET/DELETE (tolerante)
        # Warning se body presente (não mascara bug de client)
        content_length = request.headers.get("content-length", "0")
        if content_length != "0":
            logger.warning(
                f"GET/DELETE request with non-empty body (Content-Length: {content_length}). "
                f"Body ignored. Path: {request.url.path}, Method: {request.method}"
            )
        return {}
    
    if request.method in ("POST", "PUT", "PATCH"):
        # Body obrigatório para métodos de escrita
        try:
            body = await request.json()
            if not isinstance(body, dict):
                raise GateError(
                    reason_code=ReasonCode.G10_BODY_PARSE_ERROR,
                    message="Body must be a JSON object",
                    http_status=422
                )
            return body
        except GateError:
            # Re-raise GateError (já tem reason_code)
            raise
        except Exception as e:
            # JSON parse error ou body ausente
            raise GateError(
                reason_code=ReasonCode.G10_BODY_PARSE_ERROR,
                message=f"Invalid or missing JSON body: {str(e)}",
                http_status=422
            )
    
    # Métodos não suportados (OPTIONS, HEAD, etc.)
    # Retornar {} e seguir (não gerar erro)
    return {}
