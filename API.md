# Digital Ninja API Documentation

## Overview

This document describes the API structure for Digital Ninja. Currently, the application is frontend-only, but this outlines the planned API architecture.

## REST API Endpoints (Planned)

### Projects

#### List Projects
```http
GET /api/projects
```

Response:
```json
{
  "projects": [
    {
      "id": "proj_123",
      "name": "My App",
      "description": "A sample application",
      "framework": "react",
      "createdAt": "2026-01-01T00:00:00Z",
      "updatedAt": "2026-01-07T00:00:00Z"
    }
  ]
}
```

#### Get Project
```http
GET /api/projects/:id
```

Response:
```json
{
  "id": "proj_123",
  "name": "My App",
  "description": "A sample application",
  "framework": "react",
  "files": [
    {
      "name": "App.tsx",
      "type": "file",
      "path": "/src/App.tsx",
      "content": "import React from 'react'..."
    }
  ]
}
```

#### Create Project
```http
POST /api/projects
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description",
  "framework": "react",
  "template": "react-starter"
}
```

#### Update Project
```http
PUT /api/projects/:id
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

#### Delete Project
```http
DELETE /api/projects/:id
```

### Files

#### Get File
```http
GET /api/projects/:projectId/files/:filePath
```

Response:
```json
{
  "name": "App.tsx",
  "path": "/src/App.tsx",
  "content": "import React from 'react'...",
  "language": "typescript"
}
```

#### Create File
```http
POST /api/projects/:projectId/files
Content-Type: application/json

{
  "name": "NewComponent.tsx",
  "path": "/src/components/",
  "content": "export default function NewComponent() { ... }"
}
```

#### Update File
```http
PUT /api/projects/:projectId/files/:filePath
Content-Type: application/json

{
  "content": "updated content..."
}
```

#### Delete File
```http
DELETE /api/projects/:projectId/files/:filePath
```

### AI Code Generation

#### Generate Code
```http
POST /api/ai/generate
Content-Type: application/json

{
  "prompt": "Create a login form",
  "context": "React with TypeScript",
  "language": "typescript",
  "framework": "react"
}
```

Response:
```json
{
  "code": "import React from 'react'...",
  "explanation": "This is a login form component...",
  "suggestions": [
    "Add form validation",
    "Implement error handling"
  ]
}
```

#### Optimize Code
```http
POST /api/ai/optimize
Content-Type: application/json

{
  "code": "function example() { ... }",
  "language": "typescript"
}
```

#### Debug Code
```http
POST /api/ai/debug
Content-Type: application/json

{
  "code": "function example() { ... }",
  "error": "TypeError: Cannot read property...",
  "language": "typescript"
}
```

### Templates

#### List Templates
```http
GET /api/templates
```

Response:
```json
{
  "templates": [
    {
      "id": "react-starter",
      "name": "React Starter",
      "description": "A basic React application",
      "framework": "react",
      "tags": ["react", "typescript"]
    }
  ]
}
```

#### Get Template
```http
GET /api/templates/:id
```

### Deployment

#### Deploy Project
```http
POST /api/deploy/:projectId
Content-Type: application/json

{
  "platform": "vercel",
  "config": {
    "buildCommand": "npm run build",
    "outputDirectory": ".next"
  }
}
```

Response:
```json
{
  "deploymentId": "deploy_123",
  "url": "https://my-app.vercel.app",
  "status": "deployed"
}
```

#### Get Deployment Status
```http
GET /api/deploy/:deploymentId
```

## WebSocket API (Planned)

### Real-time Collaboration

Connect to WebSocket:
```javascript
const ws = new WebSocket('wss://api.digitalninja.com/ws');
```

#### Events

**Join Project**
```json
{
  "type": "join",
  "projectId": "proj_123",
  "userId": "user_456"
}
```

**File Update**
```json
{
  "type": "file_update",
  "projectId": "proj_123",
  "filePath": "/src/App.tsx",
  "content": "updated content...",
  "userId": "user_456"
}
```

**Cursor Position**
```json
{
  "type": "cursor",
  "projectId": "proj_123",
  "filePath": "/src/App.tsx",
  "line": 10,
  "column": 5,
  "userId": "user_456"
}
```

## Authentication (Planned)

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

### Logout
```http
POST /api/auth/logout
Authorization: Bearer <token>
```

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

Common error codes:
- `BAD_REQUEST` (400)
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `NOT_FOUND` (404)
- `RATE_LIMIT_EXCEEDED` (429)
- `INTERNAL_SERVER_ERROR` (500)

## Rate Limiting

- Standard: 100 requests per minute
- AI Generation: 10 requests per minute
- WebSocket: 1000 messages per minute

## SDK/Client Libraries (Planned)

### JavaScript/TypeScript
```typescript
import { DigitalNinja } from '@digital-ninja/sdk';

const client = new DigitalNinja({
  apiKey: 'your-api-key'
});

const project = await client.projects.create({
  name: 'My App',
  framework: 'react'
});
```

### Python
```python
from digital_ninja import DigitalNinja

client = DigitalNinja(api_key='your-api-key')
project = client.projects.create(
    name='My App',
    framework='react'
)
```

## Versioning

API versions are specified in the URL:
- Current: `/api/v1/`
- Beta: `/api/v2-beta/`

## Support

For API support, please open an issue on GitHub or contact support@digitalninja.com
