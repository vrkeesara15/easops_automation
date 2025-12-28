# Daily Site Improvement Planner

Determines the single highest-impact website improvement to ship today based on current metrics, the active backlog, and delivery constraints. The agent runs deterministically through an analyze → decide → summarize LangGraph flow.

## Inputs
- `metrics` (string): GA4/Search Console summary.
- `backlog` (array): Ideas as strings or structured backlog items.
- `constraints` (object): Delivery guardrails (time, risk tolerance, and whether design/code work is allowed).

## Outputs
- `selected_task`: One task selected for today.
- `reason`: Why this task was chosen.
- `expected_impact`: Anticipated benefit.
- `acceptance_criteria`: Checklist to validate completion.
- `rollback_plan`: Steps to revert if needed.

## How it works
1. Analyze metrics to set a focus category (conversion/performance/SEO/reliability).
2. Score backlog items against the focus and constraints.
3. Pick the top candidate (or a default quick win if no backlog exists).
4. Return structured output for n8n logging and orchestration.
