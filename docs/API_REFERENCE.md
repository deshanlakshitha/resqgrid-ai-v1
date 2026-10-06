# ResQGrid AI — API Reference

Complete API reference for all endpoints.

Base URL: `http://localhost:8000/api/v1`

---

## Authentication

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "role": "citizen",
  "organization": "Example Org"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@resqgrid.local",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Get Profile
```http
GET /auth/me
Authorization: Bearer {access_token}
```

---

## Incidents

### Create Incident
```http
POST /incidents
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Flash flood at Riverside",
  "description": "Water rising rapidly. Families trapped.",
  "incident_type": "flood",
  "latitude": 1.3621,
  "longitude": 103.8398,
  "address": "123 River Road",
  "people_at_risk": 25,
  "vulnerable_people": 8,
  "injuries_reported": 2,
  "medical_need": true,
  "reporter_name": "Jane Smith",
  "reporter_phone": "+1234567890"
}
```

### List Incidents
```http
GET /incidents?status=reported&severity=critical&page=1&page_size=50
Authorization: Bearer {access_token}
```

### Run AI Triage
```http
POST /incidents/{incident_id}/triage
Authorization: Bearer {access_token}

Response:
{
  "incident_type": "flood",
  "severity": "critical",
  "people_at_risk": 25,
  "vulnerable_people": 8,
  "medical_need": true,
  "immediate_needs": ["evacuation", "medical", "shelter"],
  "evidence_quality": 0.86,
  "confidence": 0.91,
  "reason_codes": ["rapid_water_rise", "vulnerable_population"]
}
```

### Calculate Priority
```http
POST /incidents/{incident_id}/priority
Authorization: Bearer {access_token}

Response:
{
  "score": 78.5,
  "components": {
    "life_risk": 100.0,
    "medical_urgency": 100.0,
    "people_at_risk": 50.0,
    "environmental_risk": 80.0,
    "time_sensitivity": 45.0,
    "evidence_confidence": 91.0
  },
  "weights": {
    "life_risk": 0.30,
    "medical_urgency": 0.20,
    "people_at_risk": 0.15,
    "environmental_risk": 0.15,
    "time_sensitivity": 0.10,
    "evidence_confidence": 0.10
  },
  "reason_codes": ["high_life_risk", "urgent_medical_need"],
  "calculated_at": "2026-08-31T12:00:00Z"
}
```

---

## Resources

### List Available Resources
```http
GET /resources/available?resource_type=ambulance
Authorization: Bearer {access_token}
```

---

## Recommendations

### Approve
```http
POST /recommendations/{id}/approve
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "approved": true,
  "reason": "Best available resource"
}
```

### Reject
```http
POST /recommendations/{id}/reject
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "approved": false,
  "reason": "Resource too far away"
}
```

---

## Dashboard

### Get Summary
```http
GET /dashboard/summary
Authorization: Bearer {access_token}

Response:
{
  "total_incidents": 20,
  "active_incidents": 15,
  "critical_incidents": 4,
  "available_resources": 25,
  "deployed_resources": 5,
  "pending_recommendations": 3,
  "active_assignments": 5,
  "active_hazards": 8,
  "avg_response_time_minutes": null
}
```

---

## AI Assistant

### Query
```http
POST /assistant/query
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "question": "What are the top 3 priority incidents right now?"
}
```

---

## Error Format

All errors follow a consistent format:

```json
{
  "detail": "Error description",
  "request_id": "uuid-string",
  "timestamp": "2026-08-31T12:00:00Z"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request — validation error |
| 401 | Unauthorized — invalid/missing token |
| 403 | Forbidden — insufficient role |
| 404 | Not Found — entity doesn't exist |
| 422 | Unprocessable Entity — schema validation failed |
| 500 | Internal Server Error |
