# Project report / viva guide

## Title
Complaint / Service Request Management System using Microservices

## Problem statement
Users need a single platform to register service complaints, track status and receive updates. Administrators need to manage, assign and update complaints. The system is divided into independent services so each business capability can be developed and deployed separately.

## Objectives
1. Secure user registration and login using JWT.
2. Provide complaint registration and tracking.
3. Allow administrators to assign complaints.
4. Provide notifications for important events.
5. Expose a single API Gateway to clients.
6. Containerize the system with Docker.
7. Provide Kubernetes deployment manifests.
8. Provide CI/CD automation with GitHub Actions.
9. Centralize application logs using ELK.

## Service responsibilities
- Authentication Service: registration, login, JWT generation and validation.
- User Service: user profile data and admin user listing.
- Complaint Service: complaint CRUD/tracking, assignment and status lifecycle.
- Assignment Service: assignment records and orchestration of complaint assignment.
- Notification Service: notification creation and user notification inbox.
- API Gateway: one entry point, routing and JWT authentication.

## Status lifecycle
OPEN -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
Other terminal/review state: REJECTED.

## Why microservices?
Each service has a focused responsibility, can be scaled independently and communicates using REST. Failure or change in one business capability is less likely to require changes to the whole application.

## Security
JWT is used for authentication. Passwords are stored as salted PBKDF2-SHA256 hashes, not plaintext. Internal service calls use an internal API key. In a production deployment, secrets should be stored in Kubernetes Secrets / a secret manager and HTTPS should be enabled.

## Docker
Each service has its own Dockerfile. Docker Compose starts the complete local environment including ELK.

## Kubernetes
The `k8s/` directory contains Deployment and Service resources. Gateway uses NodePort 30080.

## CI/CD
GitHub Actions compiles Python and builds Docker images on every push/PR. On main, the workflow can push images to Docker Hub when credentials are configured.

## ELK
Services produce JSON logs. Logstash receives logs over TCP and stores them in Elasticsearch. Kibana can be used to create dashboards and search logs.

## Viva questions
1. What is a microservice? An independently deployable service focused on one business capability.
2. Why API Gateway? It gives clients one entry point and centralizes routing/authentication.
3. Why JWT? It allows stateless token-based authentication.
4. What is REST? An HTTP-based architectural style using resources and standard methods.
5. Why Docker? It packages an application and dependencies consistently.
6. Why Kubernetes? It orchestrates containers, scaling, service discovery and deployment.
7. What is CI/CD? Automated build/test/deployment pipeline.
8. What is ELK? Elasticsearch, Logstash and Kibana for collecting, storing and visualizing logs.
9. Why separate databases? Services own their data and remain loosely coupled.
10. How is a complaint tracked? The complaint ID identifies the resource and the status field represents its lifecycle.
