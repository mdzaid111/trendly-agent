import json
from datetime import date,datetime
from pathlib import Path
from .config import settings

class TrendlyTools:
    def __init__(self,orders_path,policy,state):
        data=json.loads(Path(orders_path).read_text(encoding="utf-8"))
        self.customers={x["customer_id"]:x for x in data["customers"]}
        self.orders={x["order_id"]:x for x in data["orders"]}
        self.policy,self.state=policy,state
        self.session_id="SYSTEM"
        self.evaluations = set()

    def set_session(self,sid): self.session_id=sid

    def _owned(self,cid,oid):
        o=self.orders.get(oid)
        if not o: return None,{"ok":False,"error":"order_not_found"}
        if o["customer_id"]!=cid:
            return None,{"ok":False,"error":"order_access_denied","message":"That order does not belong to the authenticated customer."}
        return o,None

    def lookup_customer(self,cid):
        c=self.customers.get(cid)
        return {"ok":True,"customer_id":cid,"name":c["name"]} if c else {"ok":False,"error":"customer_not_found"}

    def lookup_order(self,cid,oid):
        o,e=self._owned(cid,oid)
        if e:return e
        s=o["status"]
        explanations={
          "in_transit":"The order has been dispatched and is currently in transit.",
          "delivered":"The order has been delivered.",
          "delayed":"The order is delayed beyond its expected delivery date and qualifies for the policy's ₹250 store credit on request.",
          "lost_in_transit":"The carrier has marked this parcel lost. This is a lost-parcel claim, not a return, and must be handled by a human.",
          "cancelled":"The order was cancelled and its refund is already processed. A return cannot be raised against a cancelled order.",
          "partially_shipped":"Part of the order has shipped; the backordered item has not shipped yet and has its own ETA."
        }
        return {"ok":True,"order_id":oid,"status":s,"placed_at":o["placed_at"],"delivered_at":o["delivered_at"],
          "expected_delivery":o["expected_delivery"],"carrier":o["carrier"],"tracking_number":o["tracking_number"],
          "shipping_city":o["shipping_city"],"items":o["items"],"total":o["total"],
          "explanation":explanations.get(s,f"The order status is {s}.")}

    def policy_search(self,query,section=None):
        hits=self.policy.search(query,section)
        return {"ok":True,"grounded":True,"results":hits} if hits else {
          "ok":False,"grounded":False,"message":"The policy document does not cover this question. Say you do not know and offer a human agent."}

    def evaluate_return_exchange(self,cid,oid,sku,action,reason=None,has_photos=False,condition_ok=False):
        o,e=self._owned(cid,oid)
        if e:return e
        item=next((x for x in o["items"] if x["sku"]==sku),None)
        if not item:return {"ok":False,"error":"sku_not_found"}
        if o["status"]=="cancelled":
            return {"ok":True,"eligible":False,"reason_code":"cancelled_order","explanation":"Cancelled orders cannot have returns raised."}
        if o["status"]!="delivered" or not o["delivered_at"]:
            return {"ok":True,"eligible":False,"reason_code":"not_delivered","explanation":"Returns/exchanges use the delivery date; this item is not currently eligible."}
        delivered=datetime.fromisoformat(o["delivered_at"].replace("Z","+00:00")).date()
        days=(date.fromisoformat(settings.as_of_date)-delivered).days
        if days>30:
            return {"ok":True,"eligible":False,"reason_code":"outside_30_days","days_since_delivery":days,
                    "explanation":"The 30-calendar-day return/exchange window has expired."}
        if item["category"] in {"innerwear","socks","jewellery","beauty","fragrance","face_masks","gift_cards"}:
            return {"ok":True,"eligible":False,"reason_code":"non_returnable_category",
                    "explanation":"This category is non-returnable and non-exchangeable under the policy."}
        if action not in {"return","exchange"}: return {"ok":False,"error":"invalid_action"}
        if not condition_ok:
            return {"ok":True,"eligible":False,"reason_code":"condition_confirmation_required",
                    "explanation":"Customer must confirm the item is unworn, unwashed, and has original tags and original packaging where provided."}
        if action=="exchange":
            if item.get("final_sale"):
                return {"ok":True,"eligible":True,"allowed_action":"exchange_size_only",
                        "reason_code":"final_sale_size_exchange_only","explanation":"Final-sale items allow size exchange only; no refund or store credit."}
            return {"ok":True,"eligible":True,"allowed_action":"exchange_size_only",
                    "reason_code":"eligible_size_exchange","explanation":"Eligible for one size exchange, subject to requested-size availability."}
        if item.get("final_sale"):
            return {"ok":True,"eligible":False,"reason_code":"final_sale_no_refund","explanation":"Final-sale items do not qualify for refund or store credit."}
        if reason in {"damaged","defective","wrong_item"}:
            if days > 2:
                return {"ok":True,"eligible":False,"reason_code":"damaged_report_window_expired",
                        "days_since_delivery":days,
                        "explanation":"Damaged, defective, or incorrect items must be reported within 48 hours of delivery."}
            if not has_photos:
                return {"ok":True,"eligible":False,"reason_code":"photos_required",
                        "explanation":"Photographs are required for damaged, defective, or incorrect item reports."}
            result={"ok":True,"eligible":True,"allowed_action":"return_or_refund","reason_code":"damaged_wrong_special_flow",
                    "explanation":"Eligible for the damaged/wrong-item resolution with photographs within 48 hours."}
        else:
            result={"ok":True,"eligible":True,"allowed_action":"return","reason_code":"eligible_standard_return",
                    "explanation":"The item is within the return window and its category is returnable, subject to the condition requirements in policy."}
        self.evaluations.add((self.session_id,cid,oid,sku,action,reason or "",bool(has_photos),bool(condition_ok)))
        return result

    def create_return(self,cid,oid,sku,reason=None,has_photos=False,condition_ok=False):
        key=(self.session_id,cid,oid,sku,"return",reason or "",bool(has_photos),bool(condition_ok))
        if key not in self.evaluations:
            return {"ok":False,"created":False,"error":"eligibility_check_required",
                    "message":"Run the eligibility check before creating the return."}
        check=self.evaluate_return_exchange(cid,oid,sku,"return",reason,has_photos,condition_ok)
        if not check.get("eligible"):return {"ok":False,"created":False,"eligibility":check}
        aid=self.state.record_action(self.session_id,cid,"return",oid,sku,"created",{"reason":reason,"decision":check})
        return {"ok":True,"created":True,"action_id":aid,"message":"Return request created. Pickup scheduling can be completed next."}

    def create_exchange(self,cid,oid,sku,requested_size,condition_ok=False):
        key=(self.session_id,cid,oid,sku,"exchange","",False,bool(condition_ok))
        if key not in self.evaluations:
            return {"ok":False,"created":False,"error":"eligibility_check_required",
                    "message":"Run the eligibility check before creating the exchange."}
        check=self.evaluate_return_exchange(cid,oid,sku,"exchange",condition_ok=condition_ok)
        if not check.get("eligible"):return {"ok":False,"created":False,"eligibility":check}
        if not requested_size.strip():return {"ok":False,"error":"requested_size_required"}
        aid=self.state.record_action(self.session_id,cid,"exchange",oid,sku,"pending_size_availability",
                                      {"requested_size":requested_size,"decision":check})
        return {"ok":True,"created":True,"action_id":aid,"status":"pending_size_availability",
                "message":"Exchange request created pending requested-size availability. If unavailable, policy converts it to a refund."}

    def escalate(self,cid,issue,oid=None,reason="human_review_required"):
        context=None
        if oid:
            o,e=self._owned(cid,oid)
            if e:return e
            context={"order_id":oid,"status":o["status"],"items":o["items"],"expected_delivery":o["expected_delivery"]}
        aid=self.state.record_action(self.session_id,cid,"escalation",oid,None,"queued",
                                     {"issue":issue,"reason":reason,"order_context":context})
        summary=f"Customer {cid} needs human support. Issue: {issue}."
        if context:summary+=f" Order {oid} status: {context['status']}."
        return {"ok":True,"escalated":True,"action_id":aid,"summary":summary,
                "support_hours":"09:00-21:00 IST, seven days a week."}
