
# MBB (My Buoy Buddy :D) receiver

import network
import time
from machine import Pin
import config as cfg
import ntptime

#credentials
ssid = cfg.ssid
password = cfg.password
network.hostname(cfg.hostname)


led = Pin("LED", Pin.OUT) #led pin

# make board led blink infinite for error
def blink():
    print("ERROR")
    while True:
        led.value(1)
        time.sleep(0.1)
        led.value(0)
        time.sleep(0.1)
        
def blink_limit(count: int):
    for i in range(count):
        led.value(1)
        time.sleep(0.25)
        led.value(0)
        time.sleep(0.25)
        led.value(1)
        time.sleep(1.5)
        led.value(0)

# Connect to wifi
def connect():
    wlan = network.WLAN(network.STA_IF)
    network.hostname("MBB")
    wlan.active(True)
    
    
    
    if wlan.isconnected():
        return wlan
    
    wlan.connect(ssid, password)
    time_start = time.ticks_ms() # timer for buffer
    blink_limit(1)
    
    while not wlan.isconnected():
        status = wlan.status()
        if status < 0:
            raise RuntimeError(f"WIFI Failed, status={status}")
        if time.ticks_diff(time.ticks_ms(), time_start) > (cfg.buffer_time * 1000):
            raise RuntimeError("WiFi connection timeout")
        print("Connecting...")
        print()
        time.sleep_ms(500)
    
    print("WIFI Connected:", wlan.ifconfig())
    print()
    return wlan

# Sync Time with NTP Server
days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def sync_wifi_time():
    blink_limit(1)
    ntptime.settime()
    print("Time Synced")
    print()

def formatted_time():
    year, month, day, hour, minute, second, _, _ = time.gmtime()
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"


# Connecting
try:
    wlan = connect()
        
except OSError as e: # Blink forever
    print("WIFI Error")
    blink()

# Sync time
try:
    sync_wifi_time()
    
    print("Current UTC:", formatted_time())


except Exception as e:
    print("Time Error:", e)
    blink()
    
time.sleep_ms(200)

    