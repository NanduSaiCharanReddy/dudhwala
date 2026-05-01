"""
DudhWala — Milk Delivery Management System
Full Stack: FastAPI + PostgreSQL + Serves Frontend
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date, timedelta
from typing import Optional
import random, string, os

# ════════════════════════════════════════════════════
#  DATABASE
#  Set DATABASE_URL in environment or .env file
#  Local PostgreSQL: postgresql://postgres:w00lTe$t90@localhost:5432/dudhwala
#  Railway/Supabase: set DATABASE_URL env variable automatically
# ════════════════════════════════════════════════════
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:w00lTe$t90@localhost:5432/dudhwala"
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ════════════════════════════════════════════════════
#  MODELS
# ════════════════════════════════════════════════════
class Vendor(Base):
    __tablename__ = "vendors"
    id         = Column(String, primary_key=True)
    name       = Column(String)
    phone      = Column(String, unique=True, index=True)
    shop_name  = Column(String)
    address    = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class Milkman(Base):
    __tablename__ = "milkmen"
    id          = Column(String, primary_key=True)
    name        = Column(String)
    phone       = Column(String, unique=True, index=True)
    vendor_id   = Column(String, index=True, default="")
    unique_code = Column(String, unique=True, index=True)
    active      = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    id             = Column(String, primary_key=True)
    name           = Column(String)
    phone          = Column(String, unique=True, index=True)
    vendor_id      = Column(String, index=True, default="")
    milkman_id     = Column(String, index=True, default="")
    daily_litres   = Column(Float, default=1.0)
    rate_per_litre = Column(Float, default=60.0)
    address        = Column(String, default="")
    active         = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

class Delivery(Base):
    __tablename__ = "deliveries"
    id          = Column(String, primary_key=True)
    date        = Column(String, index=True)
    customer_id = Column(String, index=True)
    milkman_id  = Column(String, index=True)
    vendor_id   = Column(String, index=True)
    litres      = Column(Float)
    created_at  = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id          = Column(String, primary_key=True)
    customer_id = Column(String, index=True)
    vendor_id   = Column(String, index=True)
    month       = Column(String)
    paid        = Column(Boolean, default=False)
    paid_at     = Column(DateTime, nullable=True)

class OTPStore(Base):
    __tablename__ = "otps"
    phone   = Column(String, primary_key=True)
    otp     = Column(String)
    expires = Column(DateTime)

Base.metadata.create_all(bind=engine)

# ════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════
def gen_id(prefix=""):
    return prefix + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def gen_code():
    return "MK" + ''.join(random.choices(string.digits, k=4))

def today_str():
    return date.today().strftime("%Y-%m-%d")

def this_month():
    return date.today().strftime("%Y-%m")

# ════════════════════════════════════════════════════
#  SCHEMAS
# ════════════════════════════════════════════════════
class SendOTPReq(BaseModel):
    phone: str
    name: str
    role: str
    vendor_code: Optional[str] = ""

class VerifyOTPReq(BaseModel):
    phone: str
    otp: str
    name: str
    role: str

class ShopUpdate(BaseModel):
    shop_name: str
    name: str
    address: str

class MilkmanAdd(BaseModel):
    name: str
    phone: str

class MilkmanLink(BaseModel):
    code: str

class CustomerAdd(BaseModel):
    name: str
    phone: str
    milkman_id: Optional[str] = ""
    daily_litres: float = 1.0
    rate_per_litre: float = 60.0
    address: str = ""

class CustomerPatch(BaseModel):
    milkman_id: Optional[str] = None
    rate_per_litre: Optional[float] = None
    daily_litres: Optional[float] = None

class DeliveryToggle(BaseModel):
    date: str
    customer_id: str
    vendor_id: str
    litres: float

class PaymentToggle(BaseModel):
    customer_id: str
    month: str

# ════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════
app = FastAPI(title="DudhWala API", version="1.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ── Serve frontend ────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h3>Place index.html inside static/ folder</h3>", 404)

# ── Health ────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

# ════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════
@app.post("/api/auth/send-otp")
def send_otp(req: SendOTPReq, db: Session = Depends(get_db)):
    # Milkman login via vendor code
    if req.role == "milkman" and req.vendor_code:
        mm = db.query(Milkman).filter(
            Milkman.unique_code == req.vendor_code.upper()
        ).first()
        if not mm:
            raise HTTPException(400, detail="INVALID_CODE")
        return {"success": True, "via_code": True, "user": {
            "id": mm.id, "name": mm.name, "phone": mm.phone,
            "role": "milkman", "vendorId": mm.vendor_id, "uniqueCode": mm.unique_code
        }}

    # Customer must be pre-registered by vendor
    if req.role == "customer":
        if not db.query(Customer).filter(Customer.phone == req.phone).first():
            raise HTTPException(403, detail="NOT_REGISTERED")

    # Save OTP (demo: always 1234 — plug in Twilio/MSG91 for real SMS)
    db.merge(OTPStore(
        phone=req.phone, otp="1234",
        expires=datetime.utcnow() + timedelta(minutes=10)
    ))
    db.commit()
    return {"success": True, "message": "OTP sent (demo: 1234)"}


@app.post("/api/auth/verify-otp")
def verify_otp(req: VerifyOTPReq, db: Session = Depends(get_db)):
    if req.otp != "1234":
        rec = db.query(OTPStore).filter(OTPStore.phone == req.phone).first()
        if not rec or rec.otp != req.otp or rec.expires < datetime.utcnow():
            raise HTTPException(400, detail="INVALID_OTP")

    if req.role == "vendor":
        user = db.query(Vendor).filter(Vendor.phone == req.phone).first()
        if not user:
            user = Vendor(id=gen_id("v_"), name=req.name, phone=req.phone,
                          shop_name=f"{req.name}'s Dairy", address="")
            db.add(user); db.commit(); db.refresh(user)
        return {"success": True, "user": {
            "id": user.id, "name": user.name, "phone": user.phone,
            "shopName": user.shop_name, "address": user.address, "role": "vendor"
        }}

    elif req.role == "milkman":
        user = db.query(Milkman).filter(Milkman.phone == req.phone).first()
        if not user:
            user = Milkman(id=gen_id("mm_"), name=req.name,
                           phone=req.phone, vendor_id="", unique_code=gen_code())
            db.add(user); db.commit(); db.refresh(user)
        return {"success": True, "user": {
            "id": user.id, "name": user.name, "phone": user.phone,
            "vendorId": user.vendor_id, "uniqueCode": user.unique_code, "role": "milkman"
        }}

    else:  # customer
        user = db.query(Customer).filter(Customer.phone == req.phone).first()
        if not user:
            raise HTTPException(403, detail="NOT_REGISTERED")
        return {"success": True, "user": {
            "id": user.id, "name": user.name, "phone": user.phone,
            "vendorId": user.vendor_id, "milkmanId": user.milkman_id,
            "dailyLitres": user.daily_litres, "ratePerLitre": user.rate_per_litre,
            "address": user.address, "role": "customer"
        }}

# ════════════════════════════════════════════════════
#  VENDOR
# ════════════════════════════════════════════════════
@app.get("/api/vendor/{vendor_id}/dashboard")
def vendor_dashboard(vendor_id: str, db: Session = Depends(get_db)):
    v = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not v: raise HTTPException(404)

    milkmen   = db.query(Milkman).filter(Milkman.vendor_id == vendor_id).all()
    customers = db.query(Customer).filter(Customer.vendor_id == vendor_id).all()
    cust_rate = {c.id: c.rate_per_litre for c in customers}

    today = today_str(); month = this_month()
    t_dels = db.query(Delivery).filter(Delivery.vendor_id == vendor_id, Delivery.date == today).all()
    m_dels = db.query(Delivery).filter(Delivery.vendor_id == vendor_id, Delivery.date.like(f"{month}%")).all()

    t_litres  = sum(d.litres for d in t_dels)
    m_litres  = sum(d.litres for d in m_dels)
    t_revenue = sum(d.litres * cust_rate.get(d.customer_id, 60) for d in t_dels)
    m_revenue = sum(d.litres * cust_rate.get(d.customer_id, 60) for d in m_dels)

    breakdown = []
    for m in milkmen:
        md = [d for d in t_dels if d.milkman_id == m.id]
        mc = [c for c in customers if c.milkman_id == m.id]
        breakdown.append({"name": m.name, "litres": sum(d.litres for d in md),
                           "done": len({d.customer_id for d in md}), "total": len(mc)})
    return {
        "vendor": {"id": v.id, "name": v.name, "shopName": v.shop_name, "address": v.address},
        "stats": {
            "milkmenCount": len(milkmen), "customerCount": len(customers),
            "todayLitres": round(t_litres, 2), "todayRevenue": round(t_revenue, 2),
            "monthLitres": round(m_litres, 2), "monthRevenue": round(m_revenue, 2),
        },
        "milkmanBreakdown": breakdown
    }

@app.put("/api/vendor/{vendor_id}/shop")
def update_shop(vendor_id: str, d: ShopUpdate, db: Session = Depends(get_db)):
    v = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not v: raise HTTPException(404)
    v.shop_name = d.shop_name; v.name = d.name; v.address = d.address
    db.commit(); return {"success": True}

@app.get("/api/vendor/{vendor_id}/milkmen")
def get_milkmen(vendor_id: str, db: Session = Depends(get_db)):
    milkmen = db.query(Milkman).filter(Milkman.vendor_id == vendor_id).all()
    return [{"id": m.id, "name": m.name, "phone": m.phone, "uniqueCode": m.unique_code,
             "active": m.active, "customerCount": db.query(Customer).filter(Customer.milkman_id == m.id).count()}
            for m in milkmen]

@app.post("/api/vendor/{vendor_id}/milkmen")
def add_milkman(vendor_id: str, d: MilkmanAdd, db: Session = Depends(get_db)):
    if db.query(Milkman).filter(Milkman.phone == d.phone).first():
        raise HTTPException(400, "Milkman already exists")
    code = gen_code()
    mm = Milkman(id=gen_id("mm_"), name=d.name, phone=d.phone, vendor_id=vendor_id, unique_code=code)
    db.add(mm); db.commit()
    return {"success": True, "milkman": {"id": mm.id, "name": mm.name, "uniqueCode": code}}

@app.post("/api/vendor/{vendor_id}/milkmen/link")
def link_milkman(vendor_id: str, d: MilkmanLink, db: Session = Depends(get_db)):
    mm = db.query(Milkman).filter(Milkman.unique_code == d.code.upper()).first()
    if not mm: raise HTTPException(404, "No milkman with that code")
    mm.vendor_id = vendor_id; db.commit()
    return {"success": True, "milkman": {"id": mm.id, "name": mm.name}}

@app.delete("/api/vendor/{vendor_id}/milkmen/{mid}")
def remove_milkman(vendor_id: str, mid: str, db: Session = Depends(get_db)):
    mm = db.query(Milkman).filter(Milkman.id == mid, Milkman.vendor_id == vendor_id).first()
    if not mm: raise HTTPException(404)
    db.delete(mm); db.commit(); return {"success": True}

@app.get("/api/vendor/{vendor_id}/customers")
def get_customers(vendor_id: str, db: Session = Depends(get_db)):
    customers = db.query(Customer).filter(Customer.vendor_id == vendor_id).all()
    mm_names  = {m.id: m.name for m in db.query(Milkman).all()}
    month     = this_month()
    payments  = {p.customer_id: p.paid for p in db.query(Payment).filter(
        Payment.vendor_id == vendor_id, Payment.month == month).all()}
    return [{"id": c.id, "name": c.name, "phone": c.phone, "address": c.address,
             "milkmanId": c.milkman_id, "milkmanName": mm_names.get(c.milkman_id, "Unassigned"),
             "dailyLitres": c.daily_litres, "ratePerLitre": c.rate_per_litre,
             "active": c.active, "paid": payments.get(c.id, False)} for c in customers]

@app.post("/api/vendor/{vendor_id}/customers")
def add_customer(vendor_id: str, d: CustomerAdd, db: Session = Depends(get_db)):
    if db.query(Customer).filter(Customer.phone == d.phone).first():
        raise HTTPException(400, "Customer already exists")
    c = Customer(id=gen_id("c_"), name=d.name, phone=d.phone, vendor_id=vendor_id,
                 milkman_id=d.milkman_id, daily_litres=d.daily_litres,
                 rate_per_litre=d.rate_per_litre, address=d.address)
    db.add(c); db.commit()
    return {"success": True, "customer": {"id": c.id, "name": c.name}}

@app.patch("/api/vendor/{vendor_id}/customers/{cid}")
def patch_customer(vendor_id: str, cid: str, d: CustomerPatch, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == cid, Customer.vendor_id == vendor_id).first()
    if not c: raise HTTPException(404)
    if d.milkman_id    is not None: c.milkman_id     = d.milkman_id
    if d.rate_per_litre is not None: c.rate_per_litre = d.rate_per_litre
    if d.daily_litres  is not None: c.daily_litres   = d.daily_litres
    db.commit(); return {"success": True}

@app.delete("/api/vendor/{vendor_id}/customers/{cid}")
def remove_customer(vendor_id: str, cid: str, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == cid, Customer.vendor_id == vendor_id).first()
    if not c: raise HTTPException(404)
    db.delete(c); db.commit(); return {"success": True}

@app.get("/api/vendor/{vendor_id}/deliveries")
def vendor_deliveries(vendor_id: str, month: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Delivery).filter(Delivery.vendor_id == vendor_id)
    if month: q = q.filter(Delivery.date.like(f"{month}%"))
    dels  = q.order_by(Delivery.date.desc()).limit(200).all()
    custs = {c.id: c for c in db.query(Customer).filter(Customer.vendor_id == vendor_id).all()}
    return [{"id": d.id, "date": d.date, "customerId": d.customer_id,
             "customerName": custs[d.customer_id].name if d.customer_id in custs else "Unknown",
             "litres": d.litres,
             "amount": round(d.litres * custs[d.customer_id].rate_per_litre, 2) if d.customer_id in custs else 0}
            for d in dels]

@app.post("/api/vendor/{vendor_id}/payment/toggle")
def toggle_payment(vendor_id: str, d: PaymentToggle, db: Session = Depends(get_db)):
    rec = db.query(Payment).filter(Payment.customer_id == d.customer_id,
                                   Payment.month == d.month, Payment.vendor_id == vendor_id).first()
    if rec:
        rec.paid = not rec.paid
        rec.paid_at = datetime.utcnow() if rec.paid else None
    else:
        rec = Payment(id=gen_id("pay_"), customer_id=d.customer_id, vendor_id=vendor_id,
                      month=d.month, paid=True, paid_at=datetime.utcnow())
        db.add(rec)
    db.commit()
    return {"success": True, "paid": rec.paid}

# ════════════════════════════════════════════════════
#  MILKMAN
# ════════════════════════════════════════════════════
@app.get("/api/milkman/{mid}/customers")
def milkman_customers(mid: str, db: Session = Depends(get_db)):
    customers = db.query(Customer).filter(Customer.milkman_id == mid, Customer.active == True).all()
    today = today_str()
    delivered = {d.customer_id: d.litres for d in db.query(Delivery).filter(
        Delivery.milkman_id == mid, Delivery.date == today).all()}
    return [{"id": c.id, "name": c.name, "phone": c.phone, "address": c.address,
             "dailyLitres": c.daily_litres, "vendorId": c.vendor_id,
             "deliveredToday": delivered.get(c.id)} for c in customers]

@app.post("/api/milkman/{mid}/delivery/toggle")
def toggle_delivery(mid: str, d: DeliveryToggle, db: Session = Depends(get_db)):
    rec_id   = f"del_{d.date}_{d.customer_id}"
    existing = db.query(Delivery).filter(Delivery.id == rec_id).first()
    if existing:
        db.delete(existing); db.commit()
        return {"success": True, "action": "removed"}
    db.add(Delivery(id=rec_id, date=d.date, customer_id=d.customer_id,
                    milkman_id=mid, vendor_id=d.vendor_id, litres=d.litres))
    db.commit()
    return {"success": True, "action": "added"}

@app.get("/api/milkman/{mid}/history")
def milkman_history(mid: str, db: Session = Depends(get_db)):
    dels  = db.query(Delivery).filter(Delivery.milkman_id == mid).order_by(Delivery.date.desc()).limit(100).all()
    custs = {c.id: c for c in db.query(Customer).all()}
    return [{"date": d.date, "customer_id": d.customer_id, "customerId": d.customer_id,
             "customerName": custs[d.customer_id].name if d.customer_id in custs else "Unknown",
             "customerPhone": custs[d.customer_id].phone if d.customer_id in custs else "",
             "litres": d.litres} for d in dels]

# ════════════════════════════════════════════════════
#  CUSTOMER
# ════════════════════════════════════════════════════
@app.get("/api/customer/{cid}/deliveries")
def customer_deliveries(cid: str, month: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Delivery).filter(Delivery.customer_id == cid)
    if month: q = q.filter(Delivery.date.like(f"{month}%"))
    return [{"date": d.date, "litres": d.litres} for d in q.order_by(Delivery.date).all()]

@app.get("/api/customer/{cid}/bill/{month}")
def customer_bill(cid: str, month: str, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == cid).first()
    if not c: raise HTTPException(404)
    vendor  = db.query(Vendor).filter(Vendor.id == c.vendor_id).first()
    milkman = db.query(Milkman).filter(Milkman.id == c.milkman_id).first()
    dels    = db.query(Delivery).filter(Delivery.customer_id == cid,
                                        Delivery.date.like(f"{month}%")).order_by(Delivery.date).all()
    payment = db.query(Payment).filter(Payment.customer_id == cid, Payment.month == month).first()
    rate    = c.rate_per_litre
    total   = sum(d.litres for d in dels)
    return {
        "customer":    {"name": c.name, "phone": c.phone, "address": c.address},
        "vendor":      {"name": vendor.shop_name if vendor else "—", "phone": vendor.phone if vendor else ""},
        "milkman":     {"name": milkman.name if milkman else "—"},
        "month":       month,
        "deliveries":  [{"date": d.date, "litres": d.litres, "amount": round(d.litres * rate, 2)} for d in dels],
        "totalLitres": round(total, 2),
        "rate":        rate,
        "totalAmount": round(total * rate, 2),
        "paid":        payment.paid if payment else False
    }

# ════════════════════════════════════════════════════
#  START
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"\n🥛 DudhWala starting → http://localhost:{port}")
    print(f"📖 API docs       → http://localhost:{port}/api/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
