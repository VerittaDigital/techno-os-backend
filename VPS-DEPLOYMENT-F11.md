# VPS Deployment Instructions — F11-SEALED-v1.0

## Pre-Deployment Checklist

- [x] Branch pushed: `stage/f11-gate-consolidation`
- [x] Tag pushed: `F11-SEALED-v1.0`
- [x] Local tests: 387 passing
- [x] Smoke tests: 8/8 passing
- [x] SEAL document: Complete
- [ ] VPS backup: Pending
- [ ] VPS deployment: Pending
- [ ] VPS smoke test: Pending

---

## Option 1: Automated Deployment (Recommended)

### Step 1: SSH into VPS
```bash
ssh root@srv1241381.hstgr.cloud
```

### Step 2: Backup current state
```bash
cd /app/techno-os-backend
git log --oneline -1 > /tmp/pre-f11-commit.txt
docker compose ps > /tmp/pre-f11-containers.txt
cp /app/logs/audit.log /tmp/pre-f11-audit.log 2>/dev/null || true
```

### Step 3: Run deployment script
```bash
cd /app/techno-os-backend
curl -sSL https://raw.githubusercontent.com/VerittaDigital/techno-os-backend/stage/f11-gate-consolidation/vps_deploy_f11.sh | bash
```

Or with local script:
```bash
# From local machine
scp vps_deploy_f11.sh root@srv1241381.hstgr.cloud:/tmp/
ssh root@srv1241381.hstgr.cloud 'bash /tmp/vps_deploy_f11.sh'
```

### Step 4: Download evidence
```bash
# From local machine
scp root@srv1241381.hstgr.cloud:/tmp/f11-evidence-*.tar.gz .
tar xzf f11-evidence-*.tar.gz
cd f11-evidence-*/

# Review evidence
cat deployed_commit.txt       # Should show F11-SEALED-v1.0
cat smoke_test_output.txt     # Should end with "✓ CP-11.3 APPROVED"
cat audit_analysis.txt        # Check G8, G10, ALLOW counts
```

---

## Option 2: Manual Deployment (Conservative)

### Step 1: Connect and navigate
```bash
ssh root@srv1241381.hstgr.cloud
cd /app/techno-os-backend
```

### Step 2: Fetch updates
```bash
git fetch --all --tags --prune
git tag -l "F11*"  # Verify tag exists
```

### Step 3: Checkout tag
```bash
git checkout F11-SEALED-v1.0
git log --oneline --decorate -3
```

### Step 4: Rebuild services
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Step 5: Health check
```bash
sleep 10
curl -fsS http://localhost:8000/health | jq '.'
docker compose ps
docker compose logs --tail=50 api
```

### Step 6: Run smoke tests
```bash
export VERITTA_BETA_API_KEY="$(grep VERITTA_BETA_API_KEY .env | cut -d'=' -f2-)"
export API_BASE="http://localhost:8000"
bash smoke_test_cp11_3.sh
```

### Step 7: Check audit log
```bash
tail -20 /app/logs/audit.log | jq -r '[.timestamp, .decision, .reason_codes[0], .trace_id] | @tsv'
```

---

## Option 3: From Local Machine (Remote Execution)

```bash
# Single command deployment from local machine
ssh root@srv1241381.hstgr.cloud 'bash -s' < vps_deploy_f11.sh

# Or pipe to tee for local copy
ssh root@srv1241381.hstgr.cloud 'bash -s' < vps_deploy_f11.sh | tee vps_deployment_log.txt
```

---

## Rollback Procedure (If Issues)

```bash
# Emergency rollback
ssh root@srv1241381.hstgr.cloud
cd /app/techno-os-backend

# Option A: Rollback to main
git checkout main
docker compose restart api

# Option B: Rollback to specific commit
git checkout f41afc2  # Last stable before F11
docker compose restart api

# Verify
curl -fsS http://localhost:8000/health
docker compose logs --tail=20 api
```

---

## Evidence Validation Checklist

After deployment, verify evidence package contains:

- [ ] `deployed_commit.txt` shows `F11-SEALED-v1.0` tag
- [ ] `smoke_test_output.txt` shows 8/8 tests passed
- [ ] `audit_analysis.txt` shows G8 >= 2, G10 >= 1
- [ ] `audit_sample.jsonl` has UUID format trace_ids
- [ ] `health_response.json` shows `{"status":"ok"}`
- [ ] `container_status.txt` shows containers running
- [ ] No errors in `deployment.log`

---

## Success Criteria

✅ **CP-11.3 Approved if**:
- All smoke tests pass (8/8)
- Audit log shows G8_UNKNOWN_ACTION for 404/405
- Audit log shows G10_BODY_PARSE_ERROR for malformed JSON
- Trace IDs are valid UUIDs
- No service disruption during deployment
- Zero errors in audit log analysis

❌ **Rollback immediately if**:
- Health check fails after 30s
- Smoke tests fail (any of 8)
- Docker containers fail to start
- Critical errors in deployment.log
- Audit log shows unexpected patterns

---

## Contact & Support

**Deployment Window**: Off-peak hours recommended  
**Estimated Duration**: 5-10 minutes (automated), 15-20 minutes (manual)  
**Monitoring**: Check audit.log for 1 hour post-deployment

**Next Steps After CP-11.3**:
1. Review evidence package
2. Approve CP-11.3 formally
3. Update production documentation
4. Schedule merge to main branch

---

**Prepared**: 2026-01-04  
**Branch**: stage/f11-gate-consolidation  
**Tag**: F11-SEALED-v1.0  
**Commit**: 7f45671 (functional) / a16ffdd (with deployment script)
