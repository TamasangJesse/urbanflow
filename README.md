# UrbanFlow

Crowd-Powered Traffic Prediction and Mobility Intelligence Platform

A microservices-based urban mobility platform designed to help commuters anticipate congestion before starting their journeys. Built for cities with limited traffic infrastructure data, particularly Yaounde and Douala.

## Architecture

- **API Gateway** - single entry point, routing, authentication
- **User Service** - registration, auth, profiles, saved routes
- **Mobility Intelligence Service** - traffic data, ML prediction (Random Forest), route recommendations
- **Notification Service** - real-time alerts via Redis Streams events

## Tech Stack

| Layer | Technology |
|-------|------------|
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

Copy the environment file and fill in your values:

    cp .env.example .env

Then start the stack:

    docker-compose up

## Project Structure

    urbanflow/
    ├── services/           Microservices (api-gateway, user, mobility, notification)
    ├── infrastructure/     Terraform + Ansible
    ├── kubernetes/         K8s deployment manifests
    ├── monitoring/         Prometheus + Grafana configs
    ├── ci-cd/              Jenkinsfile
    ├── frontend/           React app
    ├── scripts/            Dataset generation, model training utilities
    └── docs/               Architecture diagrams, design docs

## Team

| Name | Role |
|------|------|
| Jesse Francis | Scrum Master / Developer |
| Chelsie | Product Owner / Developer |

## Course

SEN3244 - Software Architecture, ICT University
