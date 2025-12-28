from fastapi import FastAPI

from .core.agent_registry import register_agents

app = FastAPI(title="EASOPS Agents", version="1.0.0")
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
