import machine
from machine import Pin, ADC, SPI
import test.st7789 as st7789
import time
import urandom
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
xAxis = ADC(Pin(28))   # joystick X-axis
yAxis = ADC(Pin(29))   # joystick Y-axis
btnA  = Pin(6, Pin.IN, Pin.PULL_UP)  # Button A (active low)

# === Game Variables ===
TAN_COLOR = st7789.color565(210, 180, 140)  # Tan background
CARD_BACK_COLOR = st7789.color565(139, 69, 19)  # Brown card back
CURSOR_COLOR = st7789.YELLOW
CARD_FRONT_COLOR = st7789.WHITE
SHAPE_COLORS = [st7789.RED, st7789.BLUE, st7789.GREEN, st7789.MAGENTA, st7789.CYAN, st7789.YELLOW]

# Game state
game_state = "instructions"  # "instructions", "playing", "game_over"
cursor_x = 0
cursor_y = 0
old_cursor_x = -1
old_cursor_y = -1
cards = []
flipped_cards = []
matched_pairs = []
moves = 0
old_moves = -1
card_w = 50
card_h = 60
grid_cols = 4
grid_rows = 3
card_spacing = 8
screen_dirty = True
high_score = None  # Best (lowest) number of moves

class Card:
    def __init__(self, x, y, shape_type, shape_color):
        self.x = x
        self.y = y
        self.shape_type = shape_type  # 0=circle, 1=square, 2=triangle, 3=diamond, 4=cross, 5=star
        self.shape_color = shape_color
        self.is_flipped = False
        self.is_matched = False

def draw_shape(x, y, shape_type, color):
    """Draw different shapes on cards"""
    cx = x + card_w // 2
    cy = y + card_h // 2
    
    if shape_type == 0:  # Circle
        # Draw circle manually using filled rectangles
        for dy in range(-15, 16):
            for dx in range(-15, 16):
                if dx*dx + dy*dy <= 15*15:  # Inside circle
                    display.pixel(cx + dx, cy + dy, color)
    elif shape_type == 1:  # Square
        display.fill_rect(cx - 12, cy - 12, 24, 24, color)
    elif shape_type == 2:  # Triangle
        # Draw triangle using lines
        display.line(cx, cy - 15, cx - 13, cy + 10, color)
        display.line(cx, cy - 15, cx + 13, cy + 10, color)
        display.line(cx - 13, cy + 10, cx + 13, cy + 10, color)
        # Fill triangle
        for i in range(-13, 14):
            height = int(25 - abs(i) * 25 / 13)
            display.vline(cx + i, cy - 15, height, color)
    elif shape_type == 3:  # Diamond
        # Draw diamond
        display.line(cx, cy - 15, cx - 12, cy, color)
        display.line(cx, cy - 15, cx + 12, cy, color)
        display.line(cx - 12, cy, cx, cy + 15, color)
        display.line(cx + 12, cy, cx, cy + 15, color)
        # Fill diamond
        for i in range(-15, 16):
            if i <= 0:
                width = int(12 * (15 + i) / 15)
            else:
                width = int(12 * (15 - i) / 15)
            display.hline(cx - width, cy + i, 2 * width + 1, color)
    elif shape_type == 4:  # Cross
        display.fill_rect(cx - 3, cy - 15, 6, 30, color)
        display.fill_rect(cx - 12, cy - 3, 24, 6, color)
    elif shape_type == 5:  # Star (simplified)
        # Draw star using lines from center
        points = [(0, -15), (-9, -5), (-15, 0), (-9, 5), (0, 15), (9, 5), (15, 0), (9, -5)]
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            display.line(cx + x1, cy + y1, cx + x2, cy + y2, color)
        # Fill star center
        display.fill_rect(cx - 5, cy - 5, 10, 10, color)

def init_game():
    """Initialize the memory game"""
    global cards, flipped_cards, matched_pairs, moves, cursor_x, cursor_y
    global old_cursor_x, old_cursor_y, old_moves, screen_dirty
    
    cards = []
    flipped_cards = []
    matched_pairs = []
    moves = 0
    old_moves = -1
    cursor_x = 0
    cursor_y = 0
    old_cursor_x = -1
    old_cursor_y = -1
    screen_dirty = True
    
    # Create pairs of cards
    shapes = []
    for i in range(6):  # 6 different shapes
        for j in range(2):  # 2 of each shape
            shapes.append((i, SHAPE_COLORS[i]))
    
    # Shuffle the shapes using a simple shuffle algorithm
    for i in range(len(shapes) - 1, 0, -1):
        j = urandom.randint(0, i)
        shapes[i], shapes[j] = shapes[j], shapes[i]
    
    # Create card objects
    card_idx = 0
    for row in range(grid_rows):
        for col in range(grid_cols):
            x = col * (card_w + card_spacing) + card_spacing
            y = row * (card_h + card_spacing) + card_spacing + 30  # Reduced offset for title
            shape_type, shape_color = shapes[card_idx]
            cards.append(Card(x, y, shape_type, shape_color))
            card_idx += 1

def draw_instructions():
    """Draw the instruction screen"""
    global screen_dirty
    if screen_dirty:
        display.fill(TAN_COLOR)
        display.text(font2, "MEMORY MATCH", 20, 40, st7789.color565(50, 50, 200))  # Blue text
        display.text(font_small, "Use joystick to move cursor", 10, 90, st7789.color565(100, 50, 50))  # Dark red text
        display.text(font_small, "Press A to flip cards", 30, 110, st7789.color565(100, 50, 50))
        display.text(font_small, "Match all pairs to win!", 25, 130, st7789.color565(100, 50, 50))
        
        # Show high score if it exists
        if high_score is not None:
            display.text(font_small, "Best: " + str(high_score) + " moves", 60, 160, st7789.color565(50, 100, 50))
            display.text(font_small, "Press A to start", 50, 190, st7789.color565(50, 100, 50))  # Dark green text
        else:
            display.text(font_small, "Press A to start", 50, 170, st7789.color565(50, 100, 50))  # Dark green text
        
        screen_dirty = False

def draw_card(card):
    """Draw a single card"""
    if card.is_matched:
        # Matched cards stay flipped
        display.fill_rect(card.x, card.y, card_w, card_h, CARD_FRONT_COLOR)
        display.rect(card.x, card.y, card_w, card_h, st7789.BLACK)
        draw_shape(card.x, card.y, card.shape_type, card.shape_color)
    elif card.is_flipped:
        # Flipped card shows shape
        display.fill_rect(card.x, card.y, card_w, card_h, CARD_FRONT_COLOR)
        display.rect(card.x, card.y, card_w, card_h, st7789.BLACK)
        draw_shape(card.x, card.y, card.shape_type, card.shape_color)
    else:
        # Card back
        display.fill_rect(card.x, card.y, card_w, card_h, CARD_BACK_COLOR)
        display.rect(card.x, card.y, card_w, card_h, st7789.BLACK)

def draw_cursor():
    """Draw cursor around current card"""
    # Erase old cursor if it moved
    if old_cursor_x != -1 and old_cursor_y != -1:
        old_card = cards[old_cursor_y * grid_cols + old_cursor_x]
        display.rect(old_card.x - 2, old_card.y - 2, card_w + 4, card_h + 4, TAN_COLOR)
        display.rect(old_card.x - 1, old_card.y - 1, card_w + 2, card_h + 2, TAN_COLOR)
        # Redraw the card border
        display.rect(old_card.x, old_card.y, card_w, card_h, st7789.BLACK)
    
    # Draw new cursor
    card = cards[cursor_y * grid_cols + cursor_x]
    display.rect(card.x - 2, card.y - 2, card_w + 4, card_h + 4, CURSOR_COLOR)
    display.rect(card.x - 1, card.y - 1, card_w + 2, card_h + 2, CURSOR_COLOR)

def draw_game():
    """Draw the game screen"""
    global screen_dirty, old_moves
    
    # Only redraw everything if screen is dirty
    if screen_dirty:
        display.fill(TAN_COLOR)
        
        # Draw all cards
        for card in cards:
            draw_card(card)
        
        screen_dirty = False
    
    # Update stats if moves changed
    if old_moves != moves:
        # Clear old stats area with individual rectangles to avoid black boxes
        display.fill_rect(10, 10, 100, 15, TAN_COLOR)  # Clear moves area
        display.fill_rect(140, 10, 90, 15, TAN_COLOR)  # Clear pairs area
        # Draw new stats
        display.text(font_small, "Moves: " + str(moves), 10, 10, st7789.color565(100, 50, 50))
        pairs_text = "Pairs: " + str(len(matched_pairs)) + "/6"
        if high_score is not None:
            pairs_text = pairs_text + " Best:" + str(high_score)
        display.text(font_small, pairs_text, 140, 10, st7789.color565(100, 50, 50))
        old_moves = moves

def handle_joystick():
    """Handle joystick input for cursor movement"""
    global cursor_x, cursor_y, old_cursor_x, old_cursor_y
    
    x_val = xAxis.read_u16()  # Now controls Y movement
    y_val = yAxis.read_u16()  # Now controls X movement
    center = 32768
    deadzone = 8000
    
    moved = False
    
    # Horizontal movement (controlled by Y axis)
    if y_val > center + deadzone:
        new_x = min(grid_cols - 1, cursor_x + 1)
        if new_x != cursor_x:
            old_cursor_x, old_cursor_y = cursor_x, cursor_y
            cursor_x = new_x
            moved = True
    elif y_val < center - deadzone:
        new_x = max(0, cursor_x - 1)
        if new_x != cursor_x:
            old_cursor_x, old_cursor_y = cursor_x, cursor_y
            cursor_x = new_x
            moved = True
    
    # Vertical movement (controlled by X axis)
    if x_val > center + deadzone:
        new_y = min(grid_rows - 1, cursor_y + 1)
        if new_y != cursor_y:
            old_cursor_x, old_cursor_y = cursor_x, cursor_y
            cursor_y = new_y
            moved = True
    elif x_val < center - deadzone:
        new_y = max(0, cursor_y - 1)
        if new_y != cursor_y:
            old_cursor_x, old_cursor_y = cursor_x, cursor_y
            cursor_y = new_y
            moved = True
    
    if moved:
        draw_cursor()
        time.sleep(0.2)  # Debounce

def flip_card():
    """Handle card flipping logic"""
    global flipped_cards, moves, matched_pairs, screen_dirty
    
    current_card = cards[cursor_y * grid_cols + cursor_x]
    
    # Can't flip if already matched or already flipped
    if current_card.is_matched or current_card.is_flipped:
        return
    
    # Can only flip if less than 2 cards are currently flipped
    if len(flipped_cards) >= 2:
        return
    
    # Flip the card
    current_card.is_flipped = True
    flipped_cards.append(current_card)
    draw_card(current_card)  # Only redraw this card
    
    # If two cards are flipped, check for match
    if len(flipped_cards) == 2:
        moves += 1
        card1, card2 = flipped_cards
        
        # Check if they match
        if card1.shape_type == card2.shape_type and card1.shape_color == card2.shape_color:
            # Match found!
            card1.is_matched = True
            card2.is_matched = True
            matched_pairs.append((card1, card2))
            flipped_cards = []
        else:
            # No match, flip back after delay
            time.sleep(1.5)
            card1.is_flipped = False
            card2.is_flipped = False
            draw_card(card1)  # Only redraw these cards
            draw_card(card2)
            flipped_cards = []

def check_win():
    """Check if all pairs are matched"""
    return len(matched_pairs) == 6

def draw_win_screen():
    """Draw the win screen"""
    global screen_dirty, high_score
    if screen_dirty:
        display.fill(TAN_COLOR)
        display.text(font2, "YOU WIN!", 40, 70, st7789.GREEN)
        display.text(font_small, "Completed in " + str(moves) + " moves", 30, 110, st7789.color565(100, 50, 50))
        
        # Check if this is a new high score
        if high_score is None or moves < high_score:
            high_score = moves
            display.text(font_small, "NEW BEST SCORE!", 45, 130, st7789.color565(200, 50, 50))  # Bright red for new record
            display.text(font_small, "Press A to play again", 30, 170, st7789.color565(50, 100, 50))
        else:
            display.text(font_small, "Best: " + str(high_score) + " moves", 55, 130, st7789.color565(50, 100, 50))
            display.text(font_small, "Press A to play again", 30, 170, st7789.color565(50, 100, 50))
        
        screen_dirty = False

def button_pressed():
    """Check if button A is pressed with debouncing"""
    if btnA.value() == 0:  # Button pressed (active low)
        time.sleep(0.05)  # Debounce delay
        while btnA.value() == 0:  # Wait for release
            time.sleep(0.01)
        return True
    return False

# === Main Game Loop ===
def main():
    global game_state, screen_dirty
    
    screen_dirty = True  # Initialize as dirty
    
    while True:
        if game_state == "instructions":
            draw_instructions()
            if button_pressed():
                game_state = "playing"
                init_game()
        
        elif game_state == "playing":
            handle_joystick()
            
            if button_pressed():
                flip_card()
            
            draw_game()
            
            if check_win():
                game_state = "game_over"
                screen_dirty = True
        
        elif game_state == "game_over":
            draw_win_screen()
            if button_pressed():
                game_state = "instructions"
                screen_dirty = True
        
        time.sleep(0.05)

# Start the game
if __name__ == "__main__":
    main()
