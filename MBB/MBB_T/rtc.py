# MBB (My Buoy Buddy :D) RTC
# Read from the DS3231 Real-time clock module
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-ds3231-rtc-micropython/

import time
import urtc
from machine import I2C, Pin
import config as cfg

days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Initialize RTC (connected to I2C)
i2c = I2C(1, scl=Pin(cfg.rtc_scl), sda=Pin(cfg.rtc_sda)) #Change pins
rtc = urtc.DS3231(i2c)

# Set the current time using a specified time tuple
def set_datetime_from_tuple(dt_tuple):
    # Time tuple: (year, month, day, day of week, hour, minute, seconds, milliseconds)
    #initial_time = (2024, 1, 30, 1, 12, 30, 0, 0)
    secs = time.mktime(dt_tuple)
    rtc.datetime(urtc.seconds2tuple(secs))


# Or get the local time from the system
def set_datetime_from_system():

    initial_time_tuple = time.gmtime() # tuple (microPython)
    initial_time_seconds = time.mktime(initial_time_tuple)  # local time in seconds

    # Convert to tuple compatible with the library
    initial_time = urtc.seconds2tuple(initial_time_seconds)

    # Sync the RTC
    rtc.datetime(initial_time)

# Send time back to main.py with time
def formatted_time():
    current_datetime = rtc.datetime()
    temperature = rtc.get_temperature()
    
    # Display time details
    print('Current date and time:')
    print('Year:', current_datetime.year)
    print('Month:', current_datetime.month)
    print('Day:', current_datetime.day)
    print('Hour:', current_datetime.hour)
    print('Minute:', current_datetime.minute)
    print('Second:', current_datetime.second)
    print('Day of the Week:', days_of_week[current_datetime.weekday])
    print(f"Buoy temperature: {temperature}°C")    
    # Format the date and time
    formatted_datetime = (
        f"{days_of_week[current_datetime.weekday]}, "
        f"{current_datetime.year:04d}-{current_datetime.month:02d}-{current_datetime.day:02d} "
        f"{current_datetime.hour:02d}:{current_datetime.minute:02d}:{current_datetime.second:02d} "
    )
    print(f"Current date and time: {formatted_datetime}")
    return formatted_datetime

# Test it
#print(formatted_time)

def get_datetime():
    # Return the DS3231 datetime object
    return rtc.datetime()

def get_temp_c():
    # Return DS3231 internal temperature (°C).
    try:
        return rtc.get_temperature(), None
    except Exception as e:
        return None, str(e)



#---Alarm---

"""Not needed due to using RUN Pin"""
# Setup GPIO for SQW and LED
#sqw_pin = Pin(cfg.alarm_pin, Pin.IN, Pin.PULL_UP)

# Add minutes to a datetime tuple and return a new datetime tuple
def add_minutes_to_time(dt, minutes):
    timestamp = time.mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 0))
    new_timestamp = timestamp + (minutes * 60)
    new_time = time.localtime(new_timestamp)
    return urtc.datetime_tuple(new_time[0], new_time[1], new_time[2], None, new_time[3], new_time[4], new_time[5], 0)

# Print the current time from the RTC
def print_current_time():
    now = rtc.datetime()
    formatted_time = f"{now.year}-{now.month:02}-{now.day:02} {now.hour:02}:{now.minute:02}:{now.second:02}"
    print(f"Current time: {formatted_time}")

# Callback for handling alarm interrupt
def clear_alarm():
    # Clear the alarm and schedule the next alarm
    if rtc.alarm(alarm=0):  # Check if Alarm 0 triggered
        print("Clearing Alarm 0 flag.")
        rtc.alarm(False, alarm=0)  # Clear alarm flag
        rtc.no_interrupt()

        """# Schedule the alarm to repeat 10 minutes from now
        now = rtc.datetime()
        next_alarm_time = add_minutes_to_time(now, 10)  # Add 10 minutes
        rtc.alarm_time(next_alarm_time, alarm=0)  # Set new alarm
        rtc.interrupt(0)  # Ensure Alarm 0 interrupt is enabled
        print(f"Next alarm set for: {next_alarm_time}")"""
        


def setup_alarm(mins):
    # Clear any existing alarms
    rtc.alarm(False, 0)
    rtc.no_interrupt()

    # Get the current time and set the first alarm X minute from now
    now = rtc.datetime()
    first_alarm_time = add_minutes_to_time(now, 1)  # Set first alarm for X minute from now
    rtc.alarm_time(first_alarm_time, alarm=0)  # Alarm 0

    # Enable the interrupt for Alarm 0
    rtc.interrupt(0)

    print(f"Alarm set for: {first_alarm_time}")

"""This Function is not needed cause the pico is rebooted"""
#def attach_alarm_irq(handler):
    # Attach an interrupt callback to SQW/INT pin.
#    sqw_pin.irq(trigger=Pin.IRQ_FALLING, handler=handler)

def sync_if_lost_power():
    try:
        # Sync time to compile time if RTC lost power
        if rtc.lost_power():
            initial_time_tuple = time.localtime()  # tuple (MicroPython)
            initial_time_seconds = time.mktime(initial_time_tuple)  # local time in seconds
            initial_time = urtc.seconds2tuple(initial_time_seconds)  # Convert to tuple compatible with the library
            rtc.datetime(initial_time)  # Sync the RTC

        print("RTC initialized. Setting up the periodic alarm...")
        setup_alarm(cfg.alarm_interval)

    except KeyboardInterrupt:
        print("Exiting program.")
