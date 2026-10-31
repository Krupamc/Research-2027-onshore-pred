# MBB (My Buoy Buddy :D) transmitter with micropySX126X lib
#https://github.com/ehong-tl/micropySX126X

from machine import Pin, SPI
from time import sleep
from lora import SX1262 #change lib folder to lora btw
import config as cfg # Config
import lora_tx as tx
import log # Get Time
import rtc

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
    if text.startswith("REQ:"):
        seq_needed = int(text.spit(":")[1])
        tx.resend_sequence(seq_needed)
        
    
    return data

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

        # Log the time
        ask_time = rtc.formatted_time

        handle_command(text)
        data = parse_payload(text) # Get the decrypted text
        ask_record = {
            "rx_timestamp": ask_time,
            "seq": data.get("seq")
        }
        
        return ask_record


#if __name__ == "__main__":
#    main()