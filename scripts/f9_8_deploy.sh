#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TECHNO OS — PRODUCTION DEPLOYMENT SCRIPT (F9.8+)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Modo: Fail-Closed · Evidence-Based · Non-Interactive
# Compatível com: F9.8A (SSH key + sudo -n + docker group)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURAÇÃO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

readonly VPS_HOST="${VPS_HOST:-techno-os}"  # SSH alias (após F9.8A)
readonly VPS_USER="${VPS_USER:-deploy}"
readonly VPS_IP="${VPS_IP:-72.61.219.157}"

readonly REMOTE_APP_DIR="/opt/techno-os/app/backend"
readonly REMOTE_COMPOSE_FILE="${REMOTE_APP_DIR}/docker-compose.prod.yml"
readonly LOCAL_WORKSPACE="${LOCAL_WORKSPACE:-$(pwd)}"

readonly ARTIFACT_BASE="/opt/techno-os/artifacts"
readonly DEPLOY_TS="$(date -u +%Y%m%d_%H%M%S)"
readonly ARTIFACT_DIR="${ARTIFACT_BASE}/deploy_${DEPLOY_TS}"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNÇÕES DE LOG E FAIL-CLOSED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date -Iseconds) $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date -Iseconds) $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date -Iseconds) $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date -Iseconds) $*" >&2
}

die() {
    log_error "ABORT: $*"
    log_error "Deployment failed at $(date -Iseconds)"
    log_error "Check logs in: ${ARTIFACT_DIR:-/opt/techno-os/artifacts/}"
    exit 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNÇÕES DE SSH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ssh_exec() {
    # Usa SSH alias se disponível (após F9.8A), senão usa user@ip
    if ssh -G "$VPS_HOST" &>/dev/null; then
        ssh "$VPS_HOST" "$@"
    else
        ssh "${VPS_USER}@${VPS_IP}" "$@"
    fi
}

ssh_sudo() {
    # Executa comando com sudo -n (non-interactive, requer F9.8A sudoers)
    ssh_exec "sudo -n $*"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VALIDAÇÕES PRÉ-DEPLOYMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

validate_ssh_connection() {
    log_info "Validating SSH connection to ${VPS_HOST}..."
    
    if ! ssh_exec "echo SSH_OK" &>/dev/null; then
        die "SSH connection failed. Check: 1) SSH key configured, 2) Host reachable"
    fi
    
    log_success "SSH connection OK"
}

validate_sudo_nopasswd() {
    log_info "Validating sudo non-interactive (F9.8A requirement)..."
    
    if ! ssh_exec "sudo -n true" &>/dev/null; then
        log_warn "sudo -n failed. F9.8A not applied yet?"
        log_warn "Deployment will request password for sudo commands."
        log_warn "Run F9.8A first for passwordless automation."
    else
        log_success "sudo non-interactive OK"
    fi
}

validate_docker_permission() {
    log_info "Validating docker permission (no sudo required)..."
    
    if ! ssh_exec "docker ps" &>/dev/null; then
        die "docker ps failed. User ${VPS_USER} not in docker group? Run F9.8A first."
    fi
    
    log_success "Docker permission OK (no sudo)"
}

validate_local_workspace() {
    log_info "Validating local workspace..."
    
    if [ ! -f "${LOCAL_WORKSPACE}/app/main.py" ]; then
        die "app/main.py not found in ${LOCAL_WORKSPACE}. Wrong directory?"
    fi
    
    if [ ! -f "${LOCAL_WORKSPACE}/docker-compose.prod.yml" ]; then
        die "docker-compose.prod.yml not found. Required for deployment."
    fi
    
    log_success "Local workspace OK"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNÇÕES DE EVIDÊNCIA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

setup_artifacts() {
    log_info "Setting up artifact directory: ${ARTIFACT_DIR}"
    
    ssh_exec "mkdir -p ${ARTIFACT_DIR}" || die "Failed to create artifact dir"
    ssh_exec "echo '${DEPLOY_TS}' > ${ARTIFACT_DIR}/timestamp.txt"
    ssh_exec "echo \$(git rev-parse HEAD 2>/dev/null || echo 'NO_GIT') > ${ARTIFACT_DIR}/commit.txt" || true
    
    log_success "Artifacts directory ready"
}

collect_pre_deployment_evidence() {
    log_info "Collecting pre-deployment evidence..."
    
    ssh_exec "docker ps --filter 'name=techno' --format '{{.Names}}\t{{.Status}}' > ${ARTIFACT_DIR}/containers_pre.txt" || true
    ssh_exec "docker images --filter 'reference=techno-os-*' --format '{{.Repository}}:{{.Tag}}\t{{.ID}}' > ${ARTIFACT_DIR}/images_pre.txt" || true
    ssh_exec "curl -sf http://127.0.0.1:8000/health > ${ARTIFACT_DIR}/health_pre.txt 2>&1" || echo "API_DOWN" | ssh_exec "tee ${ARTIFACT_DIR}/health_pre.txt" >/dev/null
    
    log_success "Pre-deployment evidence collected"
}

collect_post_deployment_evidence() {
    log_info "Collecting post-deployment evidence..."
    
    ssh_exec "docker ps --filter 'name=techno' --format '{{.Names}}\t{{.Status}}' > ${ARTIFACT_DIR}/containers_post.txt"
    ssh_exec "docker images --filter 'reference=techno-os-*' --format '{{.Repository}}:{{.Tag}}\t{{.ID}}' > ${ARTIFACT_DIR}/images_post.txt"
    ssh_exec "docker logs --tail 50 techno-os-api > ${ARTIFACT_DIR}/api_logs_post.txt 2>&1" || true
    
    log_success "Post-deployment evidence collected"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNÇÕES DE BUILD E DEPLOY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

get_current_image_tag() {
    # Retorna tag da imagem atualmente em execução
    ssh_exec "docker inspect techno-os-api --format '{{.Config.Image}}' 2>/dev/null | cut -d: -f2" || echo "unknown"
}

sync_code_to_vps() {
    log_info "Syncing code to VPS..."
    
    # Rsync apenas arquivos necessários (exclui node_modules, .git, etc)
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='venv' \
        --exclude='artifacts' \
        --exclude='*.log' \
        "${LOCAL_WORKSPACE}/" "${VPS_USER}@${VPS_IP}:${REMOTE_APP_DIR}/" \
        || die "Code sync failed"
    
    log_success "Code synced to VPS"
}

build_docker_image() {
    log_info "Building Docker image on VPS..."
    
    local git_hash
    git_hash=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")
    local image_tag="techno-os-api:${git_hash}"
    
    ssh_exec "cd ${REMOTE_APP_DIR} && docker build -t ${image_tag} -f Dockerfile . > ${ARTIFACT_DIR}/build.log 2>&1" \
        || die "Docker build failed. Check ${ARTIFACT_DIR}/build.log"
    
    # Tag como latest também
    ssh_exec "docker tag ${image_tag} techno-os-api:latest"
    
    log_success "Docker image built: ${image_tag}"
    echo "$image_tag" | ssh_exec "tee ${ARTIFACT_DIR}/new_image.txt" >/dev/null
}

deploy_containers() {
    log_info "Deploying containers with docker-compose..."
    
    local previous_image
    previous_image=$(get_current_image_tag)
    echo "$previous_image" | ssh_exec "tee ${ARTIFACT_DIR}/previous_image.txt" >/dev/null
    
    # Pull images (se houver registry externo)
    # ssh_exec "cd ${REMOTE_APP_DIR} && docker-compose -f ${REMOTE_COMPOSE_FILE} pull" || true
    
    # Up com recreate (zero downtime se health checks configurados)
    ssh_exec "cd ${REMOTE_APP_DIR} && docker-compose -f docker-compose.prod.yml up -d --remove-orphans > ${ARTIFACT_DIR}/compose_up.log 2>&1" \
        || die "docker-compose up failed. Check ${ARTIFACT_DIR}/compose_up.log"
    
    log_success "Containers deployed"
}

reload_nginx() {
    log_info "Reloading Nginx configuration..."
    
    # Testa config antes de reload
    if ! ssh_sudo "nginx -t" &>/dev/null; then
        log_warn "nginx -t failed. Skipping reload."
        return 1
    fi
    
    ssh_sudo "systemctl reload nginx" || die "nginx reload failed"
    
    log_success "Nginx reloaded"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VALIDAÇÕES PÓS-DEPLOYMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

wait_for_health() {
    log_info "Waiting for API health check..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if ssh_exec "curl -sf http://127.0.0.1:8000/health" &>/dev/null; then
            log_success "API is healthy"
            ssh_exec "curl -s http://127.0.0.1:8000/health > ${ARTIFACT_DIR}/health_post.txt"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Health check attempt ${attempt}/${max_attempts}..."
        sleep 2
    done
    
    die "API failed to become healthy after ${max_attempts} attempts"
}

validate_metrics_endpoint() {
    log_info "Validating /metrics endpoint (Prometheus scrape)..."
    
    if ssh_exec "curl -sf http://127.0.0.1:8000/metrics | head -5" &>/dev/null; then
        log_success "/metrics endpoint OK"
        ssh_exec "curl -s http://127.0.0.1:8000/metrics > ${ARTIFACT_DIR}/metrics_post.txt"
    else
        log_warn "/metrics endpoint not responding (non-critical)"
    fi
}

validate_containers_running() {
    log_info "Validating all containers are running..."
    
    local expected_containers=("techno-os-api" "techno-os-db" "techno-os-prometheus" "techno-os-grafana")
    local missing_containers=()
    
    for container in "${expected_containers[@]}"; do
        if ! ssh_exec "docker ps --filter name=${container} --filter status=running --format '{{.Names}}'" | grep -q "$container"; then
            missing_containers+=("$container")
        fi
    done
    
    if [ ${#missing_containers[@]} -gt 0 ]; then
        log_error "Missing containers: ${missing_containers[*]}"
        die "Not all containers are running"
    fi
    
    log_success "All expected containers running"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN DEPLOYMENT FLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

main() {
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TECHNO OS — PRODUCTION DEPLOYMENT"
    log_info "Timestamp: ${DEPLOY_TS}"
    log_info "Target: ${VPS_HOST} (${VPS_IP})"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # PRE-FLIGHT
    log_info "PHASE 1: Pre-flight checks"
    validate_local_workspace
    validate_ssh_connection
    validate_sudo_nopasswd
    validate_docker_permission
    
    # SETUP
    log_info "PHASE 2: Setup"
    setup_artifacts
    collect_pre_deployment_evidence
    
    # BUILD & DEPLOY
    log_info "PHASE 3: Build & Deploy"
    sync_code_to_vps
    build_docker_image
    deploy_containers
    
    # POST-DEPLOYMENT
    log_info "PHASE 4: Post-deployment validation"
    wait_for_health
    validate_containers_running
    validate_metrics_endpoint
    collect_post_deployment_evidence
    
    # OPTIONAL: Nginx reload (se houver mudanças de config)
    # reload_nginx
    
    # FINAL REPORT
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_success "DEPLOYMENT SUCCESSFUL"
    log_info "Artifacts: ${ARTIFACT_DIR}"
    log_info "New image: $(ssh_exec "cat ${ARTIFACT_DIR}/new_image.txt")"
    log_info "Previous image: $(ssh_exec "cat ${ARTIFACT_DIR}/previous_image.txt")"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    log_info "To rollback: docker tag <previous_image> techno-os-api:latest && docker-compose up -d"
    log_info "To view logs: ssh ${VPS_HOST} 'docker logs -f techno-os-api'"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
