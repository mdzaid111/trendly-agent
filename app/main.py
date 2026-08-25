from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI
from .config import settings
from .policy import Policy
from .state import StateStore
from .tools import TrendlyTools
from .agent import Agent

app=FastAPI(title="Trendly Agentic Support Assistant",version="1.0.0")
state=StateStore(settings.db_path)
policy=Policy(settings.policy_path)
tools=TrendlyTools(settings.orders_path,policy,state)
client=OpenAI(api_key=settings.groq_api_key,base_url=settings.groq_base_url) if settings.groq_api_key else None
agent=Agent(client,settings.groq_model,tools) if client else None

class SessionIn(BaseModel):
    customer_id: str=Field(pattern=r"^C-\d+$")

class ChatIn(BaseModel):
    session_id: str
    message: str=Field(min_length=1,max_length=4000)

@app.get("/health")
def health():
    return {"status":"ok","llm_configured":bool(client),"model":settings.groq_model}

@app.post("/sessions")
def create_session(body:SessionIn):
    if not tools.lookup_customer(body.customer_id).get("ok"): raise HTTPException(404,"Unknown customer")
    return {"session_id":state.create_session(body.customer_id),"customer_id":body.customer_id}

@app.post("/chat")
def chat(body:ChatIn):
    s=state.get_session(body.session_id)
    if not s: raise HTTPException(404,"Unknown session")
    if not s["customer_id"]: raise HTTPException(400,"Session has no authenticated customer")
    if not agent: raise HTTPException(503,"LLM is not configured. Set GROQ_API_KEY.")
    return {"session_id":body.session_id,"response":agent.run(body.session_id,s["customer_id"],body.message)}

@app.get("/sessions/{session_id}/history")
def history(session_id:str):
    if not state.get_session(session_id): raise HTTPException(404,"Unknown session")
    return {"messages":state.history(session_id)}
