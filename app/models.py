from sqlmodel import SQLModel, Field
from datetime import datetime

#---BUOY---

# Model for base/shared data
class BuoyPacketBase(SQLModel):
    seq: int
    rx_timestamp: datetime
    timestamp: datetime | None
    water_temp_c: float | None
    gps_lat: str | None
    gps_long: str | None
    gps_alt: str | None
    gps_sats: str | None 
    gps_hdop: str | None
    internal_temp: float | None
    batt_v: float | None
    temp_error: str | None
    gps_error: str | None
    rtc_error: str | None
    internal_temp_error: str | None
    batt_error: str | None
    rssi: float | None
    snr: float | None
    raw_payload: str | None # ?
    packet_type: str | None
    is_resend: bool | None
    expected_from: int | None
    expected_to: int | None
    received_seq: int | None

# Buoy 
class BuoyPacket(BuoyPacketBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

# Input
class BuoyPacketCreate(BuoyPacketBase):
    pass

# Model for public facing server
class BuoyPacketPublic(SQLModel):
    id: int
    timestamp: datetime | None
    water_temp_c: float | None
    gps_lat: str | None
    gps_long: str | None
    gps_alt: str | None
    gps_sats: str | None
    gps_hdop: str | None
    internal_temp: float | None
    is_resend: bool | None

#---Weather Underground scraping---

# Base Model (Parent)
class WUndergroundBase(SQLModel):
    station_id: str = Field(index=True, unique=True)
    time: datetime
    temp: float | None
    dew: float | None
    humidity: float | None
    wind_speed: float | None
    wind_gust: float | None
    wind_dir: float | None
    pressure: float | None
    precipitation_rate: float | None
    precipitation_accum: float | None
    uv: float | None
    solar_radiation: float | None

class WUnderground(WUndergroundBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class WUndergroundCreate(WUndergroundBase):
    pass

class WUndergroundPublic(WUndergroundBase):
    id: int