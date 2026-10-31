# MBB (My Buoy Buddy :D) Receiver

import machine, time
import sd_storage as sd # Mounting the Microsd card
import log # Microsd Card logging
import lora_rx as lora # LoRa Receiving
import lora_tx as tx # LoRa Transmitting
import config as cfg
import http_post as post # Send data to Server API
import boot # Time Syncing and WIFI

# Retry a function
def retry_operation_record(func, record, attempts=cfg.num_of_attempts, delay_ms=cfg.retry_delay_ms, name="operation"):
    for attempt in range(1, attempts + 1):
        ok = func(record)
        if ok:
            return True

        print(f"[ERROR] {name} attempt {attempt}/{attempts} failed")
        if attempt < attempts:
            time.sleep_ms(delay_ms)

    return False

def retry_operation(func, attempts=cfg.num_of_attempts, delay_ms=cfg.retry_delay_ms, name="operation"):
    for attempt in range(1, attempts + 1):
        ok = func()
        if ok:
            return True

        print(f"[ERROR] {name} attempt {attempt}/{attempts} failed")
        if attempt < attempts:
            time.sleep_ms(delay_ms)

    return False

def main():
    print(f"Board Powered on!\n")

    # Mount and turn on LoRa/Microsd Card
    mount = retry_operation(sd.mount_sd, name="Mount MicroSD")
    
    lora_device = retry_operation(lora.init_lora, name="LoRa Intialization")
    
    seq = log.what_is_next_sequence()
    print(f"Welcome to the {seq} sampling of the {cfg.buoy_name}!\nAll data will be collected, saved, and transmitted to the Receiver on the shore.\n")
    
    # Wait for packets
    while True:
        record = lora.receive_once()

        if record is not None:
            print("RX Record:", record)
            seq_status = log.check_sequence(record)
            
            if seq_status["ok"]:
                log.save_sample(record)

            elif seq_status["duplicate"] or seq_status["old"]:
                continue

            elif seq_status["missing_seqs"]:
                tx.ask_missing(seq_status["missing_seqs"]) #includes saving

        post.send_packet(record)
        time.sleep(0.1)

if __name__ == "__main__":
    main()