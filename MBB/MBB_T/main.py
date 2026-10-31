# # MBB (My Buoy Buddy :D) Buoy Starting Script

import machine, time
import wtemp # DS18B20 Water Probe
import GPS # NEO-6M GPS
import rtc # DS3231 RTC
import log # Microsd Card logging
import sd_storage as sd # Mounting Microsd Card
import lora_tx as lora # LoRa Tranmission
import config as cfg

def read_water_temp():
    # Water Temperature
    try:
        temp_c = wtemp.watertmp()
    
    except Exception as e: # Errors will be sent with the rest of the data as a string; an error message starts with "*"
        print(f"[ERROR] Water Temp: {e}")
        return None, str(e)
        

    if isinstance(temp_c, str):
        print("No DS18B20 found")
    else:
        print("Water temp (C): {:.2f}".format(temp_c))
    
    return temp_c, None

def read_gps():
    # GPS
    try:
        gps_d = GPS.get_gps() # Sends a error back as a string if there is one
        return gps_d, None
    
    except Exception as e:
        print(f"[ERROR] GPS: {e}")
        return None, str(e)

def get_timestamp():
    dt = rtc.get_datetime()
    return (
        f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
        f"T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}Z"
    )

def read_time():
    # RTC - Real Time Clock
    try:
        dt = get_timestamp()
        return dt, None
    except Exception as e:
        print(f"[ERROR] RTC: {e}")
        return None, str(e)

def read_battery():
    # Battery Voltage
    try:
        bat_v = "insert function"
        return bat_v, None
    except Exception as e:
        print(f"[ERROR] Battery Voltage: {e}")
        return None, str(e)

def build_record():
    # Combine the data together
    temp_c, temp_err = read_water_temp()
    timestamp, time_err = read_time()
    in_temp, in_temp_err = rtc.get_temp_c()
    gps_d, gps_d_err= read_gps()
    batt_v, batt_v_err = read_battery()

    

    seq = log.what_is_next_sequence()

    record = { # Directory of all data values to be saved and trasmitted
        "seq": seq,
        "timestamp": timestamp,
        "water_temp_c": temp_c,
        "gps_lat": None,
        "gps_long": None,
        "gps_alt": None,
        "gps_sats": None,
        "gps_hdop": None,
        "internal_temp": in_temp,
        "batt_v": batt_v,        
        "temp_error": temp_err,
        "gps_error": gps_d_err,
        "rtc_error": time_err,
        "internal_temp_error": in_temp_err,
        "batt_error": batt_v_err,
    }
    if isinstance(gps_d, dict):
            record["gps_lat"] = gps_d.get("lat")
            record["gps_long"] = gps_d.get("lon")
            record["gps_alt"] = gps_d.get("alt")
            record["gps_sats"] = gps_d.get("sats")
            record["gps_hdop"] = gps_d.get("hdop")

    return record
    
    

def save_record(record):
    # Save to a microsd card
    try:
        log.save_sample(record)
        return True
    except Exception as e:
        print(f"[ERROR] Saving Error: {e}")
        return False

def transmit_record(record):
    # Transmit to LoRa and write down missing packets to send later...
    
    try:
        lora.transmit(record)
        return True
    except Exception as e:
        print(f"[ERROR] Transmitting Error: {e}")
        return False

# Retry a function
def retry_operation(func, record, attempts=3, delay_ms=500, name="operation"):
    for attempt in range(1, attempts + 1):
        ok = func(record)
        if ok:
            return True

        print(f"[ERROR] {name} attempt {attempt}/{attempts} failed")
        if attempt < attempts:
            time.sleep_ms(delay_ms)
            
    return False

def run_cycle():
    record = build_record() # Collect Data
    print("(1/3) Data collected...")
    mount = sd.mount_sd()
    lora.init_lora()
    time.sleep_ms(500)

    # Check if data is saved; if not retry
    save_ok = retry_operation(save_record, record, attempts=cfg.num_of_attempts, delay_ms=cfg.retry_delay_ms, name="Saving")

    if not save_ok:
        print("[ERROR] Data not Saved")
    log.next_sequence()
    print("(2/3) Data Saved...")
    time.sleep_ms(500)

    # Check if data is sent; if not retry
    tx_ok = retry_operation(transmit_record, record, attempts=cfg.num_of_attempts, delay_ms=cfg.retry_delay_ms, name="Transmitting")
        
    if tx_ok:
        print("(3/3) Data Sent!")
    else:
        print("[ERROR] Data not transmitted; save for retry later")

    return record

def main():
    print(f"Buoy Powered on!\n")

    #Alarm Reset/Set up
    rtc.sync_if_lost_power()
    rtc.clear_alarm()
    rtc.setup_alarm(cfg.alarm_interval) # CAHNGE TO 60 LATER in config
    
    seq = log.what_is_next_sequence()
    print(f"Welcome to the {seq} sampling of the {cfg.buoy_name}!\nAll data will be collected, saved, and transmitted to the Receiver on the shore.\n")
    while True:
        record = run_cycle()
    
        time.sleep(10) # remove for deepsleep later
    #wait for incoming transmissions for mission styff
    record = run_cycle()
    #machine.deepsleep
    

if __name__ == "__main__":
    main()