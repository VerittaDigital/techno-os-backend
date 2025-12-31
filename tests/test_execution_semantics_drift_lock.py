"""
DRIFT LOCK — EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt

Objetivo:
Garantir que o arquivo de norma EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt
não seja alterado sem atualização consciente do hash canônico.

Regra:
- Se o conteúdo do arquivo mudar → o teste falha
- Para passar novamente → atualizar HASH_CANON_V1 com o novo SHA-256
- Isso força versionamento explícito (v1.0.2, v1.1, etc.)

Rationale:
Mudanças na norma de governança devem ser rastreáveis e intencionais.
O drift lock previne edições acidentais ou não-documentadas.
"""

import hashlib
from pathlib import Path


# Hash canônico do conteúdo atual (UTF-8 bytes)
# Calculado em: 2025-12-31
# Se este teste falhar, você editou o arquivo de norma.
# → Versione a norma (ex.: v1.0.2 ou v1.1)
# → Atualize HASH_CANON_V1 com o novo SHA-256
HASH_CANON_V1 = "0c3c0f85c953f4921a9829e22280e6b7bb53d76068fbc5499e68dbe89908b110"


def test_execution_semantics_drift_lock():
    """
    Verify EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt has not drifted.
    
    If this test fails:
    1) Check git diff EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt
    2) If change is intentional → version the norm (v1.0.2 or v1.1)
    3) Update HASH_CANON_V1 with new SHA-256
    4) Document change in commit message
    """
    norm_file = Path("EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt")
    
    # Step 1: Verify file exists
    if not norm_file.exists():
        raise FileNotFoundError(
            f"DRIFT LOCK FAILED: {norm_file} not found. "
            f"Governance norm file must be present in repository root."
        )
    
    # Step 2: Compute SHA-256 of current content (UTF-8 bytes)
    content_bytes = norm_file.read_bytes()
    computed_hash = hashlib.sha256(content_bytes).hexdigest()
    
    # Step 3: Compare with canonical hash
    if computed_hash != HASH_CANON_V1:
        raise AssertionError(
            f"\n"
            f"╔════════════════════════════════════════════════════════════════╗\n"
            f"║ DRIFT LOCK VIOLATION — EXECUTION_SEMANTICS_V1                 ║\n"
            f"╠════════════════════════════════════════════════════════════════╣\n"
            f"║ O arquivo EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt foi       ║\n"
            f"║ alterado sem atualização do hash canônico.                    ║\n"
            f"║                                                                ║\n"
            f"║ Hash esperado: {HASH_CANON_V1}                                ║\n"
            f"║ Hash atual:    {computed_hash}                                ║\n"
            f"║                                                                ║\n"
            f"║ AÇÃO NECESSÁRIA:                                              ║\n"
            f"║ 1) Revisar: git diff EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt║\n"
            f"║ 2) Se mudança é intencional:                                  ║\n"
            f"║    - Versionar a norma (ex.: v1.0.2 ou v1.1)                  ║\n"
            f"║    - Atualizar HASH_CANON_V1 neste teste                      ║\n"
            f"║    - Documentar mudança no commit                             ║\n"
            f"║ 3) Se mudança foi acidental:                                  ║\n"
            f"║    - Reverter alterações no arquivo                           ║\n"
            f"╚════════════════════════════════════════════════════════════════╝\n"
        )
    
    # If we reach here, hash matches → norm is stable
    assert computed_hash == HASH_CANON_V1, "Hash verification sanity check"
