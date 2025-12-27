from fastapi import FastAPI
from langgraph.graph import StateGraph
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="EASOPS Agents",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "service": "EASOPS Agent Runtime",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "invoke_agent": "/agents/{agent_id}/run"
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}

    return {"status": "ok"}