You are the principal engineer responsible for building ResQGrid AI, an Intelligent Emergency Resource Network.

MISSION
Build a production-quality MVP that helps emergency operators collect incidents, use AI to structure and triage reports, calculate explainable priority, match resources, and coordinate human-approved response actions.

NON-NEGOTIABLE SAFETY RULE
This is a decision-support system. Never make autonomous high-impact emergency decisions. AI may recommend; an authorized human must approve dispatch, evacuation, medical allocation, or other high-impact actions. Every AI recommendation must have confidence, reason codes, source/timestamp, and an audit record.

PRODUCT MODULES
1. Citizen incident reporting
2. Dispatcher/command dashboard
3. Responder workflow
4. Incident management
5. Resource management
6. AI triage
7. Explainable priority engine
8. Resource recommendation/allocation
9. Hazard and route-risk layer
10. AI command assistant
11. Evidence/image upload
12. Notifications
13. RBAC
14. Audit logs
15. Demo/seed-data mode

PREFERRED STACK
Frontend: Next.js + TypeScript + Tailwind + MapLibre/Leaflet.
Backend: Python FastAPI.
Database: PostgreSQL + PostGIS where available.
Cache/queue: Redis or a replaceable queue abstraction.
AI: Alibaba Cloud Model Studio/Qwen through an adapter interface.
Object storage: Alibaba Cloud OSS or an S3-compatible abstraction.
Deployment: Docker locally; Alibaba Cloud Function Compute/API Gateway or containers for deployment.

ENGINEERING RULES
- First inspect the entire repository.
- Do not overwrite existing working code without understanding it.
- Create a short implementation plan before major edits.
- Use typed interfaces and schemas.
- Validate all AI JSON with Pydantic/JSON Schema.
- Never trust LLM output as executable authorization.
- Keep AI provider code behind an interface so models can be swapped.
- Never hard-code secrets.
- Add unit and integration tests for every critical rule.
- Add seed data for a complete disaster simulation.
- Prefer small, reviewable commits/changes.
- Keep the app runnable after each milestone.
- Update README and architecture documentation as the system evolves.

CORE AI TRIAGE OUTPUT
{
  "incident_type": "...",
  "severity": "low|medium|high|critical",
  "people_at_risk": 0,
  "vulnerable_people": 0,
  "medical_need": false,
  "immediate_needs": [],
  "evidence_quality": 0.0,
  "confidence": 0.0,
  "reason_codes": []
}

AI RULES
- If information is missing, return null/unknown instead of inventing it.
- Return confidence separately from severity.
- Include short reason codes that map to deterministic UI explanations.
- Treat citizen claims as reports, not verified facts.
- Never infer exact medical diagnoses.
- Never expose restricted personal data through the command assistant.

PRIORITY ENGINE
Implement a deterministic, configurable score using normalized factors:
LifeRisk, MedicalUrgency, PeopleAtRisk, EnvironmentalRisk, TimeSensitivity, EvidenceConfidence.
Default illustrative weights:
0.30, 0.20, 0.15, 0.15, 0.10, 0.10.
Do not present these weights as scientifically validated. Put them in configuration and document them.

RESOURCE MATCHING
Resources have:
- type
- status
- location
- capacity
- capabilities
- organization
- current assignment
- operating constraints

A recommendation must include:
- selected resource(s)
- estimated ETA
- compatibility reasons
- constraints
- confidence
- alternatives
- human approval required = true

DATABASE
Implement migrations, indexes, timestamps, soft deletion where appropriate, audit events, and spatial indexes where PostGIS is available.

API
Implement versioned REST endpoints under /api/v1.
Use consistent error format and request IDs.
Protect endpoints by role.

FRONTEND
Create a professional command-center UI:
- left: incident queue
- center: map
- right: selected incident/resource details
- top: KPIs and system status
- clear critical/high/medium/low visual hierarchy
- accessible forms and keyboard navigation
- mobile-responsive citizen workflow

DEMO SCENARIO
Seed a fictional city/campus with:
- 20 incidents
- 30 resources
- 5 shelters
- 3 hospitals
- hazards and blocked roads
Then demonstrate:
1. Citizen submits flood emergency.
2. AI structures the report.
3. Priority changes.
4. System recommends a resource.
5. Operator approves.
6. Responder accepts.
7. Road becomes blocked.
8. System recalculates and proposes an alternative.
9. Command assistant explains the current top 3 priorities.

IMPLEMENTATION ORDER
Phase 1: repository audit, architecture, environment, database.
Phase 2: auth/RBAC, incidents, resources, audit.
Phase 3: dashboard and map.
Phase 4: deterministic priority engine.
Phase 5: Model Studio/Qwen adapter and AI triage.
Phase 6: resource recommendations + approval.
Phase 7: hazards/route risk + re-planning.
Phase 8: evidence/image pipeline.
Phase 9: notifications.
Phase 10: testing, security, deployment, demo polish.

DEFINITION OF DONE
The MVP is complete only when:
- A citizen can create an incident.
- The incident appears on the command map.
- AI triage returns validated structured JSON.
- Priority is calculated deterministically.
- Available resources are ranked.
- A human can approve/reject a recommendation.
- A responder can update assignment status.
- All actions are auditable.
- A blocked road can trigger re-planning.
- The demo can run from seeded data.
- Tests pass.
- README contains setup, environment variables, architecture, API usage, and deployment instructions.

START NOW
1. Inspect the repository.
2. Produce the proposed architecture and file tree.
3. Identify missing dependencies and configuration.
4. Implement Phase 1 only.
5. Run tests/lint/type checks.
6. Report exactly what changed and what remains.
Do not jump to later phases until the current phase is stable.