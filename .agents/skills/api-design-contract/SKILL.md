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

# API Design & Contract Specification Protocol

## 1. RESTful Standards
- **Resource-Oriented URIs**: Use plural nouns (`/api/v1/users`, `/api/v1/tasks/{id}`). Never use verbs in paths.
- **HTTP Verbs**:
  - `GET`: Safe, idempotent read operations.
  - `POST`: Create resource or execute non-idempotent action.
  - `PUT`: Full resource replacement.
  - `PATCH`: Partial resource update.
  - `DELETE`: Remove resource.

## 2. Standardized Response Formats
All API responses must follow a consistent envelope or structure:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2026-09-23T00:00:00Z",
    "request_id": "req-12345"
  }
}
```

In case of error:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Detailed human-readable message",
    "details": []
  }
}
```

## 3. Status Code Semantics
- `200 OK`: Request succeeded with body.
- `201 Created`: Resource successfully created.
- `204 No Content`: Successful deletion or action with no response body.
- `400 Bad Request`: Client input validation failure.
- `401 Unauthorized`: Missing or invalid authentication token.
- `403 Forbidden`: Authenticated user lacks permission.
- `404 Not Found`: Target resource does not exist.
- `422 Unprocessable Entity`: Semantic validation failed.
- `500 Internal Server Error`: Unhandled server exception.
