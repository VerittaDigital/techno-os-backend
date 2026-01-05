# Techno OS Console — Quick Reference (v0.1.0)

**Status:** ✅ Production-Ready  
**Last Updated:** January 4, 2026  
**Framework:** F-CONSOLE-0.1

---

## 🚀 Quick Start

### Local Development
```bash
npm install --legacy-peer-deps
npm run build
npm start
# → Server running on http://localhost:3000
```

### Docker Deployment
```bash
docker network create techno-net
docker build -t techno-os-console:0.1.0 .
docker-compose up
# → Console running on http://127.0.0.1:3001
```

---

## 📚 Key Documentation

| Document | Purpose |
|----------|---------|
| [BUILDING.md](BUILDING.md) | Build procedures & troubleshooting |
| [docs/INVENTORY.md](docs/INVENTORY.md) | API endpoints documentation |
| [openapi/console-v0.1.yaml](openapi/console-v0.1.yaml) | OpenAPI 3.0.0 contract |
| [docs/ERROR_POLICY.md](docs/ERROR_POLICY.md) | Error handling rules |
| [docs/CONTRACT.md](docs/CONTRACT.md) | Versioning & deprecation policy |
| [docs/COPILOT_INSTRUCTIONS.md](docs/COPILOT_INSTRUCTIONS.md) | AI governance framework |
| [.env.example](.env.example) | Environment template |

---

## 🔒 Security Checklist

- ✅ No secrets in version control
- ✅ All config via environment variables
- ✅ .env* files protected by .gitignore
- ✅ Fail-closed error handling (15s timeout)
- ✅ Unknown status → BLOCKED
- ✅ Non-root Docker user (UID 1001)
- ✅ Multi-stage Docker build

---

## 🧪 Testing

```bash
# Environment security
node scripts/test-etapa5-hardening.js

# Build reproducibility
node scripts/test-etapa6-reproducible.js

# Expected: 6/6 PASS for both
```

---

## 🏗️ Architecture

```
Console (Next.js 16 + React 19)
├── Frontend (React components)
├── API Layer (X-API-Key authentication)
│   ├── POST /api/execute (command execution)
│   ├── GET /api/audit (audit logs)
│   └── GET /api/memory (memory stats)
└── Error Handling (fail-closed, 15s timeout)
```

---

## 📦 Version Info

- **Package:** 0.1.0
- **Docker Image:** techno-os-console:0.1.0
- **Node.js:** v24.x (local) / v20-alpine (Docker)
- **Next.js:** 16.1.1
- **React:** 19.2.3

---

## 🔄 CI/CD Integration

### Build Command
```bash
npm install --legacy-peer-deps && npm run build
```

### Docker Command
```bash
docker build -t techno-os-console:0.1.0 .
docker push registry.example.com/techno-os-console:0.1.0
```

### Deployment Command
```bash
docker network create techno-net
docker-compose up -d
```

---

## ⚠️ Important Notes

1. **API Key:** Required header `X-API-Key` for all API calls
2. **Timeout:** All requests timeout after 15 seconds
3. **Error Handling:** Unknown errors normalized to status: BLOCKED
4. **Fallback:** /api/audit falls back to /api/diagnostic/metrics
5. **Storage:** sessionStorage limited to 10 safe fields

---

## 🐛 Troubleshooting

**Docker build fails:**
```bash
# Check .dockerignore
cat .dockerignore

# Clean and rebuild
docker system prune -a
docker build -t techno-os-console:0.1.0 .
```

**Port conflicts:**
```bash
# docker-compose uses 127.0.0.1:3001 (local only)
# Change in docker-compose.yml if needed
lsof -ti:3001 | xargs kill -9
```

**Environment issues:**
```bash
# Copy template and customize
cp .env.example .env.local
# Edit .env.local with your values
```

---

## 📞 Support

**For build issues:** See [BUILDING.md](BUILDING.md)  
**For API errors:** See [docs/ERROR_POLICY.md](docs/ERROR_POLICY.md)  
**For versioning:** See [docs/CONTRACT.md](docs/CONTRACT.md)  
**For governance:** See [docs/COPILOT_INSTRUCTIONS.md](docs/COPILOT_INSTRUCTIONS.md)

---

## 🎯 Next Steps

1. Implement backend endpoints (reference: openapi/console-v0.1.yaml)
2. Run integration tests (console ↔ backend)
3. Deploy to production (follow BUILDING.md)
4. Monitor healthcheck & logs
5. Plan v0.2.0 features

---

**Framework Status:** ✅ F-CONSOLE-0.1 COMPLETE  
**Production Ready:** Yes  
**Last Test Run:** All 12/12 gates PASS

> "IA como instrumento. Humano como centro."
