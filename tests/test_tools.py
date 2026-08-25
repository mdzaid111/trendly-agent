import tempfile
from pathlib import Path
from app.policy import Policy
from app.state import StateStore
from app.tools import TrendlyTools

ROOT=Path(__file__).resolve().parents[1]
ORDERS=ROOT/"data/orders.json"
POLICY=Policy(str(ROOT/"data/trendly_policy.md"))

def make_tools():
    db=tempfile.NamedTemporaryFile(delete=False).name
    state=StateStore(db)
    t=TrendlyTools(str(ORDERS),POLICY,state)
    sid=state.create_session("C-100"); t.set_session(sid)
    return t

def test_order_status_edge_cases():
    t=make_tools()
    assert t.lookup_order("C-100","TR-4521")["status"]=="in_transit"
    assert t.lookup_order("C-100","TR-4524")["status"]=="partially_shipped"
    assert t.lookup_order("C-103","TR-4525")["status"]=="delayed"
    assert t.lookup_order("C-101","TR-4526")["status"]=="lost_in_transit"
    assert t.lookup_order("C-100","TR-4529")["status"]=="cancelled"

def test_cross_customer_order_denied():
    t=make_tools()
    assert t.lookup_order("C-100","TR-4522")["error"]=="order_access_denied"

def test_return_rules():
    t=make_tools()
    # Assignment snapshot: evaluated against 2026-08-18 so the fixed dataset notes remain consistent
    x=t.evaluate_return_exchange("C-101","TR-4530","TR-KRT-033","return","change_of_mind",condition_ok=True)
    assert x["eligible"] is True
    old=t.evaluate_return_exchange("C-102","TR-4523","TR-JKT-008","return","change_of_mind",condition_ok=True)
    assert old["reason_code"]=="outside_30_days"
    jewellery=t.evaluate_return_exchange("C-102","TR-4527","TR-EAR-042","return","change_of_mind",condition_ok=True)
    assert jewellery["reason_code"]=="non_returnable_category"
    final_sale=t.evaluate_return_exchange("C-103","TR-4528","TR-SHR-009","return","change_of_mind",condition_ok=True)
    assert final_sale["reason_code"]=="final_sale_no_refund"
    exchange=t.evaluate_return_exchange("C-103","TR-4528","TR-SHR-009","exchange",condition_ok=True)
    assert exchange["allowed_action"]=="exchange_size_only"

def test_cancelled_and_lost_are_not_returns():
    t=make_tools()
    c=t.evaluate_return_exchange("C-100","TR-4529","TR-SCF-027","return","change_of_mind",condition_ok=True)
    assert c["reason_code"]=="cancelled_order"
    lost=t.lookup_order("C-101","TR-4526")
    assert lost["status"]=="lost_in_transit"

def test_policy_silence():
    t=make_tools()
    r=t.policy_search("Can I get a free personal stylist?")
    assert r["grounded"] is False

def test_creation_requires_evaluation():
    t=make_tools()
    r=t.create_return("C-101","TR-4530","TR-KRT-033")
    assert r["error"]=="eligibility_check_required"

def test_return_action_is_created_after_evaluation():
    t=make_tools()
    t.evaluate_return_exchange("C-101","TR-4530","TR-KRT-033","return","change_of_mind",condition_ok=True)
    r=t.create_return("C-101","TR-4530","TR-KRT-033","change_of_mind",condition_ok=True)
    assert r["created"] is True
    assert r["action_id"].startswith("ACT-")
