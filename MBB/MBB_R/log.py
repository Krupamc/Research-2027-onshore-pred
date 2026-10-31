# Microsd card Logging for the (My Buoy Buddy :D)
import os

import sd_storage 
import lora_tx as tx
import time
import config as cfg

log_dir = "/sd/logs"
seq_dir = "/sd/seq.txt"
time_dir = "/sd/time.txt"

header = [ # All csv headers
    "seq",
    "rx_timestamp",
    "timestamp",
    "water_temp_c",
    "gps_lat",
    "gps_long",
    "gps_alt",
    "gps_sats",
    "gps_hdop",
    "internal_temp",
    "batt_v",
    "temp_error",
    "gps_error",
    "rtc_error",
    "internal_temp_error",
    "batt_error",
    "rssi",
    "snr",
    "raw_payload",
    "packet_type",
    "is_resend",
    ]

missing_header = [
    "rx_timestamp",
    "expected_from",
    "expected_to",
    "received_seq"
]


# Monthly csvs 
def get_monthly_filename(): 
    now = time.localtime(time.time() + cfg.utc_offset * 3600)
    year = now[0]
    month = now[1]
    fname = "{:04d}-{:02d}.csv".format(year, month)
    return log_dir + "/" + fname

def ensure_header(path, header_fields):
    # If file doesn't exist or is empty, write a header row
    try:
        size = os.stat(path)[6]
    except OSError:
        size = 0

    if size == 0:
        with open(path, "w") as f:
            f.write(",".join(header_fields) + "\n")
            f.close

# Append the record to the monthly csv
def save_sample(record):
    path = get_monthly_filename()
    sd_storage.ensure_dir("/sd/logs")
    ensure_header(path, header)

    # Build CSV line
    row = []
    for key in header:
        row.append(str(record.get(key, "")))
        
    line = ",".join(row) + "\n"

    with open(path, "a") as f:
        f.write(line)
        f.flush()
        
    f.close()

# Append the missing record to a csv
def save_missing(missing_record):

    path = "/sd/logs/missing_records.csv"
    sd_storage.ensure_dir("/sd/logs")
    ensure_header(path, missing_header)

    # Build CSV line
    row = []
    for key in missing_header:
        row.append(str(missing_record.get(key, "")))

    line = ",".join(row) + "\n"

    with open(path, "a") as f:
        f.write(line)
        f.flush()
        
    f.close()

# Following functions are for R/W the Sequence #
def load_seq():
    try:
        with open(seq_dir, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_seq(seq):
    with open(seq_dir, "w") as f:
        f.write(str(seq))

def next_sequence():
    seq = load_seq() + 1
    save_seq(seq)
    return seq

def what_is_next_sequence():
    seq = load_seq() + 1
    return seq

# Check if the sequence value
def check_sequence(record):

    seq = int(record["seq"]) # Get Seq
    last_seq = load_seq()

    result = { # Directory of status
        "first_time": False,
        "duplicate": False,
        "out_of_order": False,
        "ok": False,
        "old": False,
        "missing_seqs": []
    }

    if last_seq == 0: # First time
        print("[FIRST BOOT]: Welcome to the First Sequence!!!")
        result["first_time"] = True
        save_seq(seq)

    elif seq == last_seq + 1: #No Errors
        print(f"[SEQ]: Sequence is {seq}")
        result["ok"] = True
        save_seq(seq)
    
    elif seq == last_seq: # Duplicate
        print("[SEQ Warning]: Received Duplicatet; Ignored")
        result["duplicate"] = True
    
    elif seq < last_seq: # Old Packet
        print("[SEQ Warning]: Received an Old Packet; Ignored")
        result["old"] = True
        
    
    elif seq > last_seq + 1: # Missing packets
        print("[SEQ ERROR]: Missing Packet(s); Asking for Packet(s)")
        result["missing_seqs"] = list(range(last_seq + 1, seq))
    
    else: # Will sort at server
        print("[SEQ Warning]: Out of Order")

    missing = result.get("missing_seqs")
    
    if missing:
        print(f"Found {len(missing)} missing packets")
        tx.make_missing_record(record, seq, last_seq)

    
    return result
    
    