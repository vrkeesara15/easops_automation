from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.agent_registry import register_agents

app = FastAPI(title="EASOPS Agents", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ui.agents.easops.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_agents(app)


@app.get("/")
def root():
    return {
        "service": "EASOPS Agent Runtime",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "agents": "/agents",
            "invoke_agent": "/agents/{agent_id}/run",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}
