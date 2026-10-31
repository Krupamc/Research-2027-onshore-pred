# Configuration of the MBB (My Buoy Buddy :D) Receiver:

#---WIFI---
# (Pico will flash a LED infinitly if the wifi does not connect)
ssid = "some-wifi..." # Name of the Wifi
password = "1234" # I hope you know what this is...
hostname = "My Buddy Buoy Receiver" # Name of the device on the WIFI network.
buffer_time = 30 # How many seconds the pico will let wifi try to connect before trying again.

# Buoy Name:
buoy_name = "MBB_Receiver" # How Buoy is refered to in the program.

#--API--
API_URL = "http://192.168.1.4/ingest"
API_KEY = "smth"


#---Operation Retries---
#(e.g. Saving or Transmitting)
num_of_attempts = 3
retry_delay_ms = 500

# Micro SD Card - SPI
sd_spi_id = 0        # or 0
sd_sck   = 18        # example
sd_mosi  = 19
sd_miso  = 16
sd_cs    = 17        # chip select

#---LoRa---

lora_frq_khz = 915000  # 915 MHz for North America; use 868000 for EU

lora_cfg = {
    "freq_khz": lora_frq_khz,
    "sf": 7,                 # spreading factor
    "bw": "125",             # 125 kHz bandwidth
    "coding_rate": 5,        # 4/5
    "preamble_len": 8,
    "output_power": 14,      # dBm (respect local limits)
    "implicit_header": False,
    "crc_en": True,
    "syncword": 0x12,
    "dio3_tcxo_millivolts": 1800,
    "use_regulator_ldo": True,
}

lora_gpio = [2,3,10,11,12,15,20,26] #issue due to how RTC also wants gpio 20: see plan doc
spi_id = 1
pin_sck = 10
pin_mosi = 11
pin_miso = 12
pin_cs = 3
pin_dio1 = 20
pin_rst = 15
pin_busy = 2
bad_ad = 26