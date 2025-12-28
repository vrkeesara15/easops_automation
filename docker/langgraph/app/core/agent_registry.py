"""Agent discovery and registration utilities."""

from __future__ import annotations

import importlib
import importlib.util
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


@dataclass
class AgentIndex:
    """Container for agent definitions and version metadata."""

    by_alias: Dict[str, Dict[str, AgentDefinition]] = field(default_factory=dict)
    by_id: Dict[str, Dict[str, AgentDefinition]] = field(default_factory=dict)

    def register(self, definition: AgentDefinition) -> None:
        """Register a discovered agent definition for each alias and version."""

        aliases = _collect_aliases(definition.id)
        definition.aliases = aliases

        for alias in aliases:
            alias_versions = self.by_alias.setdefault(alias, {})
            if definition.version in alias_versions:
                logger.warning(
                    "Duplicate agent alias '%s' with version '%s'; skipping",
                    alias,
                    definition.version,
                )
                continue
            alias_versions[definition.version] = definition

        id_versions = self.by_id.setdefault(definition.id, {})
        if definition.version in id_versions:
            logger.warning(
                "Duplicate agent id '%s' with version '%s'; skipping",
                definition.id,
                definition.version,
            )
            return

        id_versions[definition.version] = definition

    def all_definitions(self) -> Iterable[AgentDefinition]:
        for versions in self.by_id.values():
            yield from versions.values()

    def latest_by_alias(self) -> Dict[str, AgentDefinition]:
        return {
            alias: versions[select_latest_version(versions.keys())]
            for alias, versions in self.by_alias.items()
            if versions
        }

    def latest_by_id(self) -> Dict[str, AgentDefinition]:
        return {
            agent_id: versions[select_latest_version(versions.keys())]
            for agent_id, versions in self.by_id.items()
            if versions
        }


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


def _version_sort_key(version: str) -> tuple[int, Any]:
    """Generate a deterministic sort key for semantic-ish versions."""

    spec = importlib.util.find_spec("packaging.version")
    if spec is not None:
        from packaging.version import InvalidVersion, Version

        try:
            return (0, Version(version))
        except InvalidVersion:
            return (1, version)

    return (1, version)


def select_latest_version(versions: Iterable[str]) -> str:
    """Pick the latest version from an iterable of version strings."""

    try:
        return max(versions, key=_version_sort_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="No versions available for agent") from exc


def discover_agents(base_path: Path) -> AgentIndex:
    """Discover agent modules and return indexed definitions by id and alias."""

    index = AgentIndex()
    if not base_path.exists():
        logger.warning("Agent base path does not exist: %s", base_path)
        return index

    for agent_dir in sorted(base_path.iterdir()):
        if not agent_dir.is_dir() or agent_dir.name.startswith("__"):
            continue

        unversioned_init = agent_dir / "__init__.py"
        if unversioned_init.exists():
            module_name = f"{AGENT_MODULE_PREFIX}.{agent_dir.name}"
            definition = _load_agent_definition(module_name)
            if definition:
                index.register(definition)

        for version_dir in sorted(agent_dir.iterdir()):
            if not version_dir.is_dir() or version_dir.name.startswith("__"):
                continue

            init_file = version_dir / "__init__.py"
            if not init_file.exists():
                continue

            module_name = f"{AGENT_MODULE_PREFIX}.{agent_dir.name}.{version_dir.name}"
            definition = _load_agent_definition(module_name)
            if definition:
                index.register(definition)

    return index


def _load_agent_definition(module_name: str) -> Optional[AgentDefinition]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to import agent module %s: %s", module_name, exc)
        return None

    try:
        return AgentDefinition(
            id=getattr(module, "agent_id"),
            version=getattr(module, "agent_version"),
            input_model=getattr(module, "agent_input_model"),
            output_model=getattr(module, "agent_output_model"),
            build_graph=getattr(module, "build_graph"),
            prepare_state=getattr(module, "prepare_state"),
        )
    except AttributeError as exc:
        logger.error("Skipping agent module %s due to missing attribute: %s", module_name, exc)
        return None


def _resolve_version_map(index: AgentIndex, agent_id: str) -> Optional[Dict[str, AgentDefinition]]:
    normalized = _normalize_agent_id(agent_id)
    version_map = index.by_alias.get(normalized)
    if version_map:
        return version_map

    underscore = _normalize_agent_id(agent_id.replace("-", "_"))
    if underscore != normalized:
        return index.by_alias.get(underscore)

    return None


def resolve_agent_version(
    index: AgentIndex, agent_id: str, requested_version: Optional[str]
) -> AgentDefinition:
    """Resolve an agent definition for a given id and optional version."""

    version_map = _resolve_version_map(index, agent_id)
    if not version_map:
        raise HTTPException(status_code=404, detail="Agent not found")

    if requested_version:
        agent = version_map.get(requested_version)
        if not agent:
            available = ", ".join(
                sorted(version_map.keys(), key=_version_sort_key, reverse=True)
            )
            detail = (
                f"Version '{requested_version}' not found for agent '{agent_id}'. "
                f"Available versions: {available or 'none'}."
            )
            raise HTTPException(status_code=404, detail=detail)
        return agent

    latest_version = select_latest_version(version_map.keys())
    return version_map[latest_version]


def register_agents(app: FastAPI) -> None:
    """Auto-discover agents and attach FastAPI routes."""

    base_path = Path(__file__).resolve().parents[1] / "agents"
    index = discover_agents(base_path)

    latest_by_alias = index.latest_by_alias()
    latest_by_id = index.latest_by_id()

    response_model = _build_response_model(index.all_definitions())

    @app.get("/agents")
    def list_agents():
        return [
            {"agent_id": agent_id, "version": definition.version}
            for agent_id, definition in sorted(latest_by_id.items())
        ]

    @app.get("/agents/{agent_id}/versions")
    def list_agent_versions(agent_id: str):
        version_map = _resolve_version_map(index, agent_id)
        if not version_map:
            raise HTTPException(status_code=404, detail="Agent not found")

        sorted_versions = sorted(
            version_map.keys(), key=_version_sort_key, reverse=True
        )
        latest_version = select_latest_version(version_map.keys())
        canonical_id = next(iter(version_map.values())).id
        return {
            "agent_id": canonical_id,
            "latest_version": latest_version,
            "versions": sorted_versions,
        }

    @app.post("/agents/{agent_id}/run", response_model=response_model)
    async def run_agent(
        agent_id: str, payload: Dict[str, Any] = Body(...), version: Optional[str] = None
    ):
        agent = resolve_agent_version(index, agent_id, version)

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

    app.state.agents = latest_by_alias
    app.state.agent_catalog = latest_by_id
    app.state.agent_versions = index.by_id
