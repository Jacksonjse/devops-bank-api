# Bank Transaction API — DevOps Project

A REST API for banking operations (create account, deposit, withdraw, balance check) with full DevOps pipeline.

## Tech Stack
- **App**: Python Flask + SQLite
- **CI/CD**: GitHub Actions (build → test → deploy)
- **Container**: Docker + Docker Compose
- **Orchestration**: Kubernetes (Minikube)
- **IaC**: Ansible

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/account` | Create new account |
| POST | `/deposit` | Deposit money |
| POST | `/withdraw` | Withdraw money |
| GET | `/balance/<account_id>` | Get balance |
| GET | `/health` | Health check |

## Quick Start

```bash
# Run locally
pip install -r requirements.txt
python app.py

# Run with Docker
docker-compose up --build

# Run tests
pytest tests/ -v
```

## Fraud Detection
Transactions above ₹50,000 are automatically flagged with a warning in the response.
