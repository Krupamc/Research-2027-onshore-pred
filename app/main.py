from fastapi import FastAPI, HTTPException, Query, Header, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from typing import Annotated, Any
from sqlmodel import select
import database as db
import config as cfg
import models as model
from pathlib import Path
import csv
import math
from direction_score import rank_headings

app = FastAPI(title="Onshore Wind Prediction and Wind Recommendations")
# Open Parent dir
BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Static and Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# For any http error, send them to a specific error page
# @app.exception_handler(StarletteHTTPException)
# async def not_found(request: Request, exc: StarletteHTTPException):
#     # HTTP Errors
#     if exc.status_code == 404:
#         return templates.TemplateResponse(request, "404.html", {"request": request, "title": "404", "detail": exc.detail})
#     elif exc.status_code == 403:
#         return templates.TemplateResponse(request, "403.html", {"request": request, "title": "403", "detail": exc.detail})
#     elif exc.status_code == 401:
#         return templates.TemplateResponse(request, "401.html", {"request": request, "title": "401", "detail": exc.detail})
#     elif exc.status_code == 400:
#         return templates.TemplateResponse(request, "400.html", {"request": request, "title": "400", "detail": exc.detail})
#     elif exc.status_code == 500:
#         return templates.TemplateResponse(request, "500.html", {"request": request, "title": "500", "detail": exc.detail})
    
#     return await http_exception_handler(request, exc)

#--Actual Web--

@app.on_event("startup") # Create the DB and tables on startup:
def on_startup():
    db.create_db_and_tables()

# API Key Check
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != cfg.api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key ;-;")

# Main Page
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "home.html", {"request": request})

# Historical forcast
REPLAY_FILE = BASE_DIR / "data" / "test_predictions.csv"

# Demonstration bearings only
HEADINGS = [0, 90, 180, 270]

def load_replay():
    if not REPLAY_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Historical replay data is not installed.",
        )

    required = {
        "target_timestamp",
        "actual_u_ms",
        "actual_v_ms",
        "ridge_u_ms",
        "ridge_v_ms",
        "persistence_u_ms",
        "persistence_v_ms",
    }

    with REPLAY_FILE.open(
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)

        missing = required - set(reader.fieldnames or [])

        if missing:
            raise HTTPException(
                status_code=503,
                detail="Replay CSV is missing required columns.",
            )

        rows = list(reader)

    if not rows:
        raise HTTPException(
            status_code=503,
            detail="Historical replay has no observations.",
        )

    return rows


def wind_summary(u, v):
    speed = math.hypot(u, v)

    # Meteorological direction: where the wind comes from.
    direction = (
        math.degrees(math.atan2(-u, -v)) % 360
        if speed > 0.000001
        else None
    )

    return {
        "speed_ms": speed,
        "from_deg": direction,
    }


@app.get("/replay", response_class=HTMLResponse)
def replay(
    request: Request,
    sample: Annotated[int, Query(ge=0)] = 0,
):
    rows = load_replay()

    if sample >= len(rows):
        raise HTTPException(
            status_code=404,
            detail="Historical sample not found.",
        )

    row = rows[sample]

    numeric_fields = [
        "actual_u_ms",
        "actual_v_ms",
        "ridge_u_ms",
        "ridge_v_ms",
        "persistence_u_ms",
        "persistence_v_ms",
    ]

    try:
        values = {
            field: float(row[field])
            for field in numeric_fields
        }

        if not all(math.isfinite(value) for value in values.values()):
            raise ValueError("Non-finite observation")

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=503,
            detail="The selected replay observation is invalid.",
        )

    ranking = rank_headings(
        values["ridge_u_ms"],
        values["ridge_v_ms"],
        HEADINGS,
    )

    persistence_ranking = rank_headings(
        values["persistence_u_ms"],
        values["persistence_v_ms"],
        HEADINGS,
    )

    ridge_heading = ranking[0]["heading_deg"]
    persistence_heading = persistence_ranking[0]["heading_deg"]

    ridge_observed = rank_headings(
        values["actual_u_ms"],
        values["actual_v_ms"],
        [ridge_heading],
    )[0]

    persistence_observed = rank_headings(
        values["actual_u_ms"],
        values["actual_v_ms"],
        [persistence_heading],
    )[0]

    options = [
        {
            "index": index,
            "timestamp": item["target_timestamp"],
        }
        for index, item in enumerate(rows)
    ]

    return templates.TemplateResponse(
        request=request,
        name="replay.html",
        context={
            "options": options,
            "sample": sample,
            "timestamp": row["target_timestamp"],
            "forecast": wind_summary(
                values["ridge_u_ms"],
                values["ridge_v_ms"],
            ),
            "observed": wind_summary(
                values["actual_u_ms"],
                values["actual_v_ms"],
            ),
            "ranking": ranking,
            "ridge_heading": ridge_heading,
            "persistence_heading": persistence_heading,
            "ridge_observed": ridge_observed["headwind_ms"],
            "persistence_observed": (
                persistence_observed["headwind_ms"]
            ),
        },
    )

# ---BUOY---

# Home Page
@app.get("/buoy")
def buoy_home():
    return {"message": "This is the homepage for the MBB API"}

# Add packet to the DB
@app.post("/buoy/ingest", response_model=model.BuoyPacketPublic, dependencies=[Depends(verify_api_key)])
def buoy_add_ingest(post: model.BuoyPacketCreate, session: db.SessionDep):
    packet = model.BuoyPacket.model_validate(post)
    session.add(packet)
    session.commit()
    session.refresh(packet)
    return packet

# Delete...?
@app.delete("/buoy/ingest/{packet_id}", dependencies=[Depends(verify_api_key)])
def buoy_delete_packet(packet_id: int, session: db.SessionDep):
    packet = session.get(model.BuoyPacket, packet_id)
    if not packet:
        raise HTTPException(status_code=404, detail="No Packet to Delete")
    session.delete(packet)
    session.commit()
    return {"message": f"{packet_id} deleted", "deleted_packet": packet}

# Last row of data in DB; search by id
@app.get("/buoy/latest")
def buoy_latest(session: db.SessionDep):
    packet = session.exec(select(model.BuoyPacket).order_by(model.BuoyPacket.id.desc())).first()
    if not packet:
        raise HTTPException(status_code=404, detail="Uhhhh there is no data...wahaha")
    return packet

# Search by seq
@app.get("/buoy/by-seq/{seq}", response_model=model.BuoyPacketPublic)
def buoy_read_by_seq(seq: int, session: db.SessionDep):
    packet = session.exec(select(model.BuoyPacket).where(model.BuoyPacket.seq == seq)).first()
    if not packet:
        raise HTTPException(status_code=404, detail="That sequence is in your imagination")
    return packet

# History of packets up to 100
@app.get("/buoy/history", response_model=list[model.BuoyPacketPublic])
def buoy_history(session: db.SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100, ) -> list[model.BuoyPacketPublic]:
    packets = session.exec(select(model.BuoyPacket).offset(offset).limit(limit)).all()
    return packets

# Read Specific Packet
@app.get("/buoy/by-id/{packet_id}", response_model=model.BuoyPacketPublic)
def buoy_read_packet(packet_id: int, session: db.SessionDep) -> Any:
    packet = session.get(model.BuoyPacket, packet_id)
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
