#!/bin/bash
# F9.6.0 Post-GO Hardening Script with DRY_RUN support

set -euo pipefail

cd /mnt/d/Projects/techno-os-backend
ART_DIR="artifacts/f9_6_0_post_go"
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ART_DIR"

: "${DRY_RUN:=0}"
: "${PUSH_TAG:=0}"

echo "TS=$TS" | tee "$ART_DIR/meta_${TS}.txt"
echo "PWD=$(pwd)" | tee -a "$ART_DIR/meta_${TS}.txt"
echo "BRANCH=$(git rev-parse --abbrev-ref HEAD)" | tee -a "$ART_DIR/meta_${TS}.txt"
echo "HEAD=$(git rev-parse HEAD)" | tee -a "$ART_DIR/meta_${TS}.txt"

git status --porcelain | tee "$ART_DIR/git_status_pre_${TS}.txt"

REQ_FILES=(
  "docker-compose.yml"
  "docker-compose.edge.yml"
  ".gitignore"
)
MISSING=0
for f in "${REQ_FILES[@]}"; do
  test -f "$f" && echo "OK  $f" || { echo "MISS $f"; MISSING=1; }
done | tee "$ART_DIR/required_files_${TS}.txt"
[ "$MISSING" -eq 0 ] || { echo "ABORT: arquivos obrigatórios ausentes"; exit 1; }

# Create evidence policy doc (if not exists)
if [ ! -f docs/evidence_policy.md ]; then
  mkdir -p docs
  cat > docs/evidence_policy.md << 'EOP'
# Evidence Policy

## Canonical Light Evidence
- Files committed to git: policies, scripts, configs that define the system.
- Examples: docker-compose.yml, scripts/, docs/, .gitignore updates.

## Heavy Artifacts
- Runtime evidences: logs, probes, checksums, reports generated during execution.
- Ignored in .gitignore under artifacts/

## Storage and Retention for Heavy Artifacts
- Heavy artifacts devem ser armazenados em storage externo ou CI artifacts (ex.: GitHub Actions artifacts, S3, ou similar).
- Prazo de retenção: 30 dias ou conforme política de compliance/auditoria.
- Regeneráveis via scripts; não versionar para manter repo enxuto.

## PII and Redaction (LGPD Compliance)
- Jamais commitar dados pessoais, tokens, dumps sensíveis ou informações identificáveis.
- Redigir logs e reports: substituir PII por placeholders (ex.: [REDACTED]).
- Verificar antes de commit: scripts devem evitar exposição acidental.

## Naming Standards for Artifacts and Reports
- Padrão: artifacts/{phase}/{type}_{timestamp}.{ext}
- Exemplos: artifacts/f9_6_0_post_go/FINAL_REPORT_20260101_191232.md
- Facilita auditoria e organização cronológica.

## Rationale
- Keep repo lean for CI/CD.
- Heavy artifacts can be regenerated or stored externally if needed.
- Enterprise-grade governance para compliance e auditabilidade.
EOP
  echo "Created docs/evidence_policy.md" | tee "$ART_DIR/evidence_policy_create_${TS}.txt"
else
  echo "docs/evidence_policy.md already exists" | tee "$ART_DIR/evidence_policy_create_${TS}.txt"
fi

# Update .gitignore
if ! grep -q "Evidence Policy" .gitignore; then
  cat >> .gitignore << 'EOG'
# Evidence Policy: ignore heavy artifacts
artifacts/
EOG
  echo "Updated .gitignore with evidence policy" | tee "$ART_DIR/gitignore_update_${TS}.txt"
else
  echo ".gitignore already has evidence policy" | tee "$ART_DIR/gitignore_update_${TS}.txt"
fi

if [ "$DRY_RUN" -eq 0 ]; then
  # Add and commit changes
  git add docs/evidence_policy.md .gitignore
  git commit -m "F9.6.0: Implement evidence policy for lean git

- Add docs/evidence_policy.md defining canonical light vs heavy evidence
- Update .gitignore to ignore artifacts/ for heavy runtime evidences
- Ensures repo hygiene for CI/CD pipelines" 2>&1 | tee "$ART_DIR/git_commit_${TS}.txt"

  # Create tag
  TAG_NAME="v0.1.0-f9.6.0"
  git tag -a "$TAG_NAME" -m "F9.6.0 Post-GO Hardening Release

- Evidence policy implemented
- Repo hygiene ensured
- Ready for production deployment" 2>&1 | tee "$ART_DIR/git_tag_${TS}.txt"

  if [ "$PUSH_TAG" -eq 1 ]; then
    git push origin "$TAG_NAME" 2>&1 | tee "$ART_DIR/git_push_tag_${TS}.txt"
  fi
else
  echo "DRY_RUN=1: Skipping commit and tag creation" | tee "$ART_DIR/dry_run_skip_${TS}.txt"
fi

git status --porcelain | tee "$ART_DIR/git_status_post_${TS}.txt"

# Generate evidence
if [ "$DRY_RUN" -eq 0 ]; then
  git show --stat "$TAG_NAME" | tee "$ART_DIR/tag_show_${TS}.txt"
  git diff HEAD~1 | tee "$ART_DIR/commit_diff_${TS}.txt"
else
  echo "DRY_RUN: No tag to show" | tee "$ART_DIR/tag_show_${TS}.txt"
  echo "DRY_RUN: No diff to show" | tee "$ART_DIR/commit_diff_${TS}.txt"
fi

find "$ART_DIR" -type f -maxdepth 1 -print0 | xargs -0 sha256sum | tee "$ART_DIR/SHA256SUMS_${TS}.txt"

DIRTY_POST="$(cat "$ART_DIR/git_status_post_${TS}.txt")"

VERDICT="GO"
[ -z "$DIRTY_POST" ] || VERDICT="NO-GO"

{
  echo "# F9.6.0 — POST-GO HARDENING — FINAL REPORT"
  echo
  echo "TS: $TS"
  echo "BRANCH: $(cat "$ART_DIR/meta_${TS}.txt" | grep BRANCH | cut -d= -f2)"
  echo "HEAD: $(cat "$ART_DIR/meta_${TS}.txt" | grep HEAD | cut -d= -f2)"
  echo "TAG: ${TAG_NAME:-N/A (DRY_RUN)}"
  echo "DRY_RUN: $DRY_RUN"
  echo "PUSH_TAG: $PUSH_TAG"
  echo
  echo "## CHANGES"
  echo "- Created/Updated docs/evidence_policy.md"
  echo "- Updated .gitignore with artifacts/ ignore"
  if [ "$DRY_RUN" -eq 0 ]; then
    echo "- Committed changes"
    echo "- Created tag $TAG_NAME"
  else
    echo "- DRY_RUN: No commit/tag"
  fi
  echo
  echo "## WORKTREE POLICY"
  echo "dirty_post:"
  echo "$DIRTY_POST"
  echo
  echo "## VERDICT"
  echo "$VERDICT"
  echo
  echo "## POINTERS"
  echo "Full evidence folder: $ART_DIR/"
} | tee "$ART_DIR/FINAL_REPORT_${TS}.md"

echo "$VERDICT"