# Artifacts — Evidence Collection

## 📋 Propósito

Este diretório armazena evidências de implementação coletadas durante fases críticas do projeto.

**Conteúdo:** Logs, configs, outputs, checksums, validações.

**Governança:** Evidence-based execution (V-COF).

---

## 🗂️ Estrutura

```
artifacts/
├── f9_5/              # Evidências Fase 9.5
├── f9_6/              # Evidências Fase 9.6 (consolidado workspace_cleanup)
├── f9_8/              # Evidências Fase 9.8 (múltiplas subpastas)
├── f9_8a/             # Evidências Fase 9.8A (SSH hardening)
├── f9_8_1/            # Evidências Fase 9.8.1 (Prometheus auth)
└── archive/           # Artifacts >90 dias (compactados)
```

**Nomenclatura:** `[fase]_[descrição]_[timestamp]/`

**Exemplo:** `f9_8_1_risk1_20260103_141623/`

---

## ⏳ Política de Retenção

**Fase ativa:** 90 dias  
- Evidências rastreáveis e acessíveis
- Utilizadas para auditoria e rollback

**Após 90 dias:** Mover para `archive/`  
- Compactar em `.tar.gz`
- Manter estrutura de diretórios no nome: `f9_8_1_risk1_20260103_141623.tar.gz`

**Após 1 ano:** Deletar de `archive/`  
- Manter apenas em backup VPS
- Evidências permanentes em SEAL documents

---

## 📦 Estrutura de Artifact

Cada artifact directory deve conter:

```
f9_8_1_risk1_20260103_141623/
├── meta.txt                      # Metadata (fase, data, autor, objetivo)
├── checksums.sha256              # Checksums de todos os arquivos
├── [config_files].conf           # Configs relevantes
├── [logs].log                    # Logs coletados
├── [outputs].txt                 # Outputs de comandos
└── FINAL_REPORT.md               # Resumo executivo (opcional)
```

**Checksums obrigatórios:**
```bash
cd artifacts/[fase]_[descrição]_[timestamp]/
sha256sum *.txt *.log *.conf > checksums.sha256
```

---

## 🔍 Consulta

Para validar implementação de uma fase:

1. **Localizar artifact:**  
   ```bash
   ls -la artifacts/f9_8_1*/
   ```

2. **Verificar integridade:**  
   ```bash
   cd artifacts/f9_8_1_risk1_20260103_141623/
   sha256sum -c checksums.sha256
   ```

3. **Ler evidências:**  
   ```bash
   cat meta.txt
   cat FINAL_REPORT.md
   ```

4. **Correlacionar com SEAL:**  
   Verificar referência no SEAL correspondente (ex: `sessions/f9.8.1/SEAL-*.md`)

---

## 🛠️ Como Criar Artifact

**Template de script:**

```bash
#!/bin/bash
# Exemplo: Coletar evidências F9.9-B RISK-3

PHASE="f9_9_b_risk3"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARTIFACT_DIR="artifacts/${PHASE}_${TIMESTAMP}"

mkdir -p "$ARTIFACT_DIR"

# Meta
cat > "$ARTIFACT_DIR/meta.txt" <<EOF
Fase: F9.9-B
Risk: RISK-3 (API rate limiting)
Data: $(date -Iseconds)
Autor: deploy@vps
Objetivo: Validar implementação de rate limiting
EOF

# Evidências
curl -I https://api.example.com > "$ARTIFACT_DIR/api_health.txt"
docker logs techno-api > "$ARTIFACT_DIR/api_logs.txt"
cp /etc/nginx/sites-available/api.conf "$ARTIFACT_DIR/nginx_api.conf"

# Checksum
cd "$ARTIFACT_DIR"
sha256sum *.txt *.conf > checksums.sha256

echo "Artifact criado: $ARTIFACT_DIR"
```

---

## 🗄️ Arquivamento

**Script de arquivamento (executar manualmente):**

```bash
#!/bin/bash
# Archive artifacts >90 dias

CUTOFF_DATE=$(date -d '90 days ago' +%s)

cd artifacts/

for dir in f9_*_*/; do
  dir_timestamp=$(echo "$dir" | grep -oP '\d{8}_\d{6}')
  dir_epoch=$(date -d "${dir_timestamp:0:8} ${dir_timestamp:9:2}:${dir_timestamp:11:2}:${dir_timestamp:13:2}" +%s)
  
  if [ "$dir_epoch" -lt "$CUTOFF_DATE" ]; then
    echo "Archiving: $dir"
    tar czf "archive/${dir%.tar.gz/}.tar.gz" "$dir"
    rm -rf "$dir"
  fi
done

echo "Archival complete. Check artifacts/archive/"
```

---

## 📚 Referências

- **SEAL Documents:** `/sessions/` (correlacionar com artifacts)
- **VPS Backups:** `/backups/` (cópia redundante de artifacts críticos)
- **Governança V-COF:** `.github/copilot-instructions.md`

---

**Criado:** 2026-01-03  
**Política:** Evidence-based execution  
**Retenção:** 90 dias (fase ativa) → 1 ano (archive) → backup VPS
