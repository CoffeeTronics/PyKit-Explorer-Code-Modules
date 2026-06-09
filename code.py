import pykit_explorer
from digital_io import DigitalOutput
led = DigitalOutput(board.LED)
while True:
    print ("Hello, World!")
    led.value = True
    time.sleep(0.5)
    led.value = False
    time.sleep(0.5)