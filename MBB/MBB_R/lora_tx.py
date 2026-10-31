# MBB (My Buoy Buddy :D) Receiver
# Missing data
from machine import Pin, SPI
import time
from lora import SX1262 #change lib folder to lora btw
import config as cfg # Config
import log # Saving to MicroSD
import lora_rx as rx # Recieving functions

def make_missing_record(record, seq, last_seq):
    missing_record = {
        "rx_timestamp": "replace", # Change this with wifi time speicifed earlier
        "expected_from": last_seq + 1,
        "expected_to": seq - 1,
        "received_seq": seq,
    }
    log.save_missing(missing_record)

def transmit_test(msg):
    #lora = init_lora()
    print("LoRa TX ready (freq {} kHz)".format(cfg.lora_cfg["freq_khz"]))

    counter = 0
    while True:
        #change to be just once
        msg = "buoy ping {}".format(counter) #also send the number of bits/items
        print("TX:", msg)
        rx.lora.send(msg.encode("utf-8"))
        counter += 1
        time.sleep(5)

def transmit_missing(seq):
    #lora = init_lora()
    print("LoRa TX ready (freq {} kHz)".format(cfg.lora_cfg["freq_khz"]))

    msg = f"REQ:{seq}" # Sends a REQ with the seq wanted

    print("TX:", msg)
    rx.lora.send(msg.encode("utf-8"))



def ask_missing(missing_seqs):
    #MAKE THIS
    for seq in missing_seqs:
        transmit_missing(seq)

        loop = True
        while loop:
            record = rx.receive_once()
            if record is not None:
                log.save_sample(record)
                time.sleep_ms(1)
            else:
                loop = False
            
