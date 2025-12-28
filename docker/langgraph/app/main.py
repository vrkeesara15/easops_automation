from fastapi import FastAPI, HTTPException
from langgraph.graph import StateGraph

from .agents.daily_site_improvement_planner import (
    PlannerInput,
    PlannerOutput,
    build_graph,
    prepare_state,
)

app = FastAPI(title="EASOPS Agents", version="1.0.0")


@app.get("/")
def root():
    return {
        "service": "EASOPS Agent Runtime",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "invoke_agent": "/agents/{agent_id}/run",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/agents/{agent_id}/run", response_model=PlannerOutput)
def run_agent(agent_id: str, payload: PlannerInput):
    if agent_id.lower() not in {"daily-site-improvement-planner", "daily_site_improvement_planner"}:
        raise HTTPException(status_code=404, detail="Agent not found")

    graph: StateGraph = build_graph()
    state = prepare_state(payload)
    result = graph.invoke(state)
    return result
