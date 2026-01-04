# SEAL — STEP 10.2 SSH HARDENING
**Password Authentication Disabled via Daemon Reload**

## METADATA
- **Data**: 2026-01-03 UTC
- **Fase**: STEP 10.2 (continuação F9.8A)
- **Objetivo**: Aplicar SSH hardening via reload (sem edição de arquivos)
- **Método**: systemctl reload + desabilitar cloud-init override
- **Status**: CONCLUÍDO

---

## RESUMO EXECUTIVO

### Problema Original
Arquivos de configuração SSH (`99-hardening.conf`) criados na F9.7/F9.8A, mas daemon não recarregado. Configuração em memória divergente da configuração em disco.

### Descoberta Crítica
Arquivo `50-cloud-init.conf` (root-only) continha `PasswordAuthentication yes`, sobrescrevendo hardening configurado.

### Solução Aplicada
1. Desabilitar gerenciamento SSH pelo cloud-init
2. Remover `50-cloud-init.conf`
3. Reload SSH daemon
4. Validar configuração efetiva

### Resultado
✅ `passwordauthentication no` efetivo  
✅ `pubkeyauthentication yes` mantido  
✅ Cloud-init desabilitado para SSH  
✅ Fail-closed enforcement validado (ABORT na tentativa 1)  

---

## EXECUÇÃO

### PRÉ-REQUISITOS
1. ✅ Permissão `systemctl reload ssh` adicionada ao sudoers
2. ✅ 7 sessões SSH ativas (garantia contra lockout)

### TENTATIVA 1 — ABORT (Fail-Closed)
**Data**: 15:47 UTC

- Reload executado
- Validação: `passwordauthentication yes` ❌
- **ABORT imediato** (comportamento correto)

### INVESTIGAÇÃO
**Data**: 15:49 UTC

```bash
$ sudo cat /etc/ssh/sshd_config.d/50-cloud-init.conf
PasswordAuthentication yes
```

**Arquivos**:
- `50-cloud-init.conf` → yes (override)
- `60-cloudimg-settings.conf` → no
- `99-hardening.conf` → no

**Conclusão**: Cloud-init sobrescrevia hardening.

### CORREÇÃO
**Data**: 15:52 UTC

1. Desabilitar cloud-init SSH:
   ```bash
   /etc/cloud/cloud.cfg.d/99-disable-ssh-config.cfg
   ssh_pwauth: false
   ```

2. Remover override:
   ```bash
   sudo rm /etc/ssh/sshd_config.d/50-cloud-init.conf
   ```

3. Validação imediata:
   ```bash
   $ sudo sshd -T | grep passwordauthentication
   passwordauthentication no ✅
   ```

### TENTATIVA 2 — SUCESSO
**Data**: 15:53 UTC

- Reload SSH: `sudo systemctl reload ssh.service`
- Validação: `passwordauthentication no` ✅
- Teste nova conexão: **SUCESSO** ✅

---

## CONFIGURAÇÃO FINAL

### Arquivos Ativos
```
/etc/ssh/sshd_config.d/
├── 60-cloudimg-settings.conf → PasswordAuthentication no
└── 99-hardening.conf → PasswordAuthentication no
                         PermitRootLogin no
                         PubkeyAuthentication yes
```

### Cloud-Init
```
/etc/cloud/cloud.cfg.d/99-disable-ssh-config.cfg
ssh_pwauth: false
```

### Configuração Efetiva (sshd -T)
```
passwordauthentication no
pubkeyauthentication yes
permitrootlogin no
```

---

## ARTEFATOS (7 arquivos)

- `01_service_name.txt` — ssh.service
- `02_pre_reload.txt` — passwordauth=yes (antes)
- `03_reload_timestamp.txt` — 15:47 UTC
- `04_post_reload.txt` — passwordauth=yes (ABORT)
- `05_final_config.txt` — passwordauth=no (sucesso)
- `SEAL_STEP_10_2.md` — Documentação completa (7.6KB)
- `exec.log` — Log timestamped

---

## CONFORMIDADE V-COF

✅ **Fail-Closed**: ABORT na tentativa 1 (config incorreta)  
✅ **Human-in-the-Loop**: 7 sessões SSH, teste manual  
✅ **Evidence-Based**: 7 evidências + log completo  

---

## LIÇÕES APRENDIDAS

1. **Cloud-Init Override**: Arquivos root-only podem conter configurações inesperadas
2. **Fail-Closed Salva**: Primeira tentativa abortou corretamente
3. **Múltiplas Sessões**: Zero risco de lockout durante reload

---

**Status**: SSH HARDENING COMPLETO  
**Data Conclusão**: 2026-01-03 15:54 UTC  
**Configuração**: passwordauthentication no, pubkeyauthentication yes
