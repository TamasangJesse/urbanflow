# UrbanFlow

Crowd-Powered Traffic Prediction and Mobility Intelligence Platform

A microservices-based urban mobility platform designed to help commuters anticipate congestion before starting their journeys. Built for cities with limited traffic infrastructure data, particularly Yaoundé and Douala.

## Architecture

- **API Gateway** – single entry point, routing, authentication
- **User Service** – registration, auth, profiles, saved routes
- **Mobility Intelligence Service** – traffic data, ML prediction (Random Forest), route recommendations
- **Notification Service** – real-time alerts via Redis Streams events

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI |
| Frontend | React |
| Database | PostgreSQL |
| Event Broker | Redis Streams |
| ML | Scikit-learn (Random Forest Regressor) |
| Containers | Docker |
| Orchestration | Kubernetes (K3s) |
| CI/CD | Jenkins |
| Monitoring | Prometheus + Grafana + Alertmanager |
| IaC | Terraform + Ansible |

## Getting Started

```bash
cp .env.example .env
# Fill in your values, then:
docker-compose up
```

## Project Structure

