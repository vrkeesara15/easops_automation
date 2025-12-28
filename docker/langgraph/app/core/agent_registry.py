"""Agent discovery and registration utilities."""

from __future__ import annotations

import importlib
import logging
import operator
from dataclasses import dataclass, field
from functools import reduce
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Type

from fastapi import Body, FastAPI, HTTPException
from langgraph.graph import StateGraph
from pydantic import BaseModel

logger = logging.getLogger(__name__)

AGENT_MODULE_PREFIX = "docker.langgraph.app.agents"


@dataclass
class AgentDefinition:
    """Structured metadata for an agent implementation."""

    id: str
    version: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    build_graph: Callable[[], StateGraph]
    prepare_state: Callable[[BaseModel], dict]
    aliases: tuple[str, ...] = field(default_factory=tuple)


def _normalize_agent_id(agent_id: str) -> str:
    return agent_id.lower()


def _collect_aliases(agent_id: str) -> tuple[str, ...]:
    aliases = {_normalize_agent_id(agent_id)}
    underscore = _normalize_agent_id(agent_id.replace("-", "_"))
    aliases.add(underscore)
    return tuple(sorted(aliases))


def _build_response_model(agents: Iterable[AgentDefinition]) -> Optional[type]:
    unique_models: list[type] = []
    for agent in agents:
        if agent.output_model not in unique_models:
            unique_models.append(agent.output_model)

    if not unique_models:
        return None

    if len(unique_models) == 1:
        return unique_models[0]

    try:
        return reduce(operator.or_, unique_models)  # type: ignore[return-value]
    except TypeError:
        # Fallback to no response model if unions cannot be composed dynamically.
        logger.warning("Falling back to untyped response model for agents")
        return None


def discover_agents(base_path: Path) -> Dict[str, AgentDefinition]:
    """Discover agent modules under ``base_path`` and return a lookup map.

    The lookup map includes both the canonical agent id and an underscore alias.
    """

    agents: Dict[str, AgentDefinition] = {}
    if not base_path.exists():
        logger.warning("Agent base path does not exist: %s", base_path)
        return agents

    for module_dir in sorted(base_path.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("__"):
            continue

        init_file = module_dir / "__init__.py"
        if not init_file.exists():
            continue

        module_name = f"{AGENT_MODULE_PREFIX}.{module_dir.name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to import agent module %s: %s", module_name, exc)
            continue

        try:
            definition = AgentDefinition(
                id=getattr(module, "agent_id"),
                version=getattr(module, "agent_version"),
                input_model=getattr(module, "agent_input_model"),
                output_model=getattr(module, "agent_output_model"),
                build_graph=getattr(module, "build_graph"),
                prepare_state=getattr(module, "prepare_state"),
            )
        except AttributeError as exc:
            logger.error("Skipping agent module %s due to missing attribute: %s", module_name, exc)
            continue

        aliases = _collect_aliases(definition.id)
        definition.aliases = aliases

        for alias in aliases:
            if alias in agents:
                logger.warning("Duplicate agent alias '%s' in module %s; skipping", alias, module_name)
                continue
            agents[alias] = definition
            logger.info("Registered agent '%s' (alias '%s')", definition.id, alias)

    return agents


def register_agents(app: FastAPI) -> None:
    """Auto-discover agents and attach FastAPI routes."""

    base_path = Path(__file__).resolve().parents[1] / "agents"
    agents = discover_agents(base_path)
    catalog: Dict[str, AgentDefinition] = {}
    for definition in agents.values():
        catalog.setdefault(definition.id, definition)

    response_model = _build_response_model(catalog.values())

    @app.get("/agents")
    def list_agents():
        return [{"agent_id": agent.id, "version": agent.version} for agent in catalog.values()]

    @app.post("/agents/{agent_id}/run", response_model=response_model)
    async def run_agent(agent_id: str, payload: Dict[str, Any] = Body(...)):
        normalized = _normalize_agent_id(agent_id)
        agent = agents.get(normalized)
        if not agent:
            agent = agents.get(_normalize_agent_id(agent_id.replace("-", "_")))
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        try:
            parsed_payload = agent.input_model(**payload)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc

        graph: StateGraph = agent.build_graph()
        state = agent.prepare_state(parsed_payload)

        try:
            result = graph.invoke(state)
        except Exception as exc:  # pragma: no cover - runtime safety
            logger.exception("Agent '%s' failed during execution", agent.id)
            raise HTTPException(status_code=500, detail="Agent execution failed") from exc

        return agent.output_model.model_validate(result)

    app.state.agents = agents
    app.state.agent_catalog = catalog
