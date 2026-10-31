# MBB (My Buoy Buddy :D) receiver with micropySX126X lib
#https://github.com/ehong-tl/micropySX126X

from machine import Pin, SPI
from time import sleep
import sx1262 #change lib folder to lora btw
import config as cfg # Config
import boot
import json

def init_lora(): # Initate with Settings from config
    spi = SPI(
        cfg.spi_id,
        baudrate=2_000_000,
        polarity=0,
        phase=0,
        bits=0,
        firstbit=SPI.MSB,
        sck=Pin(cfg.pin_sck),
        mosi=Pin(cfg.pin_mosi),
        miso=Pin(cfg.pin_miso),
        )
    
    global lora

    lora = SX1262(
        spi=spi,
        cs=Pin(cfg.pin_cs, Pin.OUT),
        irq=Pin(cfg.pin_dio1, Pin.IN),
        rst=Pin(cfg.pin_rst, Pin.OUT),
        busy=Pin(cfg.pin_busy, Pin.IN) if cfg.pin_busy is not None else None,
        lora_cfg=cfg.lora_cfg,
    )
    
    return lora

# Take payload and return directory
def handle_command(text):
    
    try:
        packet = json.loads(text)
    
    except Exception as e:
        print("[RX ERROR]: Malformed/Invalid JSON:", e)
        return None
    
    packet_type = packet.get("type")
    data = packet.get("data", {})
    
    if not isinstance(data, dict):
        print("[RX ERROR]: Packet Data is not a Dict.") 
        return None

    result = {
        "packet_type": packet_type,
        "is_resend": (packet_type == "RESEND"),
        "seq": packet.get("seq", data.get("seq")),
        "seq_requested": packet.get("seq_requested"),
        "data": data
    }

    return result

def build_record(parsed, pkt, raw_text):
    
    data = parsed["data"]

    record = {
            "seq": parsed.get("seq"),
            "rx_timestamp": boot.formatted_time(),
            "timestamp": data.get("timestamp"),
            "water_temp_c": data.get("water_temp_c"),
            "gps_lat": data.get("gps_lat"),
            "gps_long": data.get("gps_long"),
            "gps_alt": data.get("gps_alt"),
            "gps_sats": data.get("gps_sats"),
            "gps_hdop": data.get("gps_hdop"),
            "internal_temp": data.get("internal_temp"),
            "batt_v": data.get("batt_v"),
            "temp_error": data.get("temp_error"),
            "gps_error": data.get("gps_error"),
            "rtc_error": data.get("rtc_error"),
            "internal_temp_error": data.get("internal_temp_error"),
            "batt_error": data.get("batt_error"),
            "rssi": pkt.get("rssi"),
            "snr": pkt.get("snr"),
            "packet_type": parsed.get("packet_type"),
            "is_resend": parsed.get("is_resend"),
            "raw_payload": raw_text
        }
    
    return record


# Will loop infinitly waiting for data and print
def debug_loop():
    print("LoRa RX ready (freq {} kHz)".format(cfg.lora_cfg["freq_khz"]))

    while True:
        pkt = lora.recv()
        if pkt is not None:
            try:
                text = pkt["payload"].decode("utf-8")
            except Exception:
                text = str(pkt["payload"])
            rssi = pkt.get("rssi", None)
            snr = pkt.get("snr", None)
            print("RX:", text, "RSSI:", rssi, "SNR:", snr)
        else:
            sleep(0.1)

# Checks for Payload once and return the record of data
def receive_once():
    pkt = lora.recv()

    if pkt is None:
        return None
    
    else:

        try:
            text = pkt["payload"].decode("utf-8")
        except:
            text = str(pkt["payload"])

        # Open JSON
        parsed = handle_command(text)
        if parsed is None:
            return None
        
    return build_record(parsed, pkt, text   )
    
#if __name__ == "__main__":
#    main()