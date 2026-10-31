# Script to monitor the battery levels

from machine import I2c, Pin, reset
import time, json
from me_ina219 import INA219

config = {
    # Hardware
    "i2c_id": 0,
    "sda_pin": 4,
    "scl_pin": 5,
    "i2c_freq": 100000,
    "i2c_address": 0x41,
    
    # Monitor
    "sample_interval_seconds": 2,
    "filter_window": 5,
    "startup_grace_seconds": 30,
    
    # Reject clearly impossible readings instead of treating them as low voltage.
    "min_valid_voltage": 6.0,
    "max_valid_voltage": 15.5,
    
    # Initial conservative values for a 3-series Li-ion pack. These MUST be verified using the actual batteries, load, and a multimeter.
    "warning_voltage": 10.8,
    "warning_duration_seconds": 60,
    "recovery_voltage": 11.0,
    "shutdown_duration_seconds": 60,
    "emergency_voltage": 9.9,
    "emergency_duration_seconds": 60,
    
    # Battery Precentages
    "battery_empty_voltage": 9.0,
    "battery_full_voltage": 12.6,
    "log_every_seconds": 30,
    
    # System
    "shutdown_enabled": False,
    "warning_repeat_seconds": 300, # Seems reqally short for our applications
    "led_pin": "LED",
    "kill_pin": None,
    "reset_on_shutdown": False,
}

class UPSMonitorPico:
    
    def __init__(self, config=None):
        self.cfg = dict(CONFIG)
        
        # Use Config File
        if config:
            self.cfg.update(config)
            
            self.i2c = I2C(self.cfg["i2c_id"], scl=Pin(self.cfg["scl_pin"]), sda=Pin(self.cfg["sda_pin"]), freq=self.cfg["i2c_freq"])
            
            self.sensor = INA219(self.i2c, address=self.cfg["i2c_address"])
            
            self.led = Pin(self.cfg["led_pin"], Pin.OUT)
            
            # Pull up the Reset Pin (if there is kill pin)
            self.kill_pin = None
            if self.cfg["kill_pin"] is not None:
                self.kill_pin = Pin(self.cfg["kill_pin"], Pin.OUT)
                self.kill_pin.value(1)
                
            self.samples = []
            self.started_ms = time.ticks_ms()
            self.last_log_ms = 0
            self.last_warning_ms = None
            self.warning_since_ms = None
            self.shutdown_sinse_ms = None
            self.emergancy_since_ms = None
            self.warning_active = False
            self.last_state = "starting"
    
    def _ticks_to_s(self, start_ms, now_ms):
        if start_ms is None:
            return 0.0
        return max(0.0, time.ticks_diff(now_ms, start_ms / 1000.0))
                   
    def _update_timer(self, start_ms, condition, now_ms):
        if not condition:
            return None
        return now_ms if start_ms is None else start_ms
    
    def _median(self, values):
        s = sorted(values)
        n = len(s)
        if n == 0:
            return 0.0
        if n % 2:
            return float(s[mid])
        return (s[mid - 1] + s[mid]) / 2.0
    
    # Determin Battery Percent Based on voltage
    def estimated_battery_percent(self, voltage):
        empty_voltage = self.cfg["battery_empty_voltage"]
        full_voltage = self.cfg["battery_full_voltage"]
        
        pct = ((voltage - empty_voltage) / (full_voltage - empty_voltage)) * 100
        
        if pct < 0:
            return 0.0
        if pct > 100:
            return 100.0
        return pct
    
    def _reset_low_voltage_timers(self):
        self.warning_since_ms = None
        self.shutdown_since_ms = None
        self.emergency_since_ms = None
        
    def _warning_due(self, now_ms):
        if self.last_warning_ms is None:
            return True
        return time.ticks_diff(now_ms, self.last_warning_ms) >= int(self.cfg["warning_repeat_seconds"] * 1000)
    
    def _blink(self, count, on_ms=150, off_ms=150):
        for _ in range(count):
            self.led.value(1)
            time.sleep_ms(on_ms)
            self.led.value(0)
            time.sleep(off_ms)
    
    def _send_low_battery_warning(self, voltage, now_ms):
        if not self._warning_due(now_ms):
            return
        print(f"[BATTERY WARNING]: low battery {voltage:.2f} V")
        self.blink(2, 100, 100)
    
    def _request_shutdown(self, voltage, reason):
        print(f"[SHUTDOWN REQUEST]: {reason} at {voltage:.2f} V")
        self._blink(5, 80, 80)
        if not self.cfg["shutdown_enabled"]:
            print("[SHUTDOWN DENIED]: Action Disabled")
            return
        if self.kill_pin is not None:
            self.kill_pin.value(0)
        if self.cfg.get("reset_on_shutdown"):
            reset()
            
    def _evalutate_voltage(self, voltage, now_ms):
        uptime_s = time.ticks_diff(now_ms, self.started_ms) / 1000.0
        grace_remaining = max(0.0, self.cfg["startup_grace_seconds"] - uptime_s)
        
        if grace_remaining > 0:
            self._reset_low_voltage_timers()
            self.warning_active = False
            state = "startup_grace"
        else:
            self.warning_since_ms = self._update_timer(self.warning_since_ms, voltage <= self.cfg["warning_voltage"], now_ms)
            self.shutdown_since_ms = self._update_timer(self.shutdown_sinse_ms, voltage <= self.cfg["shutdown_voltage"], now_ms)
            self.emergency_sinse_ms = self._update_timer(self.emergency_sinse_ms, voltage <= self.cfg["emergency_voltage"], now_ms)
            
            warning_elasped = self._ticks_to_s(self.warning_sinse_ms, now_ms)
            shutdown_elasped = self.ticks_to_s(self.shutdown_sinse_ms, now_ms)
            emergancy_elasped = self.ticks_to_s(self.emergency_sinse_ms, now_ms)
            
            if voltage >= self.cfg["recovery_voltage"]:
                self.warning_active = False
                self.last_warning_ms = None
                state = "normal"
            elif self.emergency_sinse_ms is not None and emergency_elasped >= self.cfg["emergency_duration_seconds"]:
                self.warning_active = True
                state = "emergency_shutdown"
                self._send_low_battery_warning(voltage, now_ms)
                self._request_shutdown(voltage, now_ms)
            elif self.shutdown_sinse_ms is not None and shutdown_elasped >= self.cfg["shutdown_duration_seconds"]:
                self.warning_active = True
                
    