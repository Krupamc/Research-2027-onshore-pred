# MBB (My Buoy Buddy :D) MicroSD card mounting
from machine import Pin, SPI
import os
import sdcard  # sdcard.py driver
import config as cfg

def mount_sd(): # ...mount the micosd...?
    spi = SPI(
        cfg.sd_spi_id,
        baudrate=1_000_000,
        polarity=0,
        phase=0,
        bits=8,
        firstbit=SPI.MSB,
        sck=Pin(cfg.sd_sck),
        mosi=Pin(cfg.sd_mosi),
        miso=Pin(cfg.sd_miso),
    )
    cs = Pin(cfg.sd_cs, Pin.OUT)
    sd = sdcard.SDCard(spi, cs)   
    vfs = os.VfsFat(sd)
    os.mount(vfs, "/sd")
    print("SD mounted at /sd")
    return sd

def ensure_dir(path): # Check if path exists
    try:
        os.mkdir(path)
    except OSError:
        pass 