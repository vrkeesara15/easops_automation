from dataclasses import dataclass
from typing import Any, Callable, Dict, Type, Union

from fastapi import Body, FastAPI, HTTPException
from langgraph.graph import StateGraph
from pydantic import BaseModel

from .agents import daily_site_improvement_planner, seo_opportunity_miner


@dataclass
class AgentDefinition:
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    build_graph: Callable[[], StateGraph]
    prepare_state: Callable[[BaseModel], dict]


AGENTS: Dict[str, AgentDefinition] = {
    "daily-site-improvement-planner": AgentDefinition(
        input_model=daily_site_improvement_planner.PlannerInput,
        output_model=daily_site_improvement_planner.PlannerOutput,
        build_graph=daily_site_improvement_planner.build_graph,
        prepare_state=daily_site_improvement_planner.prepare_state,
    ),
    "daily_site_improvement_planner": AgentDefinition(
        input_model=daily_site_improvement_planner.PlannerInput,
        output_model=daily_site_improvement_planner.PlannerOutput,
        build_graph=daily_site_improvement_planner.build_graph,
        prepare_state=daily_site_improvement_planner.prepare_state,
    ),
    "seo-opportunity-miner": AgentDefinition(
        input_model=seo_opportunity_miner.MinerInput,
        output_model=seo_opportunity_miner.MinerOutput,
        build_graph=seo_opportunity_miner.build_graph,
        prepare_state=seo_opportunity_miner.prepare_state,
    ),
    "seo_opportunity_miner": AgentDefinition(
        input_model=seo_opportunity_miner.MinerInput,
        output_model=seo_opportunity_miner.MinerOutput,
        build_graph=seo_opportunity_miner.build_graph,
        prepare_state=seo_opportunity_miner.prepare_state,
    ),
}

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


@app.post(
    "/agents/{agent_id}/run",
    response_model=Union[
        daily_site_improvement_planner.PlannerOutput, seo_opportunity_miner.MinerOutput
    ],
)
def run_agent(agent_id: str, payload: Dict[str, Any] = Body(...)):
    key = agent_id.lower()
    agent = AGENTS.get(key)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    parsed_payload = agent.input_model(**payload)
    graph: StateGraph = agent.build_graph()
    state = agent.prepare_state(parsed_payload)
    result = graph.invoke(state)
    return agent.output_model.model_validate(result)
