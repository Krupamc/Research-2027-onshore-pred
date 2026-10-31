from fastapi import FastAPI, HTTPException, Query, Header, Depends
from typing import Annotated, Any
from sqlmodel import select
import database as db
import config as cfg
import models as model

app = FastAPI(title="Buoy API")


#--Actual Web--

@app.on_event("startup") # Create the DB and tables on startup:
def on_startup():
    db.create_db_and_tables()

# API Key Check
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != cfg.api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key ;-;")

# Main Page
@app.get("/")
def root():
    return {"status": "ok"}

# ---BUOY---

# Home Page
@app.get("/buoy")
def buoy_home():
    return {"message": "This is the homepage for the MBB API"}

# Add packet to the DB
@app.post("/buoy/ingest", response_model=model.PacketPublic, dependencies=[Depends(verify_api_key)])
def buoy_add_ingest(post: model.PacketCreate, session: db.SessionDep):
    packet = model.Packet.model_validate(post)
    session.add(packet)
    session.commit()
    session.refresh(packet)
    return packet

# Delete...?
@app.delete("/buoy/ingest/{packet_id}", dependencies=[Depends(verify_api_key)])
def buoy_delete_packet(packet_id: int, session: db.SessionDep):
    packet = session.get(model.Packet, packet_id)
    if not packet:
        raise HTTPException(status_code=404, detail="No Packet to Delete")
    session.delete(packet)
    session.commit()
    return {"message": f"{packet_id} deleted", "deleted_packet": packet}

# Last row of data in DB; search by id
@app.get("/buoy/latest")
def buoy_latest(session: db.SessionDep):
    packet = session.exec(select(model.Packet).order_by(model.Packet.id.desc())).first()
    if not packet:
        raise HTTPException(status_code=404, detail="Uhhhh there is no data...wahaha")
    return packet

# Search by seq
@app.get("/buoy/by-seq/{seq}", response_model=model.PacketPublic)
def buoy_read_by_seq(seq: int, session: db.SessionDep):
    packet = session.exec(select(model.Packet).where(model.Packet.seq == seq)).first()
    if not packet:
        raise HTTPException(status_code=404, detail="That sequence is in your imagination")
    return packet

# History of packets up to 100
@app.get("/buoy/history", response_model=list[model.PacketPublic])
def buoy_history(session: db.SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100, ) -> list[model.PacketPublic]:
    packets = session.exec(select(model.Packet).offset(offset).limit(limit)).all()
    return packets

# Read Specific Packet
@app.get("/buoy/by-id/{packet_id}", response_model=model.PacketPublic)
def buoy_read_packet(packet_id: int, session: db.SessionDep) -> Any:
    packet = session.get(model.Packet, packet_id)
    if not packet:
        raise HTTPException(status_code=404, detail="Sorry, Packet Not Found")
    return packet

#---WEATHERUNDERGROUND---

# Home Page
@app.get("/wu")
def wu_home():
    return {"message": "This is the homepage for the Weather Underground Scraper API"}

# Add json to the DB
@app.post("/wu/ingest", response_model=model.WUndergroundPublic, dependencies=[Depends(verify_api_key)])
def wu_post_ingest(post: model.WUndergroundCreate, session: db.SessionDep):
    packet = model.WUnderground.model_validate(post)
    session.add(packet)
    session.commit()
    session.refresh(packet)
    return packet

# Delete from the DB
@app.delete("/wu/ingest/{packet_id}", dependencies=[Depends(verify_api_key)])
def wu_delete_ingest(packet_id: int, session: db.SessionDep):
    packet = session.get(model.WUnderground, packet_id)
    if not packet:
        raise HTTPException(status_code=404, detail="No Data to Delete")
    session.delete(packet)
    session.commit()
    return {"message": f"{packet_id} deleted", "deleted_packet": packet}

# History
@app.get("/wu/history", response_model=list[model.WUndergroundPublic])
def wu_history(session: db.SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100, ) -> list[model.WUndergroundPublic]:
    packets = session.exec(select(model.WUnderground).offset(offset).limit(limit)).all()
    return packets

# Latest
@app.get("/wu/latest")
def wu_latest(session: db.SessionDep):
    packet = session.exec(select(model.WUnderground).order_by(model.WUnderground.id.desc())).first()
    if not packet:
        raise HTTPException(status_code=404, detail="Uhhh there is no data...wahahh")
    return packet

# Read specific Packet
@app.get("/wu/by-id/{packet_id}", response_model=model.WUndergroundPublic)
def wu_read_ingest(packet_id: int, session: db.SessionDep) -> Any:
    packet = session.get(model.WUnderground, packet_id)
    if not packet:
        raise HTTPException(status_code=404, detail="Sorry Packet Not Found")
    return packet
