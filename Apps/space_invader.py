import time
import random
from machine import Pin, ADC, SPI
import test.st7789 as st7789  # Assuming the ST7789 library is imported and display is initialized
from board import game_kit
from test.fonts import vga2_8x8 as font1
from test.fonts import vga1_16x32 as font2

st7789_res = 0
st7789_dc = 1
disp_width = 240
disp_height = 240
CENTER_Y = int(disp_width / 2)
CENTER_X = int(disp_height / 2)
spi_sck = Pin(2)
spi_tx = Pin(3)
spi0 = SPI(0, baudrate=4000000, phase=1, polarity=1, sck=spi_sck, mosi=spi_tx)

display = st7789.ST7789(spi0, disp_width, disp_width,
                        reset=machine.Pin(st7789_res, machine.Pin.OUT),
                        dc=machine.Pin(st7789_dc, machine.Pin.OUT),
                        xstart=0, ystart=0, rotation=0)

# Input pins (adjust as per your hardware)
JOYSTICK_X = ADC(Pin(game_kit.joy_x))  # X-axis ADC
JOYSTICK_Y = ADC(Pin(game_kit.joy_y))  # Y-axis ADC (not used much here)
BUTTON_A = Pin(game_kit.key_a, Pin.IN, Pin.PULL_UP)  # Shoot
BUTTON_B = Pin(game_kit.key_b, Pin.IN, Pin.PULL_UP)  # Not used
BUTTON_X = Pin(game_kit.key_start, Pin.IN, Pin.PULL_UP)  # Not used
BUTTON_Y = Pin(game_kit.key_select, Pin.IN, Pin.PULL_UP)  # Not used

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
        self.y = SCREEN_HEIGHT - PLAYER_HEIGHT - 10
        self.old_x = self.x  # Track old position for clearing

    def move(self, dx):
        self.old_x = self.x  # Save old position before moving
        self.x += dx
        if self.x < 0:
            self.x = 0
        if self.x > SCREEN_WIDTH - PLAYER_WIDTH:
            self.x = SCREEN_WIDTH - PLAYER_WIDTH

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
        display.fill_rect(self.old_x, self.old_y, width, ENEMY_HEIGHT, st7789.BLACK)

# Global variables
player = Player()

enemies = []
player_bullets = []
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
    global score, state, enemy_direction, enemy_move_timer, enemy_shoot_timer

    # Read inputs
    joy_x = JOYSTICK_X.read_u16() // 256  # 0-255
    dx = 0
    if joy_x < 100:
        dx = -PLAYER_SPEED
    elif joy_x > 155:
        dx = PLAYER_SPEED

    player.move(dx)

    if BUTTON_A.value() == 0:  # Button pressed (active low)
        player_bullets.append(Bullet(player.x + PLAYER_WIDTH // 2, player.y))
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

    # Move enemies
    enemy_move_timer += 1
    if enemy_move_timer > 2:  # Move every 20 frames
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

    # Check if all enemies dead
    if all(not e.alive for e in enemies):
        state = STATE_VICTORY

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
    global state, score, old_score, start_drawn
    if not start_drawn:
        display.fill(st7789.BLACK)
        display.text(font1, "Space Invaders", 40, 100)
        display.text(font1, "Press A to Start", 40, 140)
        start_drawn = True
    if BUTTON_A.value() == 0:
        state = STATE_PLAYING
        score = 0
        old_score = -1
        init_enemies()
        display.fill(st7789.BLACK)  # Clear screen once when starting game
        start_drawn = False

def gameover_screen():
    global state, gameover_drawn
    if not gameover_drawn:
        display.fill(st7789.BLACK)
        display.text(font1, "Game Over", 60, 100)
        display.text(font1, "Score: " + str(score), 60, 120)
        display.text(font1, "Press A to Restart", 20, 140)
        gameover_drawn = True
    if BUTTON_A.value() == 0:
        state = STATE_START
        gameover_drawn = False

def victory_screen():
    global state, victory_drawn
    if not victory_drawn:
        display.fill(st7789.BLACK)
        display.text(font1, "Victory", 60, 100)
        display.text(font1, "Press A to Restart", 20, 120)
        victory_drawn = True
    if BUTTON_A.value() == 0:
        state = STATE_START
        victory = False

# Initial full clear
display.fill(st7789.BLACK)

# Main loop
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
    time.sleep(0.1)  # Frame rate

