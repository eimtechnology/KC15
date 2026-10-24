import time
import random
import asyncio 
from machine import Pin, ADC, SPI, I2C


import st7789
from font import vga2_8x8 as font1
from buzzer_music import music, tones

# --- ST7789 display: SPI0 ---
WIDTH, HEIGHT = 240, 240

BACKLIGHT_PIN = 21
CS_PIN = 20
DC_PIN = 17
RST_PIN = 16
MOSI_PIN = 19 #SDA
SCK_PIN = 18 #SCL
SPI_NUM = 0

spi = SPI(
    0, baudrate=31250000, polarity=0, phase=0,
    sck=Pin(18), mosi=Pin(19)
)
# The installed st7789 driver is initialized with the same keyword parameters
# as in the original game. Keep its CS asserted because this is the sole SPI
# device. This avoids relying on an optional `cs=` driver parameter.

display = st7789.ST7789(
    spi, WIDTH, HEIGHT,
    reset=Pin(RST_PIN, Pin.OUT),
    cs=Pin(CS_PIN, Pin.OUT),
    dc=Pin(DC_PIN, Pin.OUT),
    backlight=Pin(BACKLIGHT_PIN, Pin.OUT),
    rotation=0,
)
# --- Buttons: active-low, wired between GPIO and GND ---
BUTTON_X = Pin(11, Pin.IN, Pin.PULL_UP)  # Start / shoot / restart
BUTTON_Y = Pin(10, Pin.IN, Pin.PULL_UP)  # Toggle movement control mode

# --- Analog joystick (RP2040 ADC0/ADC1) ---
JOYSTICK_X = ADC(Pin(26))
JOYSTICK_Y = ADC(Pin(27))  # Initialized; vertical axis not used in this game

# --- Passive buzzer / asynchronous background music: GP8 ---
# buzzer_music.py supplies the music engine and documents this short demo song.
# Replace BGM_SONG with a longer Online Sequencer note string if desired.
BGM_SONG = (
    "0 E5 2 0;2 G5 2 0;4 B5 2 0;6 A5 1 0;7 G5 1 0;"
    "8 E5 2 0;10 G5 1 0;11 A5 1 0;12 B5 2 0;14 D6 2 0;"

    "16 D6 2 0;18 B5 2 0;20 A5 2 0;22 G5 1 0;23 A5 1 0;"
    "24 B5 2 0;26 G5 1 0;27 E5 1 0;28 F#5 2 0;30 D5 2 0;"

    "32 E5 2 0;34 G5 2 0;36 B5 2 0;38 D6 2 0;"
    "40 E6 2 0;42 D6 1 0;43 B5 1 0;44 A5 2 0;46 G5 2 0;"

    "48 A5 1 0;49 B5 1 0;50 D6 2 0;52 B5 2 0;"
    "54 A5 2 0;56 G5 2 0;58 F#5 2 0;60 E5 4 0;"

    "64 E5 1 0;65 E5 1 0;66 G5 2 0;68 A5 1 0;"
    "69 B5 1 0;70 D6 2 0;72 B5 2 0;74 A5 1 0;"
    "75 G5 1 0;76 F#5 2 0;78 E5 2 0;"

    "80 D5 2 0;82 F#5 2 0;84 A5 1 0;85 B5 1 0;"
    "86 A5 2 0;88 G5 2 0;90 F#5 2 0;92 D5 2 0;94 B4 2 0;"

    "96 E5 2 0;98 B5 2 0;100 D6 2 0;102 E6 2 0;"
    "104 D6 1 0;105 B5 1 0;106 A5 2 0;108 G5 1 0;"
    "109 A5 1 0;110 B5 2 0;"

    "112 G5 2 0;114 A5 2 0;116 B5 2 0;118 G5 2 0;"
    "120 E5 2 0;122 D5 2 0;124 E5 4 0"
)

BGM_TICK_MS = 25             # Scheduling period for music.tick()
BGM_TEMPO = 6                # Each song step lasts 6 * 25 = 150 ms
BGM_DUTY = 500              # PWM duty_u16 (0..65535), deliberately quiet
SFX_DUTY = 2400

# Use ONE PWM instance for BGM and sound effects on the same physical pin.
bgm_player = music(
    songString=BGM_SONG, looping=True, tempo=BGM_TEMPO,
    duty=BGM_DUTY, pin=Pin(8)
)
buzzer = bgm_player.pwms[0]
buzzer.duty_u16(0)
_buzzer_stop_ms = None
_sfx_frequency = 1047


def beep(frequency=1047, duration_ms=70):
    """Temporarily override BGM with a game effect without blocking."""
    global _buzzer_stop_ms, _sfx_frequency
    _sfx_frequency = frequency
    buzzer.freq(_sfx_frequency)
    buzzer.duty_u16(SFX_DUTY)
    _buzzer_stop_ms = time.ticks_add(time.ticks_ms(), duration_ms)


async def bgm_loop():
    """Advance buzzer_music while the game runs; sound effects take priority."""
    global _buzzer_stop_ms
    while True:
        bgm_player.tick()
        if _buzzer_stop_ms is not None:
            if time.ticks_diff(time.ticks_ms(), _buzzer_stop_ms) < 0:
                # music.tick() may change the note: keep the effect audible.
                buzzer.freq(_sfx_frequency)
                buzzer.duty_u16(SFX_DUTY)
            else:
                _buzzer_stop_ms = None
                # Restore whichever music note is currently playing.
                if bgm_player.playingNotes:
                    buzzer.freq(tones[bgm_player.playingNotes[0]])
                    buzzer.duty_u16(BGM_DUTY)
                else:
                    buzzer.duty_u16(0)
        await asyncio.sleep_ms(BGM_TICK_MS)


# --- MMA8451 / MMA8452 / MMA8453 accelerometer: I2C1, GP14/GP15 ---
# No external MMA845x library is needed; read_mma845x() supplies tilt input.
mma845x_i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400_000)
MMA845X_ADDR = None
MMA845X_BITS = 14


def init_mma845x():
    global MMA845X_ADDR, MMA845X_BITS
    try:
        connected = mma845x_i2c.scan()
        for address in (0x1C, 0x1D):
            if address not in connected:
                continue
            who_am_i = mma845x_i2c.readfrom_mem(address, 0x0D, 1)[0]
            bits = {0x1A: 14, 0x2A: 12, 0x3A: 10}.get(who_am_i)
            if bits is None:
                continue
            # Put device into standby before setting its +/-2g range.
            ctrl = mma845x_i2c.readfrom_mem(address, 0x2A, 1)[0]
            mma845x_i2c.writeto_mem(address, 0x2A, bytes([ctrl & 0xFE]))
            mma845x_i2c.writeto_mem(address, 0x0E, b"\x00")
            mma845x_i2c.writeto_mem(address, 0x2A, bytes([ctrl | 0x01]))
            MMA845X_ADDR = address
            MMA845X_BITS = bits
            print("MMA845x ready at", hex(address))
            return
        print("MMA845x not found on GP14/GP15 (game can still run)")
    except OSError as error:
        print("MMA845x I2C initialization failed:", error)


def read_mma845x():
    """Return (ax, ay, az) in g, or None if not detected/readable."""
    if MMA845X_ADDR is None:
        return None
    try:
        data = mma845x_i2c.readfrom_mem(MMA845X_ADDR, 0x01, 6)
        output = []
        shift = 16 - MMA845X_BITS
        counts_per_g = 1 << (MMA845X_BITS - 2)  # +/-2g full-scale
        for i in (0, 2, 4):
            raw = (data[i] << 8) | data[i + 1]
            if raw & 0x8000:
                raw -= 0x10000
            output.append((raw >> shift) / counts_per_g)
        return tuple(output)
    except OSError:
        return None


init_mma845x()

# --- Horizontal movement controls ---
# "accelerometer": X-axis tilt controls the ship; joystick is used if
# the MMA845x cannot be read. Set to "joystick" for the original controls.
CONTROL_MODE = "accelerometer"     # "accelerometer" or "joystick"
TILT_REVERSE_X = False             # True if tilting right moves the ship left
TILT_DEADZONE_G = 0.10             # Ignore small tilts/noise (+/-0.10 g)
TILT_MAX_SPEED_G = 0.65            # Tilt producing maximum movement speed
TILT_SMOOTHING = 0.35              # Low-pass filter: 0 < alpha <= 1

_tilt_neutral_x = 0.0
_tilt_filtered_x = 0.0
_y_was_pressed = False


def calibrate_tilt():
    """Treat the current board orientation as neutral (no horizontal motion)."""
    global _tilt_neutral_x, _tilt_filtered_x
    readings = []
    for _ in range(5):
        data = read_mma845x()
        if data is not None:
            readings.append(data[0])
        time.sleep_ms(20)
    if not readings:
        return False
    _tilt_neutral_x = sum(readings) / len(readings)
    _tilt_filtered_x = 0.0
    print("MMA845x X neutral:", _tilt_neutral_x, "g")
    return True


def joystick_horizontal_speed():
    """Original joystick-based horizontal speed, in pixels per frame."""
    joy_x = JOYSTICK_X.read_u16() // 256  # 0-255
    if joy_x < 100:
        return -PLAYER_SPEED
    if joy_x > 155:
        return PLAYER_SPEED
    return 0


def horizontal_speed():
    """Return signed movement speed based on X-axis tilt or joystick."""
    global _tilt_filtered_x
    if CONTROL_MODE == "joystick":
        return joystick_horizontal_speed()

    data = read_mma845x()
    if data is None:
        return joystick_horizontal_speed()  # Sensor absent or I2C read failure

    x_tilt = data[0] - _tilt_neutral_x
    if TILT_REVERSE_X:
        x_tilt = -x_tilt
    # Smooth slight fluctuations in the accelerometer output.
    _tilt_filtered_x += TILT_SMOOTHING * (x_tilt - _tilt_filtered_x)
    tilt_magnitude = abs(_tilt_filtered_x)
    if tilt_magnitude <= TILT_DEADZONE_G:
        return 0.0

    # Larger tilts result in faster movement, capped at PLAYER_SPEED.
    speed_fraction = (tilt_magnitude - TILT_DEADZONE_G) / (TILT_MAX_SPEED_G - TILT_DEADZONE_G)
    speed = min(speed_fraction, 1.0) * PLAYER_SPEED
    return speed if _tilt_filtered_x > 0 else -speed


# Game constants
SCREEN_WIDTH = 240
SCREEN_HEIGHT = 240

PLAYER_WIDTH = 20
PLAYER_HEIGHT = 10
PLAYER_SPEED = 5

ENEMY_WIDTH = 15
ENEMY_HEIGHT = 10
ENEMY_SPEED = 2

BULLET_WIDTH = 3
BULLET_HEIGHT = 5
BULLET_SPEED = 8
BULLET_COOL_DOWN = 4

ENEMY_ROWS = 3
ENEMY_COLS = 5
ENEMY_SPACING = 20

# Game states
STATE_START = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
STATE_VICTORY = 3

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
        self._position_x = float(self.x)  # Preserve fractional tilt movement
        self.y = SCREEN_HEIGHT - PLAYER_HEIGHT - 10
        self.old_x = self.x  # Track old position for clearing

    def move(self, dx):
        self.old_x = self.x  # Save old position before moving
        self._position_x += dx
        if self._position_x < 0:
            self._position_x = 0.0
        if self._position_x > SCREEN_WIDTH - PLAYER_WIDTH:
            self._position_x = float(SCREEN_WIDTH - PLAYER_WIDTH)
        self.x = int(self._position_x)  # Display coordinates must be integers

    def draw(self):
        display.fill_rect(self.x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT, st7789.GREEN)

    def clear(self):
        display.fill_rect(self.old_x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT, st7789.BLACK)

class Bullet:
    def __init__(self, x, y, direction=-1):  # direction -1 up (player), 1 down (enemy)
        self.x = x
        self.y = y
        self.direction = direction
        self.old_y = y  # Track old position for clearing

    def update(self):
        self.old_y = self.y  # Save old position
        self.y += self.direction * BULLET_SPEED

    def draw(self):
        display.fill_rect(self.x, self.y, BULLET_WIDTH, BULLET_HEIGHT, st7789.YELLOW if self.direction == -1 else st7789.RED)

    def clear(self):
        display.fill_rect(self.x, self.old_y, BULLET_WIDTH, BULLET_HEIGHT, st7789.BLACK)

    def off_screen(self):
        return self.y < 0 or self.y > SCREEN_HEIGHT

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True
        self.old_x = x
        self.old_y = y  # Track old position for clearing

    def draw(self):
        if self.alive:
            display.fill_rect(self.x, self.y, ENEMY_WIDTH, ENEMY_HEIGHT, st7789.RED)

    def clear(self, width):
        display.fill_rect(self.old_x-2, self.old_y, width+2, ENEMY_HEIGHT, st7789.BLACK)

# Global variables
player = Player()

enemies = []

player_bullets = []
bullet_cool_down = 0

enemy_bullets = []

score = 0
old_score = -1  # To track score changes

state = STATE_START

enemy_direction = 1  # 1 right, -1 left
enemy_move_timer = 0
enemy_shoot_timer = 0

start_drawn = False
gameover_drawn = False
victory_drawn = False 

def init_enemies():
    global enemies
    enemies = []
    for row in range(ENEMY_ROWS):
        for col in range(ENEMY_COLS):
            x = col * (ENEMY_WIDTH + ENEMY_SPACING) + 20
            y = row * (ENEMY_HEIGHT + ENEMY_SPACING) + 20
            enemies.append(Enemy(x, y))

def check_collision(rect1_x, rect1_y, rect1_w, rect1_h, rect2_x, rect2_y, rect2_w, rect2_h):
    return (rect1_x < rect2_x + rect2_w and
            rect1_x + rect1_w > rect2_x and
            rect1_y < rect2_y + rect2_h and
            rect1_y + rect1_h > rect2_y)

def update_game():
    global score, state, enemy_direction, enemy_move_timer, enemy_shoot_timer, bullet_cool_down
    global _y_was_pressed, CONTROL_MODE

    # Press Y once to switch between joystick and MMA845x tilt control.
    y_pressed = BUTTON_Y.value() == 0
    if y_pressed and not _y_was_pressed:
        CONTROL_MODE = "joystick" if CONTROL_MODE == "accelerometer" else "accelerometer"
        print("Movement control:", CONTROL_MODE)
    _y_was_pressed = y_pressed

    # Tilt the MMA845x along its X axis to  left/right.
    # If I2C is unavailable, the original joystick takes over.
    player.move(horizontal_speed())

    if BUTTON_X.value() == 0:  # Button pressed (active low)
        if bullet_cool_down > 0:
            pass
        else:
            player_bullets.append(Bullet(player.x + PLAYER_WIDTH // 2, player.y))
            bullet_cool_down += BULLET_COOL_DOWN
            beep(1600, 40)
        
    # Update player bullets
    for bullet in player_bullets[:]:
        bullet.update()
        if bullet.off_screen():
            bullet.clear()  # Clear last position before removing
            player_bullets.remove(bullet)
        else:
            bullet.clear()  # Always clear old position
            hit = False
            for enemy in enemies:
                if enemy.alive and check_collision(bullet.x, bullet.y, BULLET_WIDTH, BULLET_HEIGHT,
                                                  enemy.x, enemy.y, ENEMY_WIDTH, ENEMY_HEIGHT):
                    enemy.alive = False
                    if enemy_direction > 0:
                        enemy.clear(ENEMY_WIDTH + 5)  # Clear old position after update
                    else:
                        enemy.clear(ENEMY_WIDTH)  # Clear old position after update  # Clear enemy immediately
                    score += 10
                    beep(2200, 60)
                    player_bullets.remove(bullet)
                    hit = True
                    break
            if hit:
                bullet.clear()  # Ensure bullet is cleared if hit

    # Update enemy bullets
    for bullet in enemy_bullets[:]:
        bullet.update()
        bullet.clear()  # Clear old position
        if bullet.off_screen():
            enemy_bullets.remove(bullet)
        elif check_collision(bullet.x, bullet.y, BULLET_WIDTH, BULLET_HEIGHT,
                             player.x, player.y, PLAYER_WIDTH, PLAYER_HEIGHT):
            enemy_bullets.remove(bullet)
            state = STATE_GAMEOVER
            beep(260, 220)

    # Move enemies
    enemy_move_timer += 1
    if enemy_move_timer > 2:  # Move every 3 frames
        move_down = False
        for enemy in enemies:
            if enemy.alive:
                potential_x = enemy.x + enemy_direction * ENEMY_SPEED
                if potential_x < 0 or potential_x > SCREEN_WIDTH - ENEMY_WIDTH:
                    move_down = True
                    break
        if move_down:
            enemy_direction *= -1
        for enemy in enemies:
            if enemy.alive:
                enemy.old_x = enemy.x
                enemy.old_y = enemy.y
                if move_down:
                    enemy.y += ENEMY_HEIGHT
                    enemy.x += enemy_direction * ENEMY_SPEED  # Move in new direction
                    if enemy.y > SCREEN_HEIGHT - PLAYER_HEIGHT - 20:
                        state = STATE_GAMEOVER
                        beep(260, 220)
                else:
                    enemy.x += enemy_direction * ENEMY_SPEED
                
                enemy.clear(ENEMY_WIDTH)  # Clear old position after update
        enemy_move_timer = 0

    # Enemy shoot
    enemy_shoot_timer += 1
    if enemy_shoot_timer > random.randint(30, 60):
        alive_enemies = [e for e in enemies if e.alive]
        if alive_enemies:
            shooter = random.choice(alive_enemies)
            enemy_bullets.append(Bullet(shooter.x + ENEMY_WIDTH // 2, shooter.y + ENEMY_HEIGHT, 1))
        enemy_shoot_timer = 0

    if bullet_cool_down > 0:
        bullet_cool_down -= 1
    else:
        pass

    # Check if all enemies dead
    if all(not e.alive for e in enemies):
        state = STATE_VICTORY
        beep(2300, 260)

def draw_game():
    # Clear only changed parts: player, bullets, enemies, score
    if player.x != player.old_x:
        player.clear()  # Clear old player position

    player.draw()  # Draw new player

    for bullet in player_bullets:
        bullet.draw()  # Draw new bullet positions (cleared in update)

    for bullet in enemy_bullets:
        bullet.draw()

    for enemy in enemies:
        if enemy.alive:
            enemy.draw()  # Draw new enemy positions (cleared in update)

    # Update score only if changed
    global old_score
    if score != old_score:
        # Clear old score area (assuming score text is about 80 pixels wide)
        display.fill_rect(10, 10, 80, 8, st7789.BLACK)
        display.text(font1, "Score: " + str(score), 10, 10)
        old_score = score

def start_screen():
    global state, score, old_score, start_drawn, bullet_cool_down, player_bullets, enemy_bullets, player
    global _y_was_pressed
    if not start_drawn:
        display.fill(st7789.BLACK)
        display.text(font1, "Space Invaders", 40, 100)
        display.text(font1, "Hold level; press X", 30, 140)
        start_drawn = True
    if BUTTON_X.value() == 0:
        _y_was_pressed = BUTTON_Y.value() == 0
        player = Player()  # Center the ship on a new game
        state = STATE_PLAYING
        score = 0
        old_score = -1
        init_enemies()
        display.fill(st7789.BLACK)  # Clear screen once when starting game
        start_drawn = False
        bullet_cool_down = 0
        player_bullets = []
        enemy_bullets = []

def gameover_screen():
    global state, gameover_drawn
    if not gameover_drawn:
        display.fill(st7789.BLACK)
        display.text(font1, "Game Over", 60, 100)
        display.text(font1, "Score: " + str(score), 60, 120)
        display.text(font1, "Press X to Restart", 20, 140)
        gameover_drawn = True
    if BUTTON_X.value() == 0:
        state = STATE_START
        gameover_drawn = False

def victory_screen():
    global state, victory_drawn
    if not victory_drawn:
        display.fill(st7789.BLACK)
        display.text(font1, "Victory", 60, 100)
        display.text(font1, "Press X to Restart", 20, 120)
        victory_drawn = True
    if BUTTON_X.value() == 0:
        state = STATE_START
        victory_drawn = False

# --- Cooperative multitasking: 10 FPS game + independent BGM ticker ---
async def game_loop():
    display.fill(st7789.BLACK)
    while True:
        if state == STATE_START:
            start_screen()
        elif state == STATE_PLAYING:
            update_game()
            draw_game()
        elif state == STATE_GAMEOVER:
            gameover_screen()
        elif state == STATE_VICTORY:
            victory_screen()
        await asyncio.sleep_ms(100)  # Approx. 10 FPS, yields time to BGM


async def main():
    asyncio.create_task(bgm_loop())
    await game_loop()


try:
    asyncio.run(main())
finally:
    # Silence the buzzer if the program is interrupted.
    buzzer.duty_u16(0)
