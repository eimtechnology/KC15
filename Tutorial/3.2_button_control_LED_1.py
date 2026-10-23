from machine import Pin, PWM
from time import sleep

button1 = Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
led1 = Pin(18, machine.Pin.OUT)
buzzer_pin = Pin(9)
buzzer = PWM(buzzer_pin)

while True:
    if button1.value() == 0:  # Button pressed (LOW)
        led1.on() 
        buzzer.freq(1047) # Set buzzer frequency
        buzzer.duty_u16(16384)  # Set volume (0~65535)
        sleep(0.2)
        buzzer.duty_u16(0)
        led1.off()
    else:
        pass
