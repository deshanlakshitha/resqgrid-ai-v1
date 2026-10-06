# ResQGrid AI — Security Policy

---

## Non-Negotiable Safety Rule

**This is a decision-support system.** AI may recommend; an authorized human **must** approve dispatch, evacuation, medical allocation, or other high-impact actions.

## Security Architecture

### Authentication

- JWT-based with access tokens (30min) and refresh tokens (7 days)
- Passwords hashed with bcrypt
- Token includes user ID and role

### Authorization (RBAC)

| Role | Permissions |
|------|-------------|
| **Citizen** | Create incidents, upload evidence, view own reports |
| **Responder** | Update assignment status, view assigned incidents |
| **Dispatcher** | All citizen + manage incidents, run triage, approve recommendations |
| **Admin** | All dispatcher + manage users, view audit logs, system configuration |

### AI Safety

- All AI output validated against Pydantic schemas before use
- AI never executes database or infrastructure commands
- Prompt-injection defenses around tool use
- Confidence scores separate from severity
- Reason codes for explainability
- Missing information returns null, not invented data

### Data Protection

- Secrets in environment variables only (never in code)
- `.env` files in `.gitignore`
- JWT secret rotated periodically
- CORS restricted to allowed origins
- Personal data minimized in AI context
- Audit logs for all significant operations

### Input Validation

- All API inputs validated by Pydantic schemas
- File uploads limited by type and size
- SQL injection prevented by SQLAlchemy ORM
- XSS prevention by React/Next.js escaping

### API Security

- Rate limiting on public endpoints
- Request ID tracking for traceability
- Consistent error format (no stack traces in production)
- Role-based endpoint protection

### Infrastructure

- Docker containers run as non-root
- Database access via internal network only
- Redis accessible only from API service
- Evidence stored in dedicated OSS bucket with restricted access

## Incident Response

If a security issue is found:
1. Do not exploit it
2. Report to the project team
3. Document the finding
4. Fix before disclosure
