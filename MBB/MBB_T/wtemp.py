# MBB (My Buoy Buddy :D) Water probe
# Read from the DS18B20 water temp. probe

import machine, onewire, ds18x20, time
import config as cfg

ds_pin = machine.Pin(cfg.wtemp_gpio) # CHANGE THIS PIN
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

roms = ds_sensor.scan()
print('Found DS devices: ', roms) # prints all DS probes id (roms)

# Send water temp back to main.py
def watertmp():
  ds_sensor.convert_temp()
  time.sleep_ms(750)
  for rom in roms: # If there are more DS probes
    print(rom)
    tempC = ds_sensor.read_temp(rom)
    print('Water temperature (ºC):', "{:.2f}".format(tempC))
    tempC = round(tempC, 2)
    #temp = "{:.2f}".format(tempC)
    return tempC
    # Add F variables in the Receiver
    """
    tempF = tempC * (9/5) +32
    print('temperature (ºF):', "{:.2f}".format(tempF))
    """
# Test
#print(watertmp)


"""
Stuff for main.py:
while True:
    tempC = watertmp()

    if tempC is None:
        print("No DS18B20 found")
    else:
        print("Water temperature (C): {:.2f}".format(tempC))

    break
"""



"""
Other version:

print("Found DS devices:", roms)

def watertmp():
    if not roms:
        return None

    ds_sensor.convert_temp()
    time.sleep_ms(750)

    tempC = ds_sensor.read_temp(roms[0])
    return tempC
"""