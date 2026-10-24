from machine import Pin, ADC, SPI, I2C, PWM
import time
import st7789
from font import vga2_8x8 as font1
from font import vga1_16x32 as font2


# --------------------------- Configuration ----------------------------

WIDTH = 240
HEIGHT = 240

SPI_NUM = 0
SCK_PIN = 18
MOSI_PIN = 19
RST_PIN = 16
DC_PIN = 17
CS_PIN = 20
BACKLIGHT_PIN = 21

BUTTON_X_PIN = 11
BUTTON_Y_PIN = 10
JOYSTICK_X_PIN = 26
JOYSTICK_Y_PIN = 27

MMA_SDA_PIN = 14
MMA_SCL_PIN = 15

BUZZER_PIN = 8
ENABLE_BUZZER_TEST = True  # Hold Button X to sound a 1 kHz tone
REFRESH_MS = 100


# ------------------------ Hardware initialization ---------------------

spi = SPI(
    SPI_NUM,
    baudrate=31_250_000,
    polarity=0,
    phase=0,
    sck=Pin(SCK_PIN),
    mosi=Pin(MOSI_PIN),
)
display = st7789.ST7789(
    spi, WIDTH, HEIGHT,
    reset=Pin(RST_PIN, Pin.OUT),
    cs=Pin(CS_PIN, Pin.OUT),
    dc=Pin(DC_PIN, Pin.OUT),
    backlight=Pin(BACKLIGHT_PIN, Pin.OUT),
    rotation=0,
)
if hasattr(display, "init"):
    display.init()

BUTTON_X = Pin(BUTTON_X_PIN, Pin.IN, Pin.PULL_UP)
BUTTON_Y = Pin(BUTTON_Y_PIN, Pin.IN, Pin.PULL_UP)
JOYSTICK_X = ADC(Pin(JOYSTICK_X_PIN))
JOYSTICK_Y = ADC(Pin(JOYSTICK_Y_PIN))

# PWM output remains silent until Button X is pressed.
buzzer = None
if ENABLE_BUZZER_TEST:
    buzzer = PWM(Pin(BUZZER_PIN))
    buzzer.freq(1000)
    buzzer.duty_u16(0)

MMA845X_ADDR = None
MMA845X_BITS = 14

# Draw initial status before communicating with the accelerometer.
display.fill(st7789.BLACK)
display.text(font2, "Hardware Test", 8, 8)
display.text(font1, "Joystick / Buttons / MMA845x", 8, 47)

try:
    mma845x_i2c = I2C(
        1,
        sda=Pin(MMA_SDA_PIN),
        scl=Pin(MMA_SCL_PIN),
        freq=400_000,
    )
except OSError as error:
    mma845x_i2c = None
    print("MMA845x I2C bus failed:", error)


# ---------------------------- MMA845x driver --------------------------

def init_mma845x():
    """Detect MMA8451/8452/8453, enable +/-2 g measurements."""
    global MMA845X_ADDR, MMA845X_BITS
    if mma845x_i2c is None:
        return False

    try:
        connected = mma845x_i2c.scan()
        for address in (0x1C, 0x1D):
            if address not in connected:
                continue

            who_am_i = mma845x_i2c.readfrom_mem(address, 0x0D, 1)[0]
            bits = {0x1A: 14, 0x2A: 12, 0x3A: 10}.get(who_am_i)
            if bits is None:
                print("Unknown I2C device at", hex(address),
                      "WHO_AM_I =", hex(who_am_i))
                continue

            # MMA845x configuration registers must be changed in standby.
            ctrl = mma845x_i2c.readfrom_mem(address, 0x2A, 1)[0]
            mma845x_i2c.writeto_mem(address, 0x2A,
                                   bytes([ctrl & 0xFE]))
            mma845x_i2c.writeto_mem(address, 0x0E, b"\x00")
            mma845x_i2c.writeto_mem(address, 0x2A,
                                   bytes([ctrl | 0x01]))

            MMA845X_ADDR = address
            MMA845X_BITS = bits
            print("MMA845x ready at", hex(address), "({} bit)".format(bits))
            return True

        print("MMA845x not found on GP14/GP15; other tests still run")
    except OSError as error:
        print("MMA845x initialization failed:", error)

    return False


def read_mma845x():
    """Return (ax, ay, az) in g, or None if unavailable."""
    if mma845x_i2c is None or MMA845X_ADDR is None:
        return None

    try:
        data = mma845x_i2c.readfrom_mem(MMA845X_ADDR, 0x01, 6)
        result = []
        shift = 16 - MMA845X_BITS
        counts_per_g = 1 << (MMA845X_BITS - 2)

        for index in (0, 2, 4):
            raw = (data[index] << 8) | data[index + 1]
            if raw & 0x8000:
                raw -= 0x10000
            result.append((raw >> shift) / counts_per_g)

        return tuple(result)
    except OSError:
        return None


# --------------------------- Display utilities -----------------------

def draw_line(y, label, value):
    """Clear and redraw a status line without leftover pixels."""
    display.fill_rect(0, y, WIDTH, 16, st7789.BLACK)
    display.text(font1, "{}: {}".format(label, value), 10, y + 3)


def main():
    init_mma845x()
    print("Hardware diagnostics running (Ctrl+C to stop)")
    if ENABLE_BUZZER_TEST:
        print("Hold Button X for a buzzer tone")

    try:
        while True:
            x_value = JOYSTICK_X.read_u16()
            y_value = JOYSTICK_Y.read_u16()
            button_x = BUTTON_X.value()
            button_y = BUTTON_Y.value()
            accel = read_mma845x()

            # Active-low: 0 means pressed.
            if buzzer is not None:
                buzzer.duty_u16(16384 if button_x == 0 else 0)

            draw_line(75, "Joystick X", "{:05d}".format(x_value))
            draw_line(95, "Joystick Y", "{:05d}".format(y_value))
            draw_line(115, "Button X", "PRESSED" if button_x == 0 else "released")
            draw_line(135, "Button Y", "PRESSED" if button_y == 0 else "released")

            if accel is None:
                draw_line(160, "MMA845x", "not ready")
                draw_line(180, "Accel X", "N/A")
                draw_line(200, "Accel Y", "N/A")
                draw_line(220, "Accel Z", "N/A")
            else:
                ax, ay, az = accel
                draw_line(160, "MMA845x", "ready")
                draw_line(180, "Accel X", "{:+.3f} g".format(ax))
                draw_line(200, "Accel Y", "{:+.3f} g".format(ay))
                draw_line(220, "Accel Z", "{:+.3f} g".format(az))

            time.sleep_ms(REFRESH_MS)
    finally:
        if buzzer is not None:
            buzzer.duty_u16(0)
            buzzer.deinit()


if __name__ == "__main__":
    main()
