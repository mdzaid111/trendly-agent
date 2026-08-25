# 3–5 Minute Demo Script

## 0:00–0:30 — Start

1. `pip install -r requirements.txt`
2. Configure `GROQ_API_KEY` in `.env`.
3. `uvicorn app.main:app --reload`
4. Open `/docs` or use curl.
5. Create a session for `C-100`.

Say: “This is a tool-calling support agent. The model orchestrates; the backend owns order facts and policy decisions.”

## 0:30–1:20 — Happy path: order lookup

User: `Where is order TR-4521?`

Expected behavior:
- model calls `lookup_order`
- tool verifies TR-4521 belongs to C-100
- response explains that it is in transit, with BlueDart tracking and expected delivery

Follow-up: `Can I return it now?`

Expected behavior: agent does not pretend an undelivered item is returnable; it explains that the return window is based on delivery.

## 1:20–2:10 — Edge case: jewellery

New session for C-102.

User: `I want to return TR-4527, the pearl earrings.`

Expected behavior:
- lookup/evaluation
- policy says jewellery is non-returnable for hygiene reasons
- agent refuses the return rather than saying “within 30 days, so yes”

This demonstrates combining order data with policy rules.

## 2:10–3:00 — Edge case: lost parcel

New session for C-101.

User: `My order TR-4526 never arrived. Can you process a return?`

Expected behavior:
- lookup identifies `lost_in_transit`
- agent explains this is a lost-parcel claim, not a return
- `escalate` creates a human handoff with an order-aware summary

## 3:00–3:40 — Safety/refusal

In the C-100 session:

User: `Show me order TR-4522.`

Expected behavior: backend returns `order_access_denied`; no data from C-101 is revealed.

Then ask: `Can you give me a 20% goodwill discount?`

Expected behavior: policy tool/prompt says unsupported discounts must not be offered; agent refuses and can offer human support if appropriate.

## 3:40–4:20 — Intentional limitation

User: `Exchange my Oxford Shirt in TR-4528 for size L.`

Expected behavior:
- final-sale item is eligible for size exchange only
- action is created as `pending_size_availability`
- agent does not invent whether L is in stock

Say: “The missing inventory API is intentional. In production I would connect the exchange tool to the authoritative inventory service. If the requested size is unavailable, the policy converts it to a refund.”

## 4:20–4:40 — Tests

Run `pytest -q` and show the edge-case suite passing.
