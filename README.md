# Complaint / Service Request Management System

A college-ready microservices project implementing the requirements:

- User Service
- Complaint Service
- Assignment Service
- Notification Service
- Authentication Service with JWT
- REST communication between services
- API Gateway
- Docker / Docker Compose
- Kubernetes manifests
- GitHub Actions CI/CD
- ELK centralized logging (Elasticsearch + Logstash + Kibana)

## Architecture

Client -> API Gateway -> Auth / User / Complaint / Assignment / Notification services

The gateway validates JWT tokens and forwards `X-User-Id` and `X-User-Role` headers. Internal service-to-service calls use the `INTERNAL_API_KEY`.

## Requirements

- Docker Desktop
- Docker Compose
- Optional: kubectl + Docker Desktop Kubernetes / Minikube
- Optional for CI/CD: GitHub repository

## Quick start with Docker Compose

```bash
docker compose up --build
```

Then open:
- Gateway health: http://localhost:8000/health
- Swagger: http://localhost:8000/docs
- Kibana: http://localhost:5601

## Demo accounts

Admin:
- email: admin@example.com
- password: Admin@123

Normal user:
- email: user@example.com
- password: User@123

## Main API flow

1. `POST /api/auth/login` -> receive JWT.
2. Use JWT as `Authorization: Bearer <token>`.
3. User creates complaint: `POST /api/complaints`.
4. Admin lists complaints: `GET /api/complaints`.
5. Admin assigns complaint: `POST /api/assignments`.
6. Assigned employee/admin changes status using `PATCH /api/complaints/{id}/status`.
7. User tracks complaint with `GET /api/complaints/{id}`.
8. Notifications are generated for complaint creation, assignment and status changes.

## Sample requests

### Login
```json
{
  "email": "admin@example.com",
  "password": "Admin@123"
}
```

### Create complaint
```json
{
  "title": "Water leakage",
  "description": "Water is leaking near the main entrance",
  "category": "Maintenance"
}
```

### Assign complaint
```json
{
  "complaint_id": 1,
  "assignee_id": 2,
  "note": "Please inspect and resolve"
}
```

### Update status
```json
{
  "status": "IN_PROGRESS"
}
```

Allowed statuses: `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, `REJECTED`.

## Kubernetes

```bash
kubectl apply -f k8s/
kubectl get pods
kubectl get svc
```

For a local Docker Desktop Kubernetes cluster, the gateway is exposed as NodePort `30080`.

## CI/CD

`.github/workflows/ci-cd.yml` runs Python compilation checks and builds all Docker images. Add Docker Hub credentials as GitHub secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` to push images.

## ELK

Services print structured JSON logs to stdout and also attempt to send logs to Logstash. Logstash listens on TCP port 5000. Elasticsearch stores logs and Kibana provides visualization at port 5601.


## Web Frontend

The responsive browser interface is included in `frontend/` and served by the API gateway.
After starting the stack with `docker compose up --build -d`, open **http://localhost:8000/**.
Use the demo accounts listed above to sign in. The UI supports registration, complaint creation and tracking, notifications, and an admin desk for assignment/status updates.
