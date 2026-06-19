# Deployment Guide

## Prerequisites

- Docker Desktop ≥ 4.x or Docker Engine ≥ 24.x
- Docker Compose v2
- A Google Gemini API key (obtain from [Google AI Studio](https://aistudio.google.com/))
- A server with at least 2 vCPUs and 4 GB RAM for the full stack

---

## Quick Start (Local Development)

```bash
# 1. Clone the repository
git clone <repo-url>
cd customer-success-platform

# 2. Configure environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit backend/.env — set at minimum:
# SECRET_KEY=<random 32+ char string>
# GEMINI_API_KEY=<your key>

# 3. Start all services
docker compose up --build -d

# 4. Run database migrations
docker compose exec backend alembic upgrade head

# 5. Verify
curl http://localhost:8000/api/v1/health
open http://localhost:3000
```

---

## Production Deployment (Docker Compose)

### 1. Prepare the server

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Clone the repository
git clone <repo-url> /opt/csp
cd /opt/csp
```

### 2. Configure production environment

```bash
cp .env.example .env
# Edit .env:
#   POSTGRES_PASSWORD=<strong-random-password>
#   REDIS_PASSWORD=<strong-random-password>

cp backend/.env.example backend/.env
# Edit backend/.env:
#   SECRET_KEY=<openssl rand -hex 32>
#   GEMINI_API_KEY=<your-key>
#   ENVIRONMENT=production
#   ALLOWED_ORIGINS=["https://yourdomain.com"]
```

### 3. Set up data directories

```bash
sudo mkdir -p /var/lib/csp/postgres /var/lib/csp/redis
sudo chown 999:999 /var/lib/csp/postgres   # postgres uid
sudo chown 999:999 /var/lib/csp/redis      # redis uid
```

Update `.env` with:
```
POSTGRES_DATA_PATH=/var/lib/csp/postgres
REDIS_DATA_PATH=/var/lib/csp/redis
```

### 4. TLS certificate

```bash
# Option A: Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem deployment/nginx/certs/server.crt
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem   deployment/nginx/certs/server.key

# Option B: Self-signed (development/testing only)
mkdir -p deployment/nginx/certs
openssl req -x509 -newkey rsa:4096 -keyout deployment/nginx/certs/server.key \
  -out deployment/nginx/certs/server.crt -days 365 -nodes \
  -subj "/CN=localhost"
```

### 5. Build and start

```bash
# Build images
docker compose -f deployment/docker-compose.production.yml build

# Start in detached mode
docker compose -f deployment/docker-compose.production.yml up -d

# Run migrations
docker compose -f deployment/docker-compose.production.yml exec backend alembic upgrade head

# Verify
curl https://yourdomain.com/api/v1/health
```

---

## Cloud Deployment Options

### Option A: AWS (ECS + RDS + ElastiCache)

**Architecture:**
- ECS Fargate tasks for backend and frontend (no server management)
- RDS PostgreSQL 16 (Multi-AZ for HA)
- ElastiCache Redis (cluster mode disabled, single node for cost savings initially)
- Application Load Balancer (HTTPS termination, health checks)
- ECR for container images
- Secrets Manager for environment variables

**Pros:** Mature ecosystem, fine-grained IAM, managed RDS backups, auto-scaling
**Cons:** Complex setup, higher cost at small scale, vendor lock-in

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t csp-backend ./backend --target production
docker tag csp-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/csp-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/csp-backend:latest
```

**Estimated cost (us-east-1, moderate traffic):** ~$120–250/month

---

### Option B: Azure (Container Apps + Azure Database)

**Architecture:**
- Azure Container Apps for backend and frontend (serverless containers with autoscale to 0)
- Azure Database for PostgreSQL — Flexible Server
- Azure Cache for Redis
- Azure Container Registry
- Application Gateway or Azure Front Door for HTTPS

**Pros:** Container Apps scale to zero (cost-effective for low traffic), integrated AD auth
**Cons:** Container Apps has cold-start latency, less community documentation than ECS

**Estimated cost:** ~$80–200/month depending on traffic

---

### Option C: DigitalOcean (Recommended for simplicity)

**Architecture:**
- DigitalOcean Droplet (2 vCPU / 4 GB, ~$24/month) running Docker Compose
- Managed PostgreSQL cluster ($15/month for 1 GB)
- Managed Redis ($15/month for 1 GB)
- DigitalOcean Spaces for backups

**Pros:** Simple, predictable pricing, good documentation, Docker Compose works directly
**Cons:** Manual scaling, no auto-scaling without additional tooling

```bash
# On the Droplet, after git clone and .env setup:
docker compose -f deployment/docker-compose.production.yml up -d

# Use managed DB/Redis — update backend/.env:
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:25060/defaultdb?ssl=require
REDIS_URL=rediss://:password@redis-host:25061/0
```

**Estimated cost:** ~$55–80/month

---

## Environment Variable Reference

See `backend/.env.example` and `frontend/.env.example` for full documentation.

**Critical production variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (min 32 chars) | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Database password | strong random string |
| `REDIS_PASSWORD` | Redis auth password | strong random string |
| `GEMINI_API_KEY` | Google AI API key | from AI Studio |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["https://yourdomain.com"]` |
| `ENVIRONMENT` | Must be `production` | `production` |

---

## Health Check URLs

After deployment, verify all three:

| URL | Expected Response |
|-----|-------------------|
| `/api/v1/liveness` | `{"alive": true}` |
| `/api/v1/readiness` | `{"ready": true}` |
| `/api/v1/health` | `{"status": "healthy", ...}` |

A `degraded` status from `/health` means at least one upstream service (DB or Redis) is unreachable.

---

## Database Migrations in Production

Always run migrations before starting the new application version:

```bash
# Zero-downtime approach:
# 1. Deploy new backend image (old still running)
# 2. Run migrations (new image runs alembic)
docker compose exec backend alembic upgrade head

# 3. Restart backend to pick up new code
docker compose restart backend
```

Never run migrations while the old backend version is receiving traffic if the migration is not backward-compatible.

---

## Backup and Recovery

### Manual backup
```bash
docker compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB \
  | gzip > backup-$(date +%Y%m%d-%H%M).sql.gz
```

### Restore
```bash
gunzip < backup-20260101-1200.sql.gz \
  | docker compose exec -T postgres psql -U $POSTGRES_USER $POSTGRES_DB
```

### Automated backups
See `scripts/backup.sh` for a cron-ready backup script.
