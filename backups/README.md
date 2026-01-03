# Backups — Disaster Recovery

## 📋 Propósito

Este diretório gerencia backups do sistema para disaster recovery.

**Conteúdo:** Backups pré-deploy, procedimentos de restore.

**Governança:** Rollback capability (V-COF).

---

## 🗂️ Estrutura

```
backups/
├── README.md           # Este arquivo
├── pre_f9_9b/          # Backup pré-F9.9-B (2026-01-03)
│   └── README.md       # Procedimentos específicos
└── archive/            # Backups antigos >30 dias
```

---

## ⏳ Política de Retenção

**Pre-deploy backups:** 30 dias  
- Criados antes de cada fase crítica
- Contém configs, observability, artifacts

**Daily backups (VPS):** 7 dias  
- Se implementado (planejado F9.9-B)
- Backup automatizado via cron

**Após 30 dias:** Mover para `archive/`  
- Compactar em `.tar.gz`
- Manter apenas metadados acessíveis

**Após 90 dias:** Deletar de `archive/`  
- Manter apenas em backup VPS remoto
- Provider-level snapshots (se disponível)

---

## 📦 Conteúdo de Backup

Cada backup pre-deploy deve conter:

### 1. Configs Críticos
- `/etc/nginx/` — Vhosts, TLS certs
- `/etc/ssh/` — SSH config, keys
- `/etc/sudoers.d/` — Sudoers customizados
- `/etc/cloud/cloud.cfg.d/` — Cloud-init overrides

### 2. Observability
- `/opt/techno-os/observability/` — Prometheus + Grafana configs
- Docker volumes: `prometheus_data`, `grafana_data`

### 3. Artifacts
- `/opt/techno-os/artifacts/` — Evidências de fases anteriores

### 4. Estado do Sistema
- `docker ps -a` — Containers ativos
- `docker volume ls` — Volumes Docker
- `dpkg -l` — Packages instalados
- `systemctl status` — Services críticos

---

## 🔍 Backup Atual

### Pre-F9.9-B (2026-01-03)
**Localização VPS:** `/opt/techno-os/backups/pre_f9_9b_20260103_161929`

**Conteúdo:**
- `etc_configs.tar.gz` — 37KB (nginx, ssh, sudoers, cloud-init)
- `observability.tar.gz` — 1.6KB (configs Prometheus/Grafana)
- `artifacts.tar.gz` — 78KB (evidências F9.8A, F9.8.1, STEP 10.2)
- `docker_containers.txt` — 832 bytes
- `docker_volumes.txt` — 166 bytes
- `packages_installed.txt` — 19KB
- `checksums.sha256` — 517 bytes

**Total:** 160KB

**Procedimentos:** Ver `backups/pre_f9_9b/README.md`

---

## 🛠️ Como Criar Backup

**Template de script:**

```bash
#!/bin/bash
# Backup pré-deploy (executar no VPS)

PHASE="pre_f9_9b"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/techno-os/backups/${PHASE}_${TIMESTAMP}"

mkdir -p "$BACKUP_DIR"

# 1. Configs
tar czf "$BACKUP_DIR/etc_configs.tar.gz" \
  /etc/nginx/ \
  /etc/ssh/ \
  /etc/sudoers.d/ \
  /etc/cloud/cloud.cfg.d/

# 2. Observability
tar czf "$BACKUP_DIR/observability.tar.gz" \
  /opt/techno-os/observability/

# 3. Artifacts
tar czf "$BACKUP_DIR/artifacts.tar.gz" \
  /opt/techno-os/artifacts/

# 4. Estado sistema
docker ps -a > "$BACKUP_DIR/docker_containers.txt"
docker volume ls > "$BACKUP_DIR/docker_volumes.txt"
dpkg -l > "$BACKUP_DIR/packages_installed.txt"

# 5. Checksums
cd "$BACKUP_DIR"
sha256sum *.tar.gz *.txt > checksums.sha256

echo "Backup criado: $BACKUP_DIR"
echo "Tamanho: $(du -sh $BACKUP_DIR | cut -f1)"
```

---

## 🔄 Disaster Recovery

### Procedimento de Restore

**Ver documentação completa:** `/docs/operations/DISASTER_RECOVERY.md`

**Resumo rápido:**

1. **SSH no VPS:**
   ```bash
   ssh deploy@72.61.219.157
   ```

2. **Localizar backup:**
   ```bash
   ls -la /opt/techno-os/backups/pre_f9_9b_*/
   ```

3. **Validar integridade:**
   ```bash
   cd /opt/techno-os/backups/pre_f9_9b_[timestamp]/
   sha256sum -c checksums.sha256
   ```

4. **Restore configs:**
   ```bash
   sudo tar xzf etc_configs.tar.gz -C /
   sudo systemctl reload nginx
   sudo systemctl reload ssh
   ```

5. **Restore observability:**
   ```bash
   tar xzf observability.tar.gz -C /opt/techno-os/
   docker-compose -f /opt/techno-os/docker-compose.yml restart
   ```

6. **Validar:**
   ```bash
   curl -I https://prometheus.verittadigital.com
   curl -I https://grafana.verittadigital.com
   docker ps
   ```

**Tempo estimado:** 15-20 minutos

---

## 📊 Testes de Restore

**Recomendação:** Testar restore em ambiente staging antes de produção.

**Frequência:** Após cada backup crítico (antes de cada fase).

**Checklist de validação:**
- [ ] Configs restaurados (diff com originais)
- [ ] Nginx funcional (TLS + vhosts)
- [ ] SSH funcional (pubkey auth)
- [ ] Docker containers UP
- [ ] Prometheus coletando métricas
- [ ] Grafana dashboards visíveis

---

## 📚 Referências

- **Disaster Recovery:** `/docs/operations/DISASTER_RECOVERY.md`
- **Artifacts:** `/artifacts/` (evidências correlacionadas)
- **SEAL Documents:** `/sessions/` (contexto de cada fase)
- **VPS State:** `/sessions/consolidation/SEAL-SESSION-*.md`

---

**Criado:** 2026-01-03  
**Política:** Backup antes de fases críticas  
**Retenção:** 30 dias (ativo) → 90 dias (archive) → remoto
