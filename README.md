# Trendly Agentic Customer Support Assistant

An agentic customer-support backend built with **Python, FastAPI, Groq LLMs, and tool calling**.

The assistant can handle order tracking, policy questions, return/exchange eligibility, return/exchange creation, and human escalation while enforcing customer-level data isolation and deterministic business rules.

---

## Features

- Customer-authenticated sessions
- Order tracking and status explanations
- Customer-level order access control
- Policy-grounded responses
- Return/exchange eligibility evaluation
- Return request creation
- Size-exchange request creation
- Final-sale enforcement
- Lost-parcel escalation
- COD refund escalation
- Multi-turn conversation history
- Human escalation workflow
- LLM-based tool orchestration
- Deterministic business rules for critical operations

---

## Architecture

```text
                        ┌──────────────────┐
                        │      Client      │
                        │ Swagger / API    │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │     FastAPI      │
                        │   REST API       │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │      Agent       │
                        │                  │
                        │  Groq LLM        │
                        │  Tool Calling    │
                        └────────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
             ┌──────────────┐         ┌──────────────┐
             │ TrendlyTools │         │ Conversation │
             │              │         │    State     │
             └──────┬───────┘         └──────────────┘
                    │
       ┌────────────┼────────────┬──────────────┐
       │            │            │              │
       ▼            ▼            ▼              ▼
   Customer      Order       Policy        Return/Exchange
   Lookup        Lookup      Search        Evaluation
                                               │
                                      ┌────────┴────────┐
                                      │                 │
                                      ▼                 ▼
                                  Return            Exchange
                                  Creation          Creation
                                      │
                                      ▼
                                  Escalation
```

The LLM acts as an **orchestrator**. It decides which tool should be used and in what sequence.

Critical business logic is handled by deterministic application tools instead of relying on the LLM to invent or calculate business decisions.

---

## Tech Stack

- **Python 3.12**
- **FastAPI**
- **Uvicorn**
- **Groq API**
- **OpenAI Python SDK**
- **Pydantic**
- **SQLite**
- **JSON**
- **LLM Function/Tool Calling**

---

## Project Structure

```text
trendly-agent/
│
├── app/
│   ├── main.py
│   ├── agent.py
│   ├── tools.py
│   ├── policy.py
│   ├── state.py
│   └── config.py
│
├── data/
│   ├── orders.json
│   └── policy.md
│
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── PROMPTS.md
└── SOLUTION.md
```

---

# Getting Started

## Prerequisites

Make sure you have:

- Python 3.12+
- A Groq API key
- Git

Docker is **not required** to run this project.

---

## 1. Clone the repository

```bash
git clone https://github.com/mdzaid111/trendly-agent.git 
cd trendly-agent
```

---

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-20b
```

Do **not** commit your actual API key to GitHub.

The repository should contain `.env.example`, but not `.env`.

---

# Running the Application

Start the server with:

```bash
uvicorn app.main:app --reload
```

The application will start at:

```text
http://127.0.0.1:8000
```

The API is accessible through Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

# API Endpoints

## Health Check

```http
GET /health
```

Example:

```bash
curl http://127.0.0.1:8000/health
```

Example response:

```json
{
  "status": "ok",
  "llm_configured": true,
  "model": "openai/gpt-oss-20b"
}
```

---

## Create Session

```http
POST /sessions
```

Request:

```json
{
  "customer_id": "C-101"
}
```

Example response:

```json
{
  "session_id": "generated-session-id",
  "customer_id": "C-101"
}
```

The session associates the conversation with an authenticated customer.

---

## Chat

```http
POST /chat
```

Request:

```json
{
  "session_id": "generated-session-id",
  "message": "Where is my order TR-4530?"
}
```

Example response:

```json
{
  "session_id": "generated-session-id",
  "response": "Your order TR-4530 was delivered on 26 July 2026 at 11:00 AM..."
}
```

---

## Conversation History

```http
GET /sessions/{session_id}/history
```

Returns the stored conversation history for the session.

---

# Example Workflow

## 1. Order Tracking

A customer can ask:

```text
Where is my order TR-4530?
```

The agent uses:

```text
lookup_order
```

The tool verifies that the order belongs to the authenticated customer before returning order information.

Example:

```text
Customer: C-101
Order: TR-4530
```

The order data is retrieved from the application's order data rather than generated by the LLM.

---

# Return Workflow

A return request follows a controlled sequence:

```text
Customer requests return
        │
        ▼
Identify order
        │
        ▼
Identify SKU
        │
        ▼
Confirm item condition
        │
        ▼
Identify return reason
        │
        ▼
Evaluate eligibility
        │
        ├──── Not eligible
        │          │
        │          ▼
        │     Explain reason
        │
        ▼
Create return
        │
        ▼
Return confirmation
```

The agent must run:

```text
evaluate_return_exchange
```

before:

```text
create_return
```

This prevents a return from being created without an eligibility check.

---

# Exchange Workflow

Exchanges are restricted to **size exchanges**.

The requested size must be supplied before creating the exchange.

The workflow is:

```text
Customer requests exchange
        │
        ▼
Identify order + SKU
        │
        ▼
Confirm item condition
        │
        ▼
Evaluate exchange eligibility
        │
        ▼
Collect requested size
        │
        ▼
Create exchange request
```

The exchange is recorded as pending size availability.

---

# Policy Handling

Policy-related questions are grounded using:

```text
policy_search
```

Examples include:

- Return window
- Non-returnable categories
- Final-sale rules
- Footwear return conditions
- Damaged-item rules
- Exchange rules

The LLM should not invent policy information when the policy document does not contain the answer.

---

# Security and Data Isolation

Each session is associated with a customer ID.

For example:

```text
Session customer: C-101
Requested order: TR-4528
Order owner: C-103
```

The order lookup rejects the request because the order does not belong to the authenticated customer.

This prevents one customer from accessing another customer's order data.

---

# Important Business Rules

The following rules are enforced by the application:

### Customer isolation

A customer can access only orders associated with their session.

### Order data

Order facts are retrieved from the order tools.

The LLM is not allowed to invent order information.

### Final-sale products

Final-sale products allow **size exchange only**.

They do not qualify for:

- Refund
- Store credit
- Standard return

### Lost parcels

Lost parcels are treated as escalation cases rather than returns.

### COD refunds

Bank details are not collected through chat.

Cases requiring bank details are escalated to a human.

### Return eligibility

Return/exchange eligibility is evaluated before creating a return or exchange.

### Damaged / defective / wrong items

These cases require photograph confirmation and must satisfy the applicable policy time window.

---

# Agent Architecture

The main agent is implemented in:

```text
app/agent.py
```

The agent uses the Groq-compatible OpenAI SDK interface for tool calling.

Available tools include:

```text
lookup_customer
lookup_order
policy_search
evaluate_return_exchange
create_return
create_exchange
escalate
```

The agent follows a loop similar to:

```text
User Message
     │
     ▼
LLM
     │
     ├── Normal response ──► User
     │
     └── Tool call
             │
             ▼
          Tool
             │
             ▼
        Tool result
             │
             ▼
            LLM
             │
             ▼
       Final response
```

The agent supports multiple tool calls within a single request when required.

---

# Conversation State

Conversation state is persisted using SQLite.

This allows multi-turn interactions such as:

```text
User:
I want to return something.

Assistant:
Sure. Please provide the order ID.

User:
TR-4530.

Assistant:
Which item would you like to return?

User:
TR-KRT-033.

Assistant:
Please confirm the item is unworn, unwashed...
```

The previous messages are loaded into the agent context for subsequent turns.

---

# Testing

Swagger provides an easy way to test the application.

Open:

```text
http://127.0.0.1:8000/docs
```

Recommended test scenarios are listed below.

---

## Test 1 — Happy Path

Create a session:

```json
{
  "customer_id": "C-101"
}
```

Then call `/chat`:

```json
{
  "session_id": "<SESSION_ID>",
  "message": "Where is my order TR-4530?"
}
```

Expected behavior:

```text
Order TR-4530 is retrieved.
Customer ownership is verified.
The assistant returns the actual order status.
```

---

## Test 2 — Customer Access Control

Create a session for:

```text
C-101
```

Then request:

```text
Where is my order TR-4528?
```

Expected behavior:

```text
The order belongs to another customer.
The assistant must not reveal its details.
```

---

## Test 3 — Final-Sale Edge Case

Order:

```text
TR-4528
```

SKU:

```text
TR-SHR-009
```

The product is marked:

```text
final_sale: true
```

Ask:

```text
I want a refund for TR-4528.
```

Expected behavior:

```text
The refund is rejected because the item is final-sale.
Only a size exchange is allowed.
```

---

## Test 4 — Policy Question

Ask:

```text
What is your return policy?
```

Expected behavior:

```text
The agent calls policy_search and provides a policy-grounded answer.
```

---

## Test 5 — Return Eligibility

Ask:

```text
I want to return TR-4530.
```

The agent should request the required information before evaluating eligibility.

The eligibility tool should run before a return is created.

---

## Test 6 — Lost Parcel

Ask about an order with:

```text
lost_in_transit
```

Expected behavior:

```text
The case is escalated to a human.
It is not treated as a normal return.
```

---

# AI Usage

AI was used for **natural-language understanding and agent orchestration**.

The LLM is responsible for:

- Understanding user intent
- Selecting appropriate tools
- Determining the required tool sequence
- Asking for missing information
- Maintaining natural conversation
- Generating the final user-facing response

The LLM is **not** treated as the source of truth for critical business information.

Deterministic application tools handle:

- Customer authentication
- Order ownership
- Order data
- Policy retrieval
- Return eligibility
- Exchange eligibility
- Final-sale restrictions
- Return creation
- Exchange creation
- Human escalation

The system prompt and tool definitions were iterated during development to improve:

- Tool selection
- Customer-data isolation
- Policy compliance
- Return/exchange sequencing
- Clarification behavior
- Prevention of hallucinated order information

Detailed prompt iterations are documented in:

```text
PROMPTS.md
```

---

# Configuration

The application reads configuration from environment variables.

Example:

```env
GROQ_API_KEY=your_api_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-20b
```

The Groq model can be changed through:

```text
GROQ_MODEL
```

without changing the application code.

---

# Known Limitations

This project is designed as an assessment prototype rather than a production customer-support system.

Known limitations include:

1. Order data is currently stored in JSON rather than a production database.
2. Customer authentication is session/customer-ID based rather than a production authentication system.
3. Exchange requests do not connect to a real inventory system.
4. Human escalation creates an internal escalation record but does not connect to a real ticketing platform.
5. The system requires an external Groq API key for LLM functionality.
6. The current application does not provide a production deployment or authentication layer.
7. The current state store is designed for the assessment environment and would need further hardening for production-scale concurrency.

---

# Project Files

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI application and API endpoints |
| `app/agent.py` | LLM agent and tool orchestration |
| `app/tools.py` | Business tools and deterministic rules |
| `app/policy.py` | Policy retrieval |
| `app/state.py` | Session and conversation persistence |
| `app/config.py` | Application configuration |
| `PROMPTS.md` | Prompt design and iteration history |
| `SOLUTION.md` | Architecture, trade-offs, limitations and discovery questions |
| `data/orders.json` | Sample customer and order data |
| `data/policy.md` | Trendly policy document |

---

# Running in One Command

After environment setup, the application can be started with:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

---

# Submission Deliverables

This repository contains the following assessment deliverables:

```text
README.md
PROMPTS.md
SOLUTION.md
```

The README documents setup, architecture, API usage, testing, and AI usage.

`PROMPTS.md` documents the system prompt, tool instructions, and prompt iterations.

`SOLUTION.md` documents architecture decisions, trade-offs, known limitations, and discovery questions for Trendly's operations team.

---

# Author

**Md Zaid**

Trendly Agentic Customer Support Assistant