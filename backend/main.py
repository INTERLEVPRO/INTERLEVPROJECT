from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import routes_cv, routes_candidates, routes_jobs, routes_matches, routes_applications, routes_review, routes_logs, routes_settings, routes_notifications, routes_mcp
from backend.app.database import engine, Base

# Create tables for MVP (in production use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="INTERLEV Agentic AI Recruitment Automation System",
    description="Autonomous CV formatting, job discovery, matching, and review workflows.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(routes_candidates.router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(routes_jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(routes_matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(routes_applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(routes_review.router, prefix="/api/review", tags=["Review"])
app.include_router(routes_logs.router, prefix="/api/agent-logs", tags=["Logs"])
app.include_router(routes_settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(routes_notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(routes_mcp.router, prefix="/api/mcp", tags=["MCP"])

@app.get("/")
def read_root():
    return {"message": "Welcome to INTERLEV Agentic AI API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "interlev-agent-api", "version": app.version}
