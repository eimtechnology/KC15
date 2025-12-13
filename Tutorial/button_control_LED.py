from machine import Pin 
from time import sleep
from neopixel import NeoPixel

rgb_pin = Pin(23)
num_leds = 4
rgb_leds = NeoPixel(rgb_pin, num_leds)

#buttons
buttonA = Pin(11, Pin.IN, Pin.PULL_UP)
buttonB = Pin(10, Pin.IN, Pin.PULL_UP)
#end of buttons

color = (8,0,0)
lu = 8
rgb_leds.fill(color)
rgb_leds.write()

def button_pressed(button):
    if button.value() == 0:
        return True
    else:
        return False

print("start")
while True:
    if button_pressed(buttonA):
        lu-=1
        if lu < 0:
            lu = 0
        color = (lu, 0, 0)
        print(lu)
        rgb_leds.fill(color)
        rgb_leds.write()
        sleep(0.1)
    
    if button_pressed(buttonB):
        lu+=1
        if lu > 8:
            lu = 8
        color = (lu, 0, 0)
        print(lu)
        rgb_leds.fill(color)
        rgb_leds.write()
        sleep(0.1)
        
    sleep(0.1)
