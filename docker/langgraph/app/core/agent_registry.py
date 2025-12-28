"""Agent discovery, manifest validation, and FastAPI registration utilities.

This module introduces a manifest-driven agent registry so human and machine
consumers can reliably discover available LangGraph agents without hard-coded
imports. Agents are discovered dynamically from the filesystem using their
manifest files and are resolved at runtime per request to guarantee the latest
version is executed by default.
"""

from __future__ import annotations

import importlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Type

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from langgraph.graph import StateGraph
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

AGENT_MODULE_PREFIX = "docker.langgraph.app.agents"
AGENT_ROOT = Path(__file__).resolve().parents[1] / "agents"


class AgentManifest(BaseModel):
    """Schema for agent metadata shipped alongside each version."""

    agent_id: str
    version: str
    name: str
    category: str
    description: str
    when_to_use: str
    inputs: Dict[str, str]
    outputs: Dict[str, str]
    owner: str
    frequency: str
    cost: str


@dataclass
class AgentDefinition:
    """Runtime bindings for an agent implementation."""

    manifest: AgentManifest
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    build_graph: Callable[[], StateGraph]
    prepare_state: Callable[[BaseModel], dict]
    module_path: str


def _normalize_agent_id(agent_id: str) -> str:
    return agent_id.lower()


def _aliases(agent_id: str) -> set[str]:
    normalized = _normalize_agent_id(agent_id)
    return {
        normalized,
        normalized.replace("-", "_"),
        normalized.replace("_", "-"),
    }


def load_manifest(manifest_path: Path) -> AgentManifest:
    """Load and validate a manifest.json file."""

    if not manifest_path.exists():
        raise ValueError(f"Manifest file missing at {manifest_path}")

    try:
        payload = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in manifest {manifest_path}: {exc}") from exc

    try:
        return AgentManifest(**payload)
    except ValidationError as exc:
        raise ValueError(f"Manifest validation failed for {manifest_path}: {exc}") from exc


def _version_sort_key(version: str) -> tuple[int, Any]:
    """Deterministic sort key that prefers semantic versions when available."""

    value = version.lstrip("vV")
    try:
        from packaging.version import InvalidVersion, Version

        try:
            return (0, Version(value))
        except InvalidVersion:
            return (1, value)
    except Exception:  # pragma: no cover - defensive fallback
        logger.debug("packaging.version unavailable; falling back to string compare")
        return (1, value)


def resolve_latest_version(versions: Iterable[str]) -> str:
    try:
        return max(versions, key=_version_sort_key)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail="No versions available for agent") from exc


def _load_agent_definition(module_path: str, manifest: AgentManifest) -> AgentDefinition:
    """Import an agent module and align it with its manifest."""

    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # pragma: no cover - startup safety
        raise RuntimeError(f"Failed to import agent module '{module_path}': {exc}") from exc

    missing = [
        name
        for name in (
            "agent_id",
            "agent_version",
            "agent_input_model",
            "agent_output_model",
            "build_graph",
            "prepare_state",
        )
        if not hasattr(module, name)
    ]
    if missing:
        raise RuntimeError(
            f"Agent module '{module_path}' is missing required attributes: {', '.join(missing)}"
        )

    agent_id = getattr(module, "agent_id")
    agent_version = getattr(module, "agent_version")

    if agent_id != manifest.agent_id:
        raise RuntimeError(
            f"Manifest agent_id '{manifest.agent_id}' does not match module '{agent_id}' for {module_path}"
        )
    if agent_version != manifest.version:
        raise RuntimeError(
            f"Manifest version '{manifest.version}' does not match module '{agent_version}' for {module_path}"
        )

    return AgentDefinition(
        manifest=manifest,
        input_model=getattr(module, "agent_input_model"),
        output_model=getattr(module, "agent_output_model"),
        build_graph=getattr(module, "build_graph"),
        prepare_state=getattr(module, "prepare_state"),
        module_path=module_path,
    )


def discover_agents(base_path: Path = AGENT_ROOT) -> Dict[str, Dict[str, AgentDefinition]]:
    """Discover agents on disk by reading manifests and importing their modules."""

    registry: Dict[str, Dict[str, AgentDefinition]] = {}
    if not base_path.exists():
        logger.warning("Agent base path does not exist: %s", base_path)
        return registry

    for agent_dir in sorted(p for p in base_path.iterdir() if p.is_dir()):
        for version_dir in sorted(p for p in agent_dir.iterdir() if p.is_dir()):
            manifest_path = version_dir / "manifest.json"
            if not manifest_path.exists():
                logger.warning(
                    "Skipping agent at %s (missing manifest.json)", version_dir
                )
                continue

            manifest = load_manifest(manifest_path)

            agent_file = version_dir / "agent.py"
            if not agent_file.exists():
                raise RuntimeError(
                    f"Agent manifest found at {manifest_path} but agent.py is missing"
                )

            module_path = ".".join(
                [AGENT_MODULE_PREFIX, agent_dir.name, version_dir.name, "agent"]
            )
            definition = _load_agent_definition(module_path, manifest)

            versions = registry.setdefault(manifest.agent_id, {})
            if manifest.version in versions:
                logger.warning(
                    "Duplicate declaration for %s version %s; keeping first",
                    manifest.agent_id,
                    manifest.version,
                )
                continue
            versions[manifest.version] = definition

    return registry


def _build_alias_registry(registry: Mapping[str, Dict[str, AgentDefinition]]) -> Dict[str, Dict[str, AgentDefinition]]:
    alias_registry: Dict[str, Dict[str, AgentDefinition]] = {}
    for agent_id, versions in registry.items():
        for alias in _aliases(agent_id):
            alias_registry[alias] = versions
    return alias_registry


def _resolve_versions(
    registry: Mapping[str, Dict[str, AgentDefinition]], agent_id: str
) -> Dict[str, AgentDefinition]:
    alias = _normalize_agent_id(agent_id)
    if alias in registry:
        return registry[alias]

    raise HTTPException(status_code=404, detail="Agent not found")


def _build_response_model(registry: Mapping[str, Dict[str, AgentDefinition]]) -> Optional[type]:
    unique_models: list[type] = []
    for versions in registry.values():
        for definition in versions.values():
            if definition.output_model not in unique_models:
                unique_models.append(definition.output_model)

    if not unique_models:
        return None

    if len(unique_models) == 1:
        return unique_models[0]

    merged: Optional[type] = None
    for model in unique_models:
        merged = model if merged is None else merged | model  # type: ignore[assignment]

    if merged is None:
        logger.warning("Falling back to untyped response model for agents")
    return merged


def get_agent_metadata(registry: Mapping[str, Dict[str, AgentDefinition]]) -> list[dict[str, Any]]:
    """Return machine-friendly metadata for every registered agent."""

    metadata: list[dict[str, Any]] = []
    for agent_id, versions in sorted(registry.items()):
        latest_version = resolve_latest_version(versions.keys())
        latest_manifest = versions[latest_version].manifest
        sorted_versions = sorted(versions.keys(), key=_version_sort_key, reverse=True)

        metadata.append(
            {
                "agent_id": latest_manifest.agent_id,
                "name": latest_manifest.name,
                "category": latest_manifest.category,
                "description": latest_manifest.description,
                "when_to_use": latest_manifest.when_to_use,
                "inputs": latest_manifest.inputs,
                "outputs": latest_manifest.outputs,
                "owner": latest_manifest.owner,
                "frequency": latest_manifest.frequency,
                "cost": latest_manifest.cost,
                "latest_version": latest_version,
                "versions": sorted_versions,
                "manifests": {
                    version: definition.manifest.model_dump()
                    for version, definition in versions.items()
                },
            }
        )

    return metadata


def _render_catalog_html(metadata: list[dict[str, Any]]) -> str:
    by_category: Dict[str, list[dict[str, Any]]] = {}
    for agent in metadata:
        by_category.setdefault(agent["category"], []).append(agent)

    parts = ["<html><head><title>Agent Catalog</title></head><body>"]
    parts.append("<h1>Agent Catalog</h1>")
    parts.append(
        "<p>Use the POST /agents/{agent_id}/run endpoint to invoke agents. "
        "When version is omitted, the latest version is executed.</p>"
    )

    for category, agents in sorted(by_category.items()):
        parts.append(f"<h2>{category}</h2><ul>")
        for agent in sorted(agents, key=lambda a: a["name"]):
            parts.append("<li>")
            parts.append(f"<h3>{agent['name']} ({agent['agent_id']})</h3>")
            parts.append(f"<p><strong>Description:</strong> {agent['description']}</p>")
            parts.append(f"<p><strong>When to use:</strong> {agent['when_to_use']}</p>")
            parts.append(
                f"<p><strong>Run endpoint:</strong> POST /agents/{agent['agent_id']}/run</p>"
            )
            parts.append(
                f"<p><strong>Available versions:</strong> {', '.join(agent['versions'])} (latest: {agent['latest_version']})</p>"
            )
            parts.append("<p><strong>Inputs:</strong></p><ul>")
            for key, desc in agent["inputs"].items():
                parts.append(f"<li><code>{key}</code>: {desc}</li>")
            parts.append("</ul>")
            parts.append("<p><strong>Outputs:</strong></p><ul>")
            for key, desc in agent["outputs"].items():
                parts.append(f"<li><code>{key}</code>: {desc}</li>")
            parts.append("</ul>")
            parts.append(
                f"<p><strong>Owner:</strong> {agent['owner']} — <strong>Frequency:</strong> {agent['frequency']} — "
                f"<strong>Cost:</strong> {agent['cost']}</p>"
            )
            parts.append("</li>")
        parts.append("</ul>")

    parts.append("</body></html>")
    return "\n".join(parts)


def register_agents(app: FastAPI) -> None:
    """Auto-discover agents, validate manifests, and attach FastAPI routes."""

    registry_by_id = discover_agents(AGENT_ROOT)
    registry_by_alias = _build_alias_registry(registry_by_id)

    response_model = _build_response_model(registry_by_id)
    metadata = get_agent_metadata(registry_by_id)

    @app.get("/agents")
    def list_agents():
        return [
            {"agent_id": item["agent_id"], "latest_version": item["latest_version"]}
            for item in metadata
        ]

    @app.get("/agents/registry")
    def agent_registry():
        return metadata

    @app.get("/agents/catalog", response_class=HTMLResponse)
    def agent_catalog():
        return _render_catalog_html(metadata)

    @app.get("/agents/{agent_id}/versions")
    def list_agent_versions(agent_id: str):
        versions = _resolve_versions(registry_by_alias, agent_id)
        sorted_versions = sorted(versions.keys(), key=_version_sort_key, reverse=True)
        latest_version = resolve_latest_version(versions.keys())
        canonical_id = next(iter(versions.values())).manifest.agent_id
        return {
            "agent_id": canonical_id,
            "latest_version": latest_version,
            "versions": sorted_versions,
        }

    @app.post("/agents/{agent_id}/run", response_model=response_model)
    async def run_agent(
        agent_id: str, payload: Dict[str, Any] = Body(...), version: Optional[str] = None
    ):
        versions = _resolve_versions(registry_by_alias, agent_id)

        if version:
            if version not in versions:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Version '{version}' not found for agent '{agent_id}'. "
                        f"Available versions: {', '.join(sorted(versions.keys()))}."
                    ),
                )
            definition = versions[version]
        else:
            latest_version = resolve_latest_version(versions.keys())
            definition = versions[latest_version]

        try:
            parsed_payload = definition.input_model(**payload)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc

        graph: StateGraph = definition.build_graph()
        state = definition.prepare_state(parsed_payload)

        try:
            result = graph.invoke(state)
        except Exception as exc:  # pragma: no cover - runtime safety
            logger.exception("Agent '%s' failed during execution", definition.manifest.agent_id)
            raise HTTPException(status_code=500, detail="Agent execution failed") from exc

        if definition.output_model:
            return definition.output_model.model_validate(result)
        return result

    app.state.agent_registry = registry_by_id
    app.state.agent_versions = registry_by_alias
    app.state.agent_metadata = metadata
