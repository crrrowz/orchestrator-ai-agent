---
name: api-design-contract
description: Enterprise API contract specification skill. Enforces RESTful conventions, semantic HTTP status codes, structured error payloads, and OpenAPI schemas.
triggers:
  - api
  - rest
  - endpoint
  - route
  - schema
  - contract
---

# API Design Contract

## 1. RESTful Standards
- Resource URIs: Use plural nouns (`/api/v1/resources`, `/api/v1/resources/{id}`).
- HTTP Verbs: `GET` (read), `POST` (create), `PUT` (replace), `PATCH` (update), `DELETE` (remove).

## 2. Response Envelopes
- Success: `{"success": true, "data": {}, "error": null}`
- Error: `{"success": false, "data": null, "error": {"code": "CODE", "message": "Detail"}}`

## 3. Status Codes
- `200` OK, `201` Created, `204` No Content
- `400` Bad Request, `401` Unauthorized, `403` Forbidden, `404` Not Found, `422` Unprocessable, `500` Internal Error
