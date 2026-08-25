# Prompt Engineering Notes

## System prompt

The production system prompt is in `app/agent.py` as `SYSTEM_PROMPT`.

Its structure is deliberate:

1. **Role + objective** — defines the assistant as a support orchestrator.
2. **Non-negotiable rules** — authorization, policy grounding, tool ordering, privacy, refusal boundaries, and side-effect confirmation.
3. **Status guidance** — maps the fixed dataset's status states to customer-friendly explanations.
4. **Return/exchange guidance** — tells the model which facts it must collect before calling deterministic tools.

The model is explicitly told that it is an orchestrator and that tools, not prose, determine facts and side effects.

## Tool strategy

| Tool | Why it exists | Main guardrail |
|---|---|---|
| `lookup_customer` | Validate session customer | Unknown customer rejected |
| `lookup_order` | Retrieve order facts/status | Ownership checked server-side |
| `policy_search` | Ground policy answers | Returns `grounded=false` when silent |
| `evaluate_return_exchange` | Deterministic policy decision | Delivery/category/final-sale/cancelled checks |
| `create_return` | Side effect | Requires prior eligibility check |
| `create_exchange` | Side effect | Requires prior eligibility + requested size |
| `escalate` | Human handoff | Creates audit record + summary |

## Prompt iteration

### Iteration 1 — generic support prompt

Initial behavior was too permissive: an LLM can sound confident even when a policy question is not covered.

### Iteration 2 — explicit source-of-truth rule

Added: policy questions must call `policy_search`, and unsupported policy questions must be routed to a human.

### Iteration 3 — tool-owned authorization

Prompt-only privacy rules are insufficient. The customer id is now attached to the session and injected by the server into tool calls, so the model cannot use another customer id to bypass ownership checks.

### Iteration 4 — side-effect gating

Added a deterministic eligibility tool before create tools. Create tools reject calls without a matching prior evaluation.

### Iteration 5 — missing-information handling

Added explicit confirmation for return condition, photographs for damaged/wrong-item claims, and requested size for exchanges. The model must ask instead of assuming.

### Iteration 6 — inventory uncertainty

No inventory source exists in the assignment. The agent therefore does not hallucinate availability. It records an exchange as pending size availability and surfaces the limitation.

## Prompt invariants

- Never invent order data.
- Never reveal a different customer's order.
- Never answer policy questions from general knowledge.
- Never create a return/exchange without eligibility evaluation.
- Never collect bank/card/CVV information.
- Never offer an unlisted discount or goodwill credit.
- Never call a lost parcel a return.
- Never claim a side effect succeeded without a successful tool result.
