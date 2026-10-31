# MY Version of the ina219 drivers for a Micropython Microcontroller (Pico)

from micropython import const
import time

_REG_CONFIG = const(0x00)
_REG_SHUNT_VOLTAGE = const(0x01)
_REG_BUS_VOLTAGE = const(0x02)
_REG_POWER = const(0x03)
_REG_CURRENT = const(0x04)
_REG_CALIBRATION = const(0x05)

# 16 V bus range, +/-80 mV shunt range, 12-bit ADC with 32-sample averaging,
# continuous shunt and bus conversion.
_CONFIG_16V_5A = const(0x0EEF)
_DEFAULT_CALIBRATION = const(26868)
_DEFAULT_CURRENT_LSB_MA = 0.1524
_DEFAULT_POWER_LSB_W = 0.003048

class INA219:
    # Small INA219 driver using Microcontroller I2C
    def __init__(self, i2c, address=0x41, calibration=_DEFAULT_CALIBRATION, current_lsb_ma=_DEFAULT_CURRENT_LSB_MA, power_lsb_w=_DEFAULT_POWER_LSB_W)
        # Make sure we are using right device
        if not 0x03 <= address <= 0x77:
            raise ValueError(f"Invalid 7 Bit I2C Address: {address}")
        
        self.i2c = i2c
        self.address = address
        self.calibration = calibration
        self.current_lsb_ma = current_lsb_ma
        self.power_lsb_w = power_lsb_w
        self._buf2 = bytearray(2)
        self.configure()
    
    @staticmethod
    def _to_signed_16(value) -> int:
        return value - 65536 if value & 0x800 else value
    
    def _read_u16_be(self, register) -> int:
        self.i2c.readfrom_mem_into(self.address, register, self._buf2)
        return (self._buf2[0] << 8) | self._buf2[1]
    
    def configure(self) -> None:
        self.write_u16_be(_REG_CALIBRATION, self.calibration)
        self.write_u16_be(_REG_CONFIG, _CONFIG_16V_5A)
        
    def read(self):
        # Some INA219 variants can lose calibration after a reset. Rewriting it
        # before current/power reads is cheap and matches the original example.
        self.write_u16_be(_REG_CALIBRATION, self.calibration)
        raw_bus = self._read_u16_be(_REG_BUS_VOLTAGE)
        raw_shunt = self._read_u16_be(_REG_SHUNT_VOLTAGE)
        raw_current = self._read_u16_be(_REG_CURRENT)
        raw_power = self.read_u16_be(_REG_POWER)
        
        bus_voltage_v = (raw_bus >> 3) * 0.004
        shunt_voltage_mv = self._to_signed_16(raw_shunt) * 0.01
        supple_voltage_v = self. bus_voltage_v + (shunt_voltage_mv / 1000.0)
        
        return {
            "bus_voltage_v": bus_voltage_v,
            "shunt_voltage_mv": shunt_voltage_mv,
            "current_ma": self._to_signed_16(raw_current) * self.current_lsb_ma,
            "power_w": raw_power * self.power_lsb_w,
            "conversion_ready": bool(raw_bus & 0x002),
            "math_overflow": bool(raw_bus & 0x001)
        }
        
