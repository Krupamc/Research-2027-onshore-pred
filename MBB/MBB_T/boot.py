
# MBB (My Buoy Buddy :D) Transmitter
"""There is not much to say here other than that the buoy turns on."""

import time

#Sleep before program to give USBs more time to setup
try: 
    time.sleep_ms(200)

except Exception:
    pass


    