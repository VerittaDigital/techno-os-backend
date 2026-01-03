# BACKUP PROCEDURE — Pre F9.9-B
**Snapshot Completo do Estado Estável Pós F9.8**

## METADATA
- **Data**: 2026-01-03
- **Objetivo**: Backup de estado estável antes de F9.9-B (LLM Hardening)
- **Estado**: F9.8 + F9.8A + F9.8.1 + STEP 10.2 concluídos
- **Branch**: stage/f9.8-observability (commit e9907a8)

---

## ESTADO DO SISTEMA (ESTÁVEL)

### Infraestrutura
- ✅ VPS: Ubuntu 24.04 LTS (72.61.219.157)
- ✅ Nginx: 1.24.0 (TLS ECDSA, Basic Auth ativo)
- ✅ Docker: 4 containers (Prometheus, Grafana, Cadvisor, Node-Exporter)
- ✅ SSH: ed25519 key-only, password auth disabled
- ✅ Observability: Prometheus + Grafana com autenticação

### Segurança Aplicada
- ✅ TLS certificados (Let's Encrypt ECDSA)
- ✅ Prometheus Basic Auth (RISK-1 mitigado)
- ✅ SSH hardening (password auth desabilitado)
- ✅ Sudoers restricted (least privilege)
- ✅ Cloud-init SSH desabilitado

### Artefatos Preservados (VPS)
```
/opt/techno-os/artifacts/
├── f9_8a_sudo_sshkey_20260103_123202Z/
│   ├── 20 arquivos (F9.8A)
│   └── step10_2/ (7 arquivos - SSH hardening)
└── f9_8_1_risk1_20260103_141623/
    └── 16 arquivos (Prometheus auth)
```

**Total**: 43+ evidências + SEALs

---

## BACKUP VPS — PROCEDIMENTO RECOMENDADO

### OPÇÃO 1: Snapshot Completo (Provider Level)
Se o provider (HostGator/similar) oferece snapshots:

```bash
# Via painel do provider
1. Acessar painel de gerenciamento VPS
2. Criar snapshot: "pre-f9.9b-llm-hardening-2026-01-03"
3. Validar que snapshot foi criado
4. Anotar snapshot ID
```

**Vantagens**: Restauração completa em minutos, estado exato do sistema

---

### OPÇÃO 2: Backup Manual Seletivo (SSH)

Execute no terminal VPS:

```bash
# Criar diretório de backup
BACKUP_DIR="/opt/techno-os/backups/pre_f9_9b_$(date +%Y%m%d)"
sudo mkdir -p "$BACKUP_DIR"

# 1. Configurações críticas
sudo tar -czf "$BACKUP_DIR/etc_configs.tar.gz" \
  /etc/nginx/ \
  /etc/ssh/sshd_config* \
  /etc/sudoers.d/ \
  /etc/cloud/cloud.cfg.d/ \
  --exclude='*.log'

# 2. Observability stack
sudo tar -czf "$BACKUP_DIR/observability.tar.gz" \
  /opt/techno-os/observability/ \
  --exclude='*.log'

# 3. Artefatos e evidências
sudo tar -czf "$BACKUP_DIR/artifacts.tar.gz" \
  /opt/techno-os/artifacts/

# 4. Docker configs
docker-compose -f /opt/techno-os/observability/docker-compose.yml config \
  > "$BACKUP_DIR/docker-compose.yml"

# 5. Lista de containers
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" \
  > "$BACKUP_DIR/docker_containers.txt"

# 6. Lista de volumes
docker volume ls > "$BACKUP_DIR/docker_volumes.txt"

# 7. Sistema
sudo dpkg --get-selections > "$BACKUP_DIR/packages_installed.txt"
sudo ufw status verbose > "$BACKUP_DIR/ufw_status.txt" 2>/dev/null || echo "UFW não ativo"

# 8. Inventário
ls -lhR "$BACKUP_DIR" > "$BACKUP_DIR/backup_inventory.txt"

# 9. Checksum
cd "$BACKUP_DIR" && sha256sum *.tar.gz *.txt *.yml > checksums.sha256

echo "✅ Backup concluído: $BACKUP_DIR"
```

---

### OPÇÃO 3: Backup Off-Site (Download Local)

Após OPÇÃO 2, execute no **seu terminal local**:

```bash
# Criar diretório local
mkdir -p ~/techno-os-backups/pre-f9.9b-2026-01-03

# Download do backup
scp -r techno-os:/opt/techno-os/backups/pre_f9_9b_* \
  ~/techno-os-backups/pre-f9.9b-2026-01-03/

# Validar checksums
cd ~/techno-os-backups/pre-f9.9b-2026-01-03/pre_f9_9b_*
sha256sum -c checksums.sha256
```

---

## VALIDAÇÃO PÓS-BACKUP

### Checklist
- [ ] Backup criado com sucesso
- [ ] Checksums validados
- [ ] Tamanho razoável (esperado: 50-200 MB configs, ~500MB+ com volumes Docker)
- [ ] Inventário de arquivos presente
- [ ] Backup testável (extract test em diretório temporário)

### Teste de Restauração (Dry-Run)
```bash
# Testar extração (NÃO sobrescrever)
mkdir /tmp/backup_test
cd /tmp/backup_test
tar -tzf $BACKUP_DIR/etc_configs.tar.gz | head -20
echo "✅ Tar válido e pode ser extraído"
```

---

## ROLLBACK PROCEDURE (Se F9.9-B Falhar)

### Cenário 1: Rollback Específico (Nginx/SSH)
```bash
# Restaurar configs
sudo tar -xzf $BACKUP_DIR/etc_configs.tar.gz -C /

# Reload serviços
sudo systemctl reload nginx
sudo systemctl reload ssh

# Validar
curl -skI https://prometheus.verittadigital.com
ssh techno-os echo OK
```

### Cenário 2: Rollback Docker Stack
```bash
cd /opt/techno-os/observability
docker-compose down
sudo tar -xzf $BACKUP_DIR/observability.tar.gz -C /opt/techno-os/
docker-compose up -d
```

### Cenário 3: Snapshot Completo (Provider)
```
1. Acessar painel provider
2. Selecionar snapshot "pre-f9.9b-llm-hardening-2026-01-03"
3. Restaurar VPS para snapshot
4. Validar acesso SSH e serviços
```

---

## PRÓXIMOS PASSOS (Após Backup)

1. ✅ Backup VPS concluído e validado
2. ✅ Git branch F9.8 merged/pushed
3. ✅ Ponto de restauração seguro estabelecido
4. → **Iniciar F9.9-B** (LLM Hardening)

**Branch para F9.9-B**: `stage/f9.9-b-llm-hardening` (já criada)

---

## RISCOS PENDENTES (F9.9-B)

Conforme doc `F9.9-B-HARDENING-PENDENCIES.md`:

- **RISK-3**: API rate limiting não configurado
- **RISK-4**: Input sanitization não implementado  
- **RISK-5**: LLM context injection possível
- **RISK-6**: Output validation insuficiente
- **RISK-7**: Logs não anonimizados
- **RISK-8**: Métricas de uso LLM ausentes

---

## ASSINATURAS

**Preparado por**: GitHub Copilot  
**Supervisor**: Vinicius  
**Governança**: V-COF (Fail-Closed + Backup Mandatory)

**Status**: PRONTO PARA F9.9-B  
**Data**: 2026-01-03
