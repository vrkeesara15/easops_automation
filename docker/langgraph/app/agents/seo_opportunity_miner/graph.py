"""LangGraph agent for mining SEO quick win opportunities."""

from collections import defaultdict
from typing import Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class SearchConsoleRow(BaseModel):
    """Normalized Search Console row."""

    query: str = Field(..., description="Search query")
    page: str = Field(..., description="Page URL that ranked for the query")
    impressions: int = Field(..., ge=0, description="Impressions for the query/page pair")
    clicks: int = Field(..., ge=0, description="Clicks for the query/page pair")
    position: float = Field(..., ge=0, description="Average position for the query/page pair")


class MinerInput(BaseModel):
    """Inputs expected by the SEO Opportunity Miner agent."""

    search_console_rows: List[SearchConsoleRow] = Field(
        ..., description="List of Search Console rows including query, page, and metrics."
    )
    site_pages: List[str] = Field(
        default_factory=list,
        description="Known site pages used to validate recommendations.",
    )


class MinerOutput(BaseModel):
    """Agent output schema for a single prioritized fix."""

    page_url: str
    keyword: str
    issue_type: str
    recommended_fix: str
    estimated_impact: str


class MinerState(TypedDict, total=False):
    """Internal state passed between LangGraph nodes."""

    search_console_rows: List[SearchConsoleRow]
    site_pages: List[str]
    opportunities: List[Dict[str, object]]
    best_recommendation: Dict[str, object]


MIN_IMPRESSIONS = 50
LOW_CTR_THRESHOLD = 2.5
MID_POSITION_RANGE = (6, 20)


def _ctr(clicks: int, impressions: int) -> float:
    if impressions == 0:
        return 0.0
    return round((clicks / impressions) * 100, 2)


def _score_opportunity(opportunity: Dict[str, str]) -> float:
    impressions = opportunity.get("impressions", 0)
    ctr_gap = opportunity.get("ctr_gap", 0)
    position_score = opportunity.get("position_score", 0)
    cannibalization_weight = 15 if opportunity.get("issue_type") == "cannibalization" else 0
    return impressions + ctr_gap + position_score + cannibalization_weight


def analyze(state: MinerState) -> MinerState:
    rows = state.get("search_console_rows") or []
    site_pages = set(state.get("site_pages") or [])
    query_groups: Dict[str, List[SearchConsoleRow]] = defaultdict(list)
    for row in rows:
        query_groups[row.query.lower()].append(row)

    opportunities: List[Dict[str, str]] = []

    for row in rows:
        ctr = _ctr(row.clicks, row.impressions)
        impressions = row.impressions

        if impressions >= MIN_IMPRESSIONS and ctr < LOW_CTR_THRESHOLD:
            opportunities.append(
                {
                    "page_url": row.page,
                    "keyword": row.query,
                    "issue_type": "ctr",
                    "recommended_fix": (
                        "Tighten the title tag and H1 around the keyword, add a benefit-driven meta "
                        "description, and place 2 internal links with the exact query in anchor text "
                        "from relevant pages."
                    ),
                    "estimated_impact": "Higher click-through rate from existing impressions.",
                    "impressions": impressions,
                    "ctr_gap": max(5.0 - ctr, 0),
                    "position_score": max(0, 25 - row.position),
                }
            )

        if MID_POSITION_RANGE[0] <= row.position <= MID_POSITION_RANGE[1] and impressions >= MIN_IMPRESSIONS:
            opportunities.append(
                {
                    "page_url": row.page,
                    "keyword": row.query,
                    "issue_type": "rank",
                    "recommended_fix": (
                        "Add 3-5 internal links pointing to this URL with the keyword in anchor text, "
                        "align the H1/H2 with the query, and include a concise FAQ section to earn "
                        "rich snippet eligibility."
                    ),
                    "estimated_impact": "Move the page into the top 5 positions for incremental clicks.",
                    "impressions": impressions,
                    "ctr_gap": max(3.0 - ctr, 0),
                    "position_score": max(0, 30 - row.position * 1.5),
                }
            )

    for query, grouped_rows in query_groups.items():
        if len(grouped_rows) < 2:
            continue

        canonical = max(grouped_rows, key=lambda r: (r.clicks, -r.position))
        competing = [row for row in grouped_rows if row.page != canonical.page]
        competing_paths = ", ".join({row.page for row in competing})

        opportunities.append(
            {
                "page_url": canonical.page,
                "keyword": canonical.query,
                "issue_type": "cannibalization",
                "recommended_fix": (
                    "Choose this URL as the primary page, add internal links to it from the competing "
                    f"pages ({competing_paths}), and adjust their headings to target secondary terms "
                    "instead of the main keyword."
                ),
                "estimated_impact": "Consolidated relevance should lift rankings and CTR for the primary page.",
                "impressions": canonical.impressions,
                "ctr_gap": max(5.0 - _ctr(canonical.clicks, canonical.impressions), 0),
                "position_score": max(0, 25 - canonical.position),
            }
        )

    if site_pages:
        for opportunity in opportunities:
            if opportunity["page_url"] not in site_pages:
                opportunity["recommended_fix"] += " Validate this URL exists or update to the closest matching live page."

    scored = sorted(opportunities, key=_score_opportunity, reverse=True)

    return {**state, "opportunities": scored}


def decide(state: MinerState) -> MinerState:
    opportunities = state.get("opportunities") or []
    if opportunities:
        best = opportunities[0]
    else:
        best = {
            "page_url": state.get("site_pages", ["/"])[0] if state.get("site_pages") else "",
            "keyword": "",
            "issue_type": "rank",
            "recommended_fix": "Add an internal link cluster around the homepage with the top commercial keyword.",
            "estimated_impact": "Small uplift from clarifying site relevance.",
        }

    clean_best = {k: v for k, v in best.items() if k in {"page_url", "keyword", "issue_type", "recommended_fix", "estimated_impact"}}
    return {**state, "best_recommendation": clean_best}


def summarize(state: MinerState) -> MinerOutput:
    best = state.get("best_recommendation") or {}
    return MinerOutput(**best)


def prepare_state(payload: MinerInput) -> MinerState:
    return {
        "search_console_rows": payload.search_console_rows,
        "site_pages": payload.site_pages,
    }


def build_graph() -> StateGraph:
    graph = StateGraph(MinerState)
    graph.add_node("analyze", analyze)
    graph.add_node("decide", decide)
    graph.add_node("summarize", summarize)

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "decide")
    graph.add_edge("decide", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()
