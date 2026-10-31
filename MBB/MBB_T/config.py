# Configuration of the MBB (My Buoy Buddy :D):

""" This is the config.py file of the MBB. 
    If you are building the buoy using the exact same parts and setup,
    you will not have to change much. But if you are doing something different
    some changes will have to be made. 
    NOTE: This may include changing some sensor code and main.py depending on your setup
"""
# Buoy Name
buoy_name = "MBB_OG"

# How often the buoy colects data:
alarm_interval = 1

#---Operation Retries---
#(e.g. Saving or Transmitting)
num_of_attempts = 3
retry_delay_ms = 500

# ---GPIO---
# General Input Output Pins Layout
# ex: Module - Protocal/Pins reqiured

# RTC (Real Time Clock Moudule) - I2C
rtc_sda=6 #BIG PROBLEM for later me ;)
rtc_scl=7 #Resoder board resister
alarm_pin = 30 #Solder the R7 resistor, connect the INT pin to the RUN pin of the Pico, to reset Pico when DS3231 alarm clock outputs low level.

# Water temp - Ground, 3v3, any gpio
wtemp_gpio=9 #?

# GPS - UART 0/1
gps_tx = 0
gps_rx = 1

# Micro SD Card - SPI
sd_spi_id = 0        # or 0
sd_sck   = 18
sd_mosi  = 19
sd_miso  = 16
sd_cs    = 17        # chip select

#---LoRa---
lora_frq_khz = 915000  # 915 MHz for North America; use 868 MHZ for EU

lora_cfg = {
    "freq_khz": lora_frq_khz,
    "sf": 7,                 # spreading factor
    "bw": "125",             # 125 kHz bandwidth
    "coding_rate": 5,        # 4/5
    "preamble_len": 8,
    "output_power": 14,      # dBm
    "implicit_header": False,
    "crc_en": True,
    "syncword": 0x12,
    "dio3_tcxo_millivolts": 1800,
    "use_regulator_ldo": True,
}

# Pins
lora_gpio = [2,3,10,11,12,15,20,26] # Issue due to how RTC also wants gpio 20: see plan doc
spi_id = 1
pin_sck = 10
pin_mosi = 11
pin_miso = 12
pin_cs = 3
pin_dio1 = 20
pin_rst = 15
pin_busy = 2
bad_ad = 26