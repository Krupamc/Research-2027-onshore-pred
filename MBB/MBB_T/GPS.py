# GPS for the MBB (My Buoy Buddy :D)
# Read from the NEO-6M GPS module
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-neo-6m-micropython/

from machine import UART, Pin
from time import sleep
from micropyGPS import MicropyGPS
import config as cfg

# Instantiate the micropyGPS object
my_gps = MicropyGPS()

# Define the UART pins and create a UART object
gps_serial = UART(0, baudrate=9600, tx=Pin(cfg.gps_tx), rx=Pin(cfg.gps_rx))

def get_gps(): # Get all gps data as a string
    try:
        while gps_serial.any():
            data = gps_serial.read()
            for byte in data:
                stat = my_gps.update(chr(byte))
                if stat is not None:
                    # Print parsed GPS data
                    print('UTC Timestamp:', my_gps.timestamp)
                    print('Date:', my_gps.date_string('long'))
                    print('Latitude:', my_gps.latitude_string())
                    print('Longitude:', my_gps.longitude_string())
                    print('Altitude:', my_gps.altitude)
                    print('Satellites in use:', my_gps.satellites_in_use)
                    print('Horizontal Dilution of Precision:', my_gps.hdop)
                    print()
                    gps_data = str(my_gps.latitude_string()), str(my_gps.longitude_string()), str(my_gps.altitude), str(my_gps.satellites_in_use), str(my_gps.hdop)
                    return gps_data
            
    except Exception as e: # Sends error message as a string starting with "*"
        print(f"An error occurred: {e}")
        error = "*" + str(e)
        return error
    
def get_time(): # Get gps time
    try:
        while gps_serial.any():
            data = gps_serial.read()
            for byte in data:
                stat = my_gps.update(chr(byte))
                if stat is not None:
                    # Print parsed GPS data
                    print('UTC Timestamp:', my_gps.timestamp)
                    gps_time = my_gps.timestamp
                    return gps_time
            
    except Exception as e:
        print(f"An error occurred: {e}")
        error = "*" + str(e)
        return error
    
def get_long(): # Get gps longitude
    try:
        while gps_serial.any():
            data = gps_serial.read()
            for byte in data:
                stat = my_gps.update(chr(byte))
                if stat is not None:
                    # Print parsed GPS data
                    print('Longitude:', my_gps.longitude_string())
                    gps_long = my_gps.longitude_string()
                    return gps_long
            
    except Exception as e:
        print(f"An error occurred: {e}")
        error = "*" + str(e)
        return error
    
def get_lat(): # Get gps latitude
    try:
        while gps_serial.any():
            data = gps_serial.read()
            for byte in data:
                stat = my_gps.update(chr(byte))
                if stat is not None:
                    # Print parsed GPS data
                    print('Latitude:', my_gps.latitude_string())
                    gps_lat = my_gps.latitude_string()
                    return gps_lat
            
    except Exception as e:
        print(f"An error occurred: {e}")
        error = "*" + str(e)
        return error

def get_alt(): # get gps (buoy) altitude
    try:
        while gps_serial.any():
            data = gps_serial.read()
            for byte in data:
                stat = my_gps.update(chr(byte))
                if stat is not None:
                    # Print parsed GPS data
                    print('Altitude:', my_gps.altitude)
                    gps_alt = my_gps.altitude
                    return gps_alt
            
    except Exception as e:
        print(f"An error occurred: {e}")
        error = "*" + str(e)
        return error
    
def get_sats(): # Get gps # of satelies
    try:
        while gps_serial.any():
            data = gps_serial.read()
            for byte in data:
                stat = my_gps.update(chr(byte))
                if stat is not None:
                    # Print parsed GPS data
                    print('Satellites in use:', my_gps.satellites_in_use)
                    gps_sats = my_gps.satellites_in_use
                    return gps_sats
            
    except Exception as e:
        print(f"An error occurred: {e}")
        error = "*" + str(e)
        return error

def get_hdop(): # Get the hdop
    try:
        while gps_serial.any():
            data = gps_serial.read()
            for byte in data:
                stat = my_gps.update(chr(byte))
                if stat is not None:
                    # Print parsed GPS data
                    print('Horizontal Dilution of Precision:', my_gps.hdop)
                    gps_hdop = my_gps.hdop
                    return gps_hdop
            
    except Exception as e:
        print(f"An error occurred: {e}")
        error = "*" + str(e)
        return error
    
# Test it
#print(get_gps)