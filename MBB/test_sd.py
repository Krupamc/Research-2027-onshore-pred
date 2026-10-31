from machine import Pin, SPI
import os
import sdcard

# Micro SD Card - SPI
sd_spi_id = 0
sd_sck   = 18        
sd_mosi  = 19
sd_miso  = 16
sd_cs    = 17   

# Mount
spi = SPI(
    sd_spi_id,
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    bits=8,
    firstbit=SPI.MSB,
    sck=Pin(sd_sck),
    mosi=Pin(sd_mosi),
    miso=Pin(sd_miso),
)

cs = Pin(sd_cs, Pin.OUT)
sd = sdcard.SDCard(spi, cs)
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")
print("SD Mounted at /sd")

def ensure_dir(path):
    try:
        os.mkdir(path)
    except OSError:
        pass