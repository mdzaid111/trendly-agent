# Trendly Agent — Solution Note

## Architecture

The solution uses a thin FastAPI API, a persistent SQLite state/audit layer, an OpenAI-compatible LLM client, and deterministic business tools. The model performs orchestration through function calling. It decides whether to look up an order, retrieve policy, evaluate eligibility, create an action, or escalate. The backend owns customer authorization, policy evaluation, and side effects.

The two supplied artifacts are treated as immutable source data: `orders.json` is loaded exactly as provided and `trendly_policy.md` is the only policy source. This directly matches the assignment's requirement that the policy document is the only source of truth and the ten orders are fixed. fileciteturn0file2L28-L30

## Orchestration and state

A session has an authenticated customer id and a durable message history. On each turn, the agent receives the prior conversation plus the new user message. Tool calls are executed in a bounded loop (maximum eight model turns) so failures cannot create an unbounded agent loop.

The order lookup tool handles all supplied edge statuses: in-transit, delivered, partially shipped, delayed, lost in transit, and cancelled. The fixed dataset itself calls out that lost parcels must be escalated, that jewellery is non-returnable despite being within the window, that final-sale items are exchange-only, and that the cancelled order has already been refunded. fileciteturn0file0L78-L109 fileciteturn0file0L112-L161

Return/exchange flow is deliberately two-step: evaluate first, then create. The evaluator combines delivery date, category, final-sale status, cancellation state, reason, condition confirmation, and damaged-item reporting requirements. Create tools reject calls that have not passed evaluation and write an audit action id to SQLite.

## Prompting and guardrails

The prompt makes the LLM an orchestrator rather than a source of truth. Policy questions go through `policy_search`. If policy retrieval is silent, the agent says it does not know and offers human support, matching section 7. The policy also explicitly prohibits discounts, collection of bank/card/CVV data, cross-customer order discussion, and invented policy; these are implemented as prompt rules plus backend constraints. fileciteturn0file1L96-L106

The strongest security boundary is not the prompt: the server associates a session with one customer id and overwrites model-supplied customer ids before tool execution. Thus an LLM cannot use a prompt injection to fetch another customer's order.

## Key trade-offs

**LLM vs. rules:** The LLM is useful for intent interpretation, clarification, sequencing, and natural-language responses. Rules are better for authorization and policy decisions. This hybrid avoids both brittle keyword routing and hallucinated business logic.

**SQLite vs. external state service:** SQLite keeps the one-command demo simple and durable enough for an assignment. A production deployment would use a managed relational database or support platform state store.

**Policy search vs. embedding RAG:** The policy is small and sectioned. Lightweight lexical retrieval is deterministic and auditable for this assignment. Production scale could add embeddings, but the retrieved text should still be traceable to policy sections.

**Inventory:** The provided data contains no size inventory. The agent therefore refuses to invent availability and records an exchange as pending availability. A real deployment needs an inventory tool; policy says an unavailable exchange converts to a refund. fileciteturn0file1L68-L74

## Known limitations

1. No live carrier API is provided, so tracking status is limited to the fixed order dataset.
2. No inventory API is provided, so requested-size availability cannot be determined.
3. Return condition is collected as a customer confirmation rather than validated from an image or warehouse system.
4. The assignment's fixed data does not include a recently delivered damaged/wrong item, so that path is guarded and testable but not represented by a concrete fixture.
5. Human escalation is recorded locally rather than integrated with a ticketing platform.
6. The demo requires a free-tier LLM API key; the repository cannot supply credentials.

## Five discovery questions for Trendly Ops

1. **Identity:** What authentication/customer verification signal is available in the production chat channel before an order can be discussed?
2. **Systems:** Which OMS/WMS/carrier APIs are authoritative for order state, shipment events, return creation, and inventory?
3. **Returns:** What exact workflow/ticket states should be created for standard returns, exchanges, damaged items, and lost parcels?
4. **Human handoff:** Which helpdesk should receive escalations, what fields are mandatory, and what SLA/priority rules should apply?
5. **Exceptions:** Who is authorized to approve policy exceptions, and how should approved discounts/credits be represented so the agent cannot invent them?
