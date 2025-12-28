"""Shared agent state definitions and helpers for LangGraph agents.

These schemas standardize how agents receive inputs, emit outputs, and
communicate intermediate state between LangGraph nodes. The models are
kept intentionally JSON-serializable and use plain Python collections so
that downstream automation tools (e.g., n8n) can easily consume them.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseAgentInput(BaseModel):
    """Canonical input envelope passed to every agent.

    Attributes:
        agent_id: Identifier for the agent implementation (e.g., "seo-opportunity-miner").
        agent_version: Semantic or git-based version of the agent.
        run_id: Unique identifier for the invocation; useful for tracing.
        input_payload: Arbitrary structured payload that the agent should process.
        metadata: Optional unstructured metadata (headers, user info, etc.).
    """

    agent_id: str = Field(..., description="Agent identifier, stable across deployments.")
    agent_version: str = Field(..., description="Version string for the agent logic.")
    run_id: str = Field(..., description="Unique identifier for the current run.")
    input_payload: Dict[str, Any] = Field(
        ..., description="Raw payload the agent should operate on."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional contextual metadata for tracing or auditing.",
    )

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=False)


class BaseAgentOutput(BaseModel):
    """Standardized output envelope produced by agents."""

    success: bool = Field(..., description="Whether the agent completed successfully.")
    summary: str = Field(..., description="High-level description of the outcome.")
    artifacts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of generated assets (files, links, structured payloads).",
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured metrics for observability (latency, token counts, etc.).",
    )
    next_actions: List[str] = Field(
        default_factory=list,
        description="Actionable follow-ups suggested by the agent.",
    )

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=False)


class BaseAgentState(BaseModel):
    """LangGraph-compatible state shared across all agents.

    This model can be used directly as a LangGraph state type. It stores the
    normalized input envelope, an optional output envelope, and any logs
    collected during the run. Because it is a Pydantic model backed by plain
    Python data structures, it remains JSON-serializable and compatible with
    low-code orchestrators such as n8n.
    """

    input: BaseAgentInput = Field(
        ..., description="Normalized agent input provided at invocation time."
    )
    output: Optional[BaseAgentOutput] = Field(
        default=None, description="Finalized agent output once processing completes."
    )
    logs: List[str] = Field(
        default_factory=list, description="Ordered log lines collected during execution."
    )

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=False)


def init_state(agent_input: BaseAgentInput) -> BaseAgentState:
    """Create the initial state for an agent run.

    The returned state is ready to be passed into a LangGraph state machine.
    Logs start empty and `output` is unset to reflect an in-progress run.
    """

    return BaseAgentState(input=agent_input)


def finalize_state(state: BaseAgentState, output: BaseAgentOutput) -> BaseAgentState:
    """Produce a new state with the final output attached.

    This helper keeps the existing input and logs, returning an updated
    `BaseAgentState` instance to make downstream serialization trivial.
    """

    return state.model_copy(update={"output": output})
