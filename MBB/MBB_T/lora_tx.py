# MBB (My Buoy Buddy :D) Buoy transmitter with micropySX126X lib
#https://github.com/ehong-tl/micropySX126X

from machine import Pin, SPI
from time import sleep
from lora import SX1262 #change lib folder to lora btw
import config as cfg
import log
import json

def init_lora():
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

def transmit_test(msg):
    lora = init_lora()
    print("LoRa TX ready (freq {} kHz)".format(cfg.lora_cfg["freq_khz"]))

    counter = 0
    while True:
        #change to just be 1 time
        msg = "buoy ping {}".format(counter) #also send the number of bits/items
        print("TX:", msg)
        lora.send(msg.encode("utf-8"))
        counter += 1
        sleep(5)

def transmit(record, seq):
    #lora = init_lora()
    print("LoRa TX ready (freq {} kHz)".format(cfg.lora_cfg["freq_khz"]))
    
    packet = { # Take the record and put it inside a JSON dump
        "type": "SEND",
        "seq": seq,
        "data": record
    }
 
    msg = json.dumps(packet)

    print("TX:", msg)
    lora.send(msg.encode("utf-8"))

def resend_sequence(seq_needed):
    print("LoRa TX ready for Resend (freq {} kHz)".format(cfg.lora_cfg["freq_khz"]))

    sample = log.read_sample(seq_needed) # Read the data from the monthly csv
    
    if sample is None: # IF data is not found, make send JSON with error
        packet = {
            type: "RESEND",
            "seq_requested": seq_needed,
            "data": f"[ERROR seq {seq_needed} not found]"
        }
        
    else: # With data send JSON
        packet = {
        "type": "RESEND",
        "seq_requested": seq_needed,
        "data": sample
    }
    
    msg = json.dumps(packet) # JSON

    print("TX:", msg)
    lora.send(msg.encode("utf-8"))

#if __name__ == "__main__":
#    main()

# WORKING ON Resend by reading from csv