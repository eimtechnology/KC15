from machine import Pin 
from time import sleep
from neopixel import NeoPixel

rgb_pin = Pin(23)
num_leds = 4
rgb_leds = NeoPixel(rgb_pin, num_leds)

luminance = 0
max_luminance = 8
sleep_interval = 0.12

color = (0,0,0)
rgb_leds.fill(color)
rgb_leds.write()

while True:
        sleep(0.02)
        for luminance in range (0, max_luminance):
                color = (luminance, 0, 0)
                rgb_leds.fill(color)
                rgb_leds.write()
                sleep(sleep_interval)        
        
        sleep(0.02)
        for luminance in range (max_luminance, 0, -1):
                color = (luminance, 0, 0)
                rgb_leds.fill(color)
                rgb_leds.write()
                sleep(sleep_interval)
