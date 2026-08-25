from pathlib import Path
import tempfile
from types import SimpleNamespace
from app.agent import Agent
from app.policy import Policy
from app.state import StateStore
from app.tools import TrendlyTools

ROOT=Path(__file__).resolve().parents[1]

class FakeCompletions:
    def __init__(self): self.calls=0
    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            tc=SimpleNamespace(id="tc1", function=SimpleNamespace(name="lookup_order",
                    arguments='{"customer_id":"C-100","order_id":"TR-4521"}'))
            msg=SimpleNamespace(content=None, tool_calls=[tc])
        else:
            msg=SimpleNamespace(content="Order TR-4521 is in transit with BlueDart. It is expected by July 31.", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

class FakeClient:
    def __init__(self): self.chat=SimpleNamespace(completions=FakeCompletions())

def test_real_tool_call_loop_and_state():
    db=tempfile.NamedTemporaryFile(delete=False).name
    state=StateStore(db)
    policy=Policy(str(ROOT/"data/trendly_policy.md"))
    tools=TrendlyTools(str(ROOT/"data/orders.json"),policy,state)
    sid=state.create_session("C-100")
    agent=Agent(FakeClient(),"fake",tools)
    answer=agent.run(sid,"C-100","Where is TR-4521?")
    assert "in transit" in answer
    history=state.history(sid)
    assert any(x.get("tool_name")=="lookup_order" for x in history)
