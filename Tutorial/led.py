from machine import Pin
from time import sleep

led_pin_number = 9
led_pin = Pin(led_pin_number, Pin.OUT)
led_pin.on()
sleep(5)
led_pin.off()