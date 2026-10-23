from machine import Pin, PWM
from time import sleep

button1 = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
button2 = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
led1 = machine.Pin(18, machine.Pin.OUT)
led2 = machine.Pin(19, machine.Pin.OUT)
buzzer_pin = machine.Pin(9)
buzzer = machine.PWM(buzzer_pin)

while True:
    if button1.value() == 0: # Button 1 pressed
        led1.on()
        buzzer.freq(1047) # Set buzzer frequency
        buzzer.duty_u16(512)  # Set volume (0~65535)
        sleep(0.2)
        buzzer.duty_u16(0)
        led1.off()
    elif button2.value() == 0: # Button 2 pressed
        led2.on()
        buzzer.freq(1397) # Set buzzer frequency
        buzzer.duty_u16(512)  # Set volume (0~65535)
        sleep(0.2)
        buzzer.duty_u16(0)
        led2.off()
    else:
        pass

