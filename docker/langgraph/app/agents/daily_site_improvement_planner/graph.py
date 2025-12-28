"""LangGraph agent for planning a single daily site improvement task."""

from typing import List, Optional, TypedDict, Union

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class BacklogItem(BaseModel):
    """Normalized backlog item."""

    title: str = Field(..., description="Short title for the idea/task.")
    impact: Optional[int] = Field(
        None,
        description="Relative impact score (higher is better).",
        ge=1,
        le=10,
    )
    effort: Optional[int] = Field(
        None,
        description="Relative effort score (higher means more effort).",
        ge=1,
        le=10,
    )
    category: Optional[str] = Field(
        None, description="Type of task, e.g., conversion, performance, SEO, reliability."
    )
    notes: Optional[str] = Field(None, description="Optional supporting details.")


class PlannerConstraints(BaseModel):
    """Execution constraints used to filter candidate tasks."""

    time_hours: Optional[int] = Field(
        None, description="Time available today for delivery."
    )
    risk_tolerance: Optional[str] = Field(
        None, description="Risk appetite, e.g., 'low', 'medium', 'high'."
    )
    allow_design: bool = Field(
        True, description="Whether design/UX changes are allowed today."
    )
    allow_code: bool = Field(
        True, description="Whether code deployments are allowed today."
    )


class PlannerInput(BaseModel):
    """Inputs expected by the Daily Site Improvement Planner agent."""

    metrics: str = Field(..., description="GA4/Search Console summary for the site.")
    backlog: List[Union[str, BacklogItem]] = Field(
        default_factory=list,
        description="List of candidate ideas. Can be strings or structured items.",
    )
    constraints: PlannerConstraints = Field(
        default_factory=PlannerConstraints, description="Execution constraints."
    )


class PlannedOption(TypedDict):
    """Shortlisted option with deterministic scoring."""

    title: str
    score: int
    category: str
    reason: str
    expected_impact: str


class PlannerState(TypedDict, total=False):
    """Internal state passed between LangGraph nodes."""

    metrics: str
    backlog: List[BacklogItem]
    constraints: PlannerConstraints
    analysis: str
    shortlisted: List[PlannedOption]
    decision: PlannedOption


class PlannerOutput(BaseModel):
    """Agent output schema."""

    selected_task: str
    reason: str
    expected_impact: str
    acceptance_criteria: List[str]
    rollback_plan: List[str]


CATEGORY_HINTS = {
    "conversion": ["conversion", "checkout", "form", "cart", "funnel"],
    "performance": ["performance", "speed", "lcp", "core web vitals", "cls"],
    "seo": ["search", "seo", "ranking", "crawl", "index"],
    "reliability": ["error", "bug", "downtime", "crash", "500", "404"],
}


def _normalize_backlog_item(item: Union[str, BacklogItem]) -> BacklogItem:
    if isinstance(item, BacklogItem):
        return item
    if isinstance(item, str):
        return BacklogItem(title=item)
    raise TypeError("Backlog items must be strings or BacklogItem objects")


def _categorize(metrics: str) -> str:
    lowered = metrics.lower()
    for category, keywords in CATEGORY_HINTS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "conversion"


def _score_item(item: BacklogItem, category_focus: str, constraints: PlannerConstraints) -> int:
    impact = item.impact if item.impact is not None else 6
    effort = item.effort if item.effort is not None else 3
    score = impact - effort

    title_lower = item.title.lower()
    if category_focus and category_focus in (item.category or "").lower():
        score += 2
    if category_focus in title_lower:
        score += 1

    if not constraints.allow_design and "design" in title_lower:
        score -= 4
    if not constraints.allow_code and any(term in title_lower for term in ("deploy", "release", "refactor")):
        score -= 4

    if constraints.time_hours is not None and constraints.time_hours < 4 and effort > 5:
        score -= 3
    if constraints.risk_tolerance and constraints.risk_tolerance.lower() == "low":
        if any(term in title_lower for term in ("experiment", "ab test", "a/b", "major")):
            score -= 2

    return score


def analyze(state: PlannerState) -> PlannerState:
    constraints = state.get("constraints", PlannerConstraints())
    category_focus = _categorize(state.get("metrics", ""))

    shortlisted: List[PlannedOption] = []
    reasons: List[str] = []
    for raw_item in state.get("backlog", []):
        score = _score_item(raw_item, category_focus, constraints)
        expected_impact = raw_item.notes or (
            f"Improve {category_focus} performance with a low-risk iteration"
        )
        shortlisted.append(
            {
                "title": raw_item.title,
                "score": score,
                "category": raw_item.category or category_focus,
                "reason": f"Aligned to {category_focus} signal and fits constraints",
                "expected_impact": expected_impact,
            }
        )
        reasons.append(f"{raw_item.title} scored {score} for {category_focus} focus")

    shortlisted.sort(key=lambda item: item["score"], reverse=True)
    analysis = (
        f"Focus category: {category_focus}. "
        f"Evaluated {len(shortlisted)} backlog items. "
        + " | ".join(reasons or ["No backlog items supplied; will generate a safety net task."])
    )

    return {
        **state,
        "shortlisted": shortlisted[:3] if shortlisted else [],
        "analysis": analysis,
    }


def decide(state: PlannerState) -> PlannerState:
    shortlisted = state.get("shortlisted") or []
    if shortlisted:
        decision = shortlisted[0]
    else:
        focus = _categorize(state.get("metrics", ""))
        decision = {
            "title": f"Create a fast, low-risk {focus} improvement",
            "score": 1,
            "category": focus,
            "reason": "No backlog supplied; created default action",
            "expected_impact": f"Stabilize {focus} KPI with quick win",
        }

    return {**state, "decision": decision}


def summarize(state: PlannerState) -> PlannerOutput:
    decision = state["decision"]
    acceptance_criteria = [
        f"{decision['title']} is scoped and documented with owners assigned",
        "Change is reviewed for risk and aligns with today's constraints",
        "Monitoring or analytics check is in place to validate impact",
    ]

    rollback_plan = [
        "If negative signals appear, disable or revert the change immediately",
        "Restore prior configuration or content from version control",
        "Communicate rollback and next steps in the release channel",
    ]

    return PlannerOutput(
        selected_task=decision["title"],
        reason=decision["reason"],
        expected_impact=decision["expected_impact"],
        acceptance_criteria=acceptance_criteria,
        rollback_plan=rollback_plan,
    )


def prepare_state(payload: PlannerInput) -> PlannerState:
    normalized_backlog = [_normalize_backlog_item(item) for item in payload.backlog]
    return {
        "metrics": payload.metrics,
        "backlog": normalized_backlog,
        "constraints": payload.constraints,
    }


def build_graph() -> StateGraph:
    graph = StateGraph(PlannerState)
    graph.add_node("analyze", analyze)
    graph.add_node("decide", decide)
    graph.add_node("summarize", summarize)

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "decide")
    graph.add_edge("decide", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()
