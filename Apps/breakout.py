import machine
from machine import Pin, ADC, SPI
import test.st7789 as st7789
import time
from test.fonts import vga1_16x32 as font2
from test.fonts import vga2_8x8 as font_small

# === Display setup ===
st7789_res = 0
st7789_dc  = 1
disp_width = 240
disp_height = 240

spi_sck = machine.Pin(2)
spi_tx  = machine.Pin(3)
spi0 = machine.SPI(0, baudrate=4000000, phase=0, polarity=1, sck=spi_sck, mosi=spi_tx)

display = st7789.ST7789(spi0, disp_width, disp_height,
    reset=machine.Pin(st7789_res, machine.Pin.OUT),
    dc=machine.Pin(st7789_dc, machine.Pin.OUT),
    xstart=0, ystart=0, rotation=0)

# === Controls ===
xAxis = ADC(Pin(29))   # joystick X-axis
btnA  = Pin(6, Pin.IN, Pin.PULL_UP)  # Button A (active low)

# === Game setup function ===
def init_game():
    global paddle_x, paddle_y, paddle_w, paddle_h, paddle_vx
    global ball_x, ball_y, ball_dx, ball_dy, old_ball_x, old_ball_y
    global bricks, rows, cols, brick_w, brick_h
    global score

    paddle_w, paddle_h = 50, 10
    paddle_y = 220
    paddle_x = 100
    paddle_vx = 0

    ball_x, ball_y = 120, 200
    ball_dx, ball_dy = 2, -2
    old_ball_x, old_ball_y = ball_x, ball_y

    rows, cols = 6, 6
    brick_w = disp_width // cols
    brick_h = 15
    bricks = [(x*brick_w, y*brick_h) for y in range(rows) for x in range(cols)]

    score = 0

    # Draw fresh screen
    display.fill(st7789.BLACK)
    for (bx, by) in bricks:
        display.fill_rect(bx, by, brick_w-2, brick_h-2, st7789.GREEN)
    display.fill_rect(paddle_x, paddle_y, paddle_w, paddle_h, st7789.WHITE)
    display.fill_rect(ball_x, ball_y, 5, 5, st7789.RED)

# === Main game loop ===
def play_game():
    global paddle_x, paddle_y, paddle_w, paddle_h, paddle_vx
    global ball_x, ball_y, ball_dx, ball_dy, old_ball_x, old_ball_y
    global bricks, score

    while True:
        # Reset button check
        if btnA.value() == 0:  # pressed
            init_game()
            return  # exit this loop → restart game

        # --- joystick input for paddle velocity ---
        x_val = xAxis.read_u16()
        center = 32768
        deadzone = 4000
        max_speed = 5

        if abs(x_val - center) > deadzone:
            if x_val > center:
                paddle_vx = int(((x_val - center) / (65535 - center)) * max_speed)
            else:
                paddle_vx = -int(((center - x_val) / center) * max_speed)
        else:
            paddle_vx = 0

        # --- update paddle ---
        new_paddle_x = paddle_x + paddle_vx
        new_paddle_x = max(0, min(disp_width - paddle_w, new_paddle_x))

        if new_paddle_x != paddle_x:
            display.fill_rect(paddle_x, paddle_y, paddle_w, paddle_h, st7789.BLACK)
            display.fill_rect(new_paddle_x, paddle_y, paddle_w, paddle_h, st7789.WHITE)
            paddle_x = new_paddle_x

        # --- update ball ---
        ball_x += ball_dx
        ball_y += ball_dy

        display.fill_rect(old_ball_x, old_ball_y, 5, 5, st7789.BLACK)
        display.fill_rect(ball_x, ball_y, 5, 5, st7789.RED)

        old_ball_x, old_ball_y = ball_x, ball_y

        # walls
        if ball_x <= 0 or ball_x >= disp_width-5:
            ball_dx *= -1
        if ball_y <= 0:
            ball_dy *= -1
        if ball_y >= disp_height:  # GAME OVER
            display.fill(st7789.BLACK)
            display.text(font2, "GAME OVER", 40, 100, st7789.RED)
            display.text(font_small, "Press A to restart", 50, 150, st7789.WHITE)
            return

        # paddle bounce
        if (paddle_y-5 <= ball_y <= paddle_y+paddle_h) and (paddle_x <= ball_x <= paddle_x+paddle_w):
            hit_pos = (ball_x - paddle_x) / paddle_w - 0.5
            ball_dx = int(hit_pos * 6)
            if ball_dx == 0:
                ball_dx = 1
            ball_dy *= -1

        # brick collision
        hit = None
        for b in bricks:
            bx, by = b
            if bx <= ball_x <= bx+brick_w and by <= ball_y <= by+brick_h:
                hit = b
                ball_dy *= -1
                break
        if hit:
            bricks.remove(hit)
            score += 10
            display.fill_rect(hit[0], hit[1], brick_w-2, brick_h-2, st7789.BLACK)

        # win condition
        if not bricks:
            display.fill(st7789.BLACK)
            display.text(font2, "YOU WIN!", 40, 100, st7789.GREEN)
            display.text(font_small, "Press A to restart", 50, 150, st7789.WHITE)
            return

        time.sleep(0.02)

# === Run ===
init_game()
while True:
    play_game()  # play until win/lose/reset
    # At GAME OVER / YOU WIN, wait for reset
    while btnA.value() == 1:
        time.sleep(0.05)  # idle until A is pressed
    init_game()
