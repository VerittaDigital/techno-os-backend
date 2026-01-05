# HOTFIX REMOTE-SSH DOCKER RUNBOOK

## Recommended VSCode Extensions
- Remote-SSH
- Docker
- Dev Containers

## SSH Config Snippet
```
Host veritta-vps
    HostName <VPS_IP>
    User deploy
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
```

## Attaching VSCode to Remote
1. Open VSCode, install Remote-SSH extension.
2. Cmd+Shift+P > Remote-SSH: Connect to Host > veritta-vps
3. Open folder /opt/techno-os/app/backend
4. For container logs: Use Docker extension to attach to techno-os-api container.

## Inspecting Compose Services and Logs
- `docker-compose ps` to list services.
- `docker-compose logs -f api` to follow api logs.
- `docker exec -it techno-os-api /bin/bash` for shell access (safe, no secrets).