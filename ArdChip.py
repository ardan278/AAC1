import pyfirmata
import time
port='COM6'
b=pyfirmata.ArduinoMega(port)
led=b.get_pin('d:5:o')

def set(match):
    if match:
        led.write(1)
        time.sleep(5)
        led.write(0)
    else:
        led.write(0)