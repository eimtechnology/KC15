from machine import Pin, ADC, SPI
import st7789
from time import sleep

# initiate the ST7789 display
spi = SPI(0, baudrate=31250000, polarity=1, phase=1, sck=Pin(18), mosi=Pin(19))
WIDTH, HEIGHT = 240, 240
display = st7789.ST7789(
  spi, WIDTH, HEIGHT,
  reset=Pin(16, Pin.OUT),
  cs=Pin(17, Pin.OUT),
  dc=Pin(21, Pin.OUT),
  backlight=Pin(20, Pin.OUT),
  rotation=0
)
display.fill(st7789.BLACK)

# set up joystick input pins
x_adc = ADC(Pin(26))  # GP27 = ADC1
y_adc = ADC(Pin(27))  # GP26 = ADC0

# Initial position of rectangle
x, y = WIDTH // 2, HEIGHT // 2
RECT_SIZE = 10

# Range thresholds for joystick movement (tune as needed)
DEADZONE = 1000  # prevent small jitters
SPEED = 2        # pixels per move

def read_joystick():
    x_val = x_adc.read_u16()
    y_val = y_adc.read_u16()
    return x_val, y_val

def constrain(val, min_val, max_val):
    return max(min_val, min(val, max_val))

while True:
    # Read joystick
    x_val, y_val = read_joystick()

    # Clear the previous rectangle
    display.fill_rect(x, y, RECT_SIZE, RECT_SIZE, st7789.BLACK)

    # Update position based on joystick input
    if x_val > (32768 + DEADZONE):
        x += SPEED
    elif x_val < (32768 - DEADZONE):
        x -= SPEED

    if y_val > (32768 + DEADZONE):
        y -= SPEED  # Inverted because the screen Y axis increases downward
    elif y_val < (32768 - DEADZONE):
        y += SPEED

    # Constrain within screen bounds
    x = constrain(x, 0, WIDTH - RECT_SIZE)
    y = constrain(y, 0, HEIGHT - RECT_SIZE)

  # Draw a new rectangle
  display.fill_rect(x, y, RECT_SIZE, RECT_SIZE, st7789.RED)

  sleep(0.05)  # Small delay to control speed

