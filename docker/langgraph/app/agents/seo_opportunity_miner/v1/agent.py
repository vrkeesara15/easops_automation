"""SEO Opportunity Miner agent definition (v1)."""

from .graph import (
    MinerInput,
    MinerOutput,
    build_graph,
    prepare_state,
)

agent_id = "seo-opportunity-miner"
agent_version = "v1"
agent_input_model = MinerInput
agent_output_model = MinerOutput

__all__ = [
    "build_graph",
    "MinerInput",
    "MinerOutput",
    "prepare_state",
    "agent_id",
    "agent_version",
    "agent_input_model",
    "agent_output_model",
]
