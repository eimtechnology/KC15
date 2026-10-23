from machine import Pin, ADC
from time import sleep

x_adc = ADC(Pin(27))  # GP27 = ADC1
y_adc = ADC(Pin(26))  # GP26 = ADC0

while True:
    x_val = x_adc.read_u16()  
    y_val = y_adc.read_u16()
    print('X axis:', x_val,'  Y axis:', y_val)
    sleep(0.1)
