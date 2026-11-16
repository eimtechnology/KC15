import uos
import st7789
from UI import Option_Box, Band_Selector
from font import vga1_16x32 as font
from font import vga2_8x8 as small_font
import framebuf
from machine import Pin, SPI, ADC,PWM
import time, math,array
from utime import sleep_ms
import st7789 as stTest
import struct


pwm = PWM(Pin(19))
pwm.freq(50)

st7789_res = 0
st7789_dc  = 1
disp_width = 240
disp_height = 240
CENTER_Y = int(disp_width/2)
CENTER_X = int(disp_height/2)
spi_sck=Pin(2)
spi_tx=Pin(3)
spi0=SPI(0,baudrate=4000000, phase=1, polarity=1, sck=spi_sck, mosi=spi_tx)


#different option box UI elements: parameters(xPos, yPos, color, border_thickness, box_id)
black_box = Option_Box(0,94, st7789.BLACK, 5, 0)
brown_box = Option_Box(60,94, st7789.color565(150, 75, 0),5, 1)
red_box = Option_Box(120,94, st7789.RED, 5, 2)
orange_box = Option_Box(180,94, st7789.color565(255,166,0), 5, 3)

yellow_box = Option_Box(0,130, st7789.color565(255,255,0), 5, 4)
green_box = Option_Box(60,130, st7789.GREEN, 5, 5)
blue_box = Option_Box(120,130, st7789.BLUE, 5, 6)
violet_box = Option_Box(180,130, st7789.color565(127,0,255), 5, 7)

grey_box = Option_Box(0,164, st7789.color565(90,90,90), 5, 8)
white_box = Option_Box(60,164, st7789.color565(230,230,230), 5, 9)
gold_box = Option_Box(120,164, st7789.color565(212,175,55), 5, 10)
silver_box = Option_Box(180,164, st7789.color565(165,169,180), 5, 11)

resistor_color = st7789.color565(255, 188, 107)

band_selector = Band_Selector(0,200, 5)

#coordinate drawing information for each band in resistor UI [xPos, yPos, width, height]
band_pos = [[60,44,9,41],
         [85,47,7,35],
         [104,47,7,35],
         [121,46,7,36],
         [166,44,9,41]]


ui_elements = [[black_box, brown_box, red_box, orange_box],
               [yellow_box, green_box, blue_box, violet_box],
               [grey_box, white_box, gold_box, silver_box],
               [band_selector, band_selector, band_selector, band_selector]]

cursor = [0,0] #gives coordinates for the current element selected in ui_elements
prev_cursor = [0,0] #previous position of the cursor

#stores values of for all 5 current bands selected
current_band_values = [None,None,None,None,'']

#stores whether or not the user is selecting a color or not
is_select_mode = True

current_band = 1

#display needs to be initialized with old library in order to turn on
#new library isn't able to turn it on for a mysterious reason
display = stTest.ST7789(spi0, disp_width, disp_width,
                          reset=Pin(st7789_res, Pin.OUT),
                          dc=Pin(st7789_dc, Pin.OUT),
                          xstart=0, ystart=0, rotation=0)


display = st7789.ST7789(spi0, disp_width, disp_width,
                          reset=Pin(st7789_res, Pin.OUT),
                          dc=Pin(st7789_dc, Pin.OUT))
#display.init()


def draw_resistor(display):
    edge = st7789.color565(132, 127, 112)
    lead_edge = st7789.color565(132, 137, 140)
    lead_fill = st7789.color565(207, 211, 212)
    display.fill_rect(5, 61, 230, 7, lead_edge)
    display.fill_rect(5, 62, 230, 5, lead_fill)

    # Upper silhouette in screen coordinates. Mirror it about y=64 for the
    # lower edge. The thicker ends accommodate the two taller outer bands.
    profile = ((39, 49), (40, 46), (43, 43), (46, 42), (66, 42),
               (77, 45), (147, 45), (158, 42), (182, 42), (186, 43),
               (189, 46), (190, 49))
    for i in range(1, len(profile)):
        x0, y0 = profile[i - 1]
        x1, y1 = profile[i]
        width = x1 - x0
        if y0 == y1:
            display.fill_rect(x0, y0, width, 129 - 2 * y0, resistor_color)
        else:
            for x in range(x0, x1):
                top = y0 + ((y1 - y0) * (x - x0) + width // 2) // width
                display.vline(x, top, 129 - 2 * top, resistor_color)
        display.line(x0, y0, x1, y1, edge)
        display.line(x0, 128 - y0, x1, 128 - y1, edge)
    for x, top in (profile[0], profile[-1]):
        display.vline(x, top, 129 - 2 * top, edge)


display.fill(st7789.WHITE)
draw_resistor(display)


xAxis = ADC(Pin(28))
yAxis = ADC(Pin(29))

buttonB = Pin(5,Pin.IN, Pin.PULL_UP) #B
buttonA = Pin(6,Pin.IN, Pin.PULL_UP) #A
buttonStart = Pin(7,Pin.IN, Pin.PULL_UP) #A
buttonSelect = Pin(8,Pin.IN, Pin.PULL_UP) #A

def draw_arrow(display, tail_x, tip_x, y):
    direction = 1 if tip_x > tail_x else -1
    wing_x = tip_x - 12 * direction
    display.fill_rect(min(tail_x, tip_x), y, abs(tip_x - tail_x) + 1, 2, st7789.BLACK)
    for center_y in (y, y + 1):
        display.line(wing_x, center_y - 6, tip_x, center_y, st7789.BLACK)
        display.line(wing_x, center_y + 6, tip_x, center_y, st7789.BLACK)


#re-draws a ui element
def display_element(element):
    #redraw box and box border
    display.fill_rect(element.x_pos, element.y_pos, element.width, element.height, element.color)
    display.fill_rect(element.border_x, element.border_y, element.border_width, element.border_height, element.fill_color)

    if type(element) == Band_Selector:
        draw_arrow(display, 83, 10, 219)
        draw_arrow(display, 156, 229, 219)
        display.text(font, str(current_band), 110, 204, st7789.BLACK, element.fill_color)
    else:
        element_value = element.id #by default, the value of an element is equal to its ID
        if current_band == 1 or current_band == 2 or current_band == 3:
            if element_value > 9:
                element_value = '' #element has no value if the current band = 1, 2, or 3 and its ID > 9
        elif current_band == 4:
            element_value = Option_Box.fourth_band_values[element.id]
        elif current_band == 5:
            element_value = Option_Box.fifth_band_values[element.id]

        display.text(small_font, str(element_value), element.border_x, element.border_y + 5, st7789.BLACK, element.fill_color)

#refreshes all UI elements
def refresh_box_ui():
    for rows in ui_elements:
        for box in rows:
            display_element(box)


#calculates resistance based on current bands selected (current_band_values list)
def calculate_resistance():
    #if a multiplier value (4th band) hasn't been selected, don't calculate
    if current_band_values[3] == None:
        return
    #stores all 3 digit for first 3 bands of ressistor
    digits = ''

    #combine all digits to form 1 value, ignore digits that have no value (band isn't selected for that digit)
    for i in range(3):
        if current_band_values[i] != None:
            digits = digits + str(current_band_values[i])

    digits = int(digits)
    resistance = digits * current_band_values[3]


    prefix = ''
    #handles what prefix to give based on "raw" value of resistance
    if resistance > 999999999:
        #give prefix G for giga
        prefix = 'G'
        resistance /= 1000000000
    elif resistance > 999999:
        #give prefix M for mega
        prefix = 'M'
        resistance /= 1000000
    elif resistance > 999:
        #give prefix K for kilo
        prefix = 'K'
        resistance /= 1000
    else:
        prefix = ''

    if(current_band_values[4] != ''):
        percentage_text = ' +-' + str(current_band_values[4])
    else:
        percentage_text = ''

    #clear previous resistance text and drew updated one
    display.fill_rect(2,0,225,32,st7789.WHITE)
    display.text(font, str(resistance) + prefix + percentage_text , 2,0, st7789.BLACK, st7789.WHITE)



#draw all 5 bands to be empty
for i in range(5):
    display.fill_rect(band_pos[i][0], band_pos[i][1], band_pos[i][2], band_pos[i][3], resistor_color)

ui_elements[cursor[0]][cursor[1]].is_highlighted(True)
refresh_box_ui()

while True:
    if is_select_mode:

        #update previous cursor values to current
        prev_cursor[0] = cursor[0]
        prev_cursor[1] = cursor[1]

        #move cursor according to joystick movement (bounds detection included)
        if xAxis.read_u16() < 500: #if joystick is pressed up, move cursor up
            cursor[0] -= 1
            if(cursor[0] < 0):
                cursor[0] = 0
        elif xAxis.read_u16() > 55500: #if joystick is pressed down, move cursor down
            cursor[0] += 1
            if(cursor[0] > 3):
                cursor[0] = 3
        elif yAxis.read_u16() < 500  and cursor[0] != 3: #if joystick is pressed left, move cursor left
            cursor[1] -= 1
            if(cursor[1] < 0):
                cursor[1] = 0
        elif yAxis.read_u16() > 55500  and cursor[0] != 3: #if joystick is pressed right, move cursor right
            cursor[1] += 1
            if(cursor[1] > 3):
                cursor[1] = 3

        #if the cursor has moved, update which UI element is highlighted by cursor
        if prev_cursor[0] != cursor[0] or prev_cursor[1] != cursor[1]:
            #revert previously highlighted element
            ui_elements[prev_cursor[0]][prev_cursor[1]].is_highlighted(False)
            display_element(ui_elements[prev_cursor[0]][prev_cursor[1]])
            #highlight element cursor is on
            ui_elements[cursor[0]][cursor[1]].is_highlighted(True)
            display_element(ui_elements[cursor[0]][cursor[1]])
            time.sleep(0.25)

        #if the confirm selection button is pressed, move out of select mode
        if buttonStart.value() == 0:
            is_select_mode = False
            time.sleep(0.3)
    else:
        #if the element that was selected is the band selector...
        if type(ui_elements[cursor[0]][cursor[1]]) == Band_Selector:
            #handle current band we're on based on joystick movement (bounds detection included)
            if yAxis.read_u16() < 500: #if joystick is pressed left, current band we are on decreases
                current_band -= 1
                if(current_band < 1):
                    current_band = 1
                display.text(font, str(current_band), 110, 204, st7789.BLACK, ui_elements[cursor[0]][cursor[1]].fill_color) #draw new number based on current_band
                time.sleep(0.25)
            elif yAxis.read_u16() > 55500: #if joystick is pressed right, current band we are on increases
                current_band += 1
                if(current_band > 5):
                    current_band = 5
                display.text(font, str(current_band), 110, 204, st7789.BLACK, ui_elements[cursor[0]][cursor[1]].fill_color) #draw new number based on current_band
                time.sleep(0.25)

            if buttonStart.value() == 0:
                is_select_mode = True
                refresh_box_ui()
                time.sleep(0.3)
        else:
            selected_option = ui_elements[cursor[0]][cursor[1]]

            #assign 4th band value based on list of multiplier values and selected box
            if current_band == 4:
                current_band_values[current_band - 1] = Option_Box.multiplier_values[selected_option.id]
            #assign 5th band value based on list of fifth band values and selected box
            elif current_band == 5:
                #if the selected box has a value, assign band value, else set is_select_mode to True
                if Option_Box.fifth_band_values[selected_option.id] != '':
                    current_band_values[current_band - 1] = Option_Box.fifth_band_values[selected_option.id]
                else:
                    is_select_mode = True

            else:
                #if the selected box has a value (not box with ids 11 or 10), assign band value, else set is_select_mode to True
                if selected_option.id != 11 and selected_option.id != 10:
                    current_band_values[current_band - 1] = selected_option.id
                else:
                    is_select_mode = True

            #if is_select_mode is False, the selected box has a value, calculate resistance and update current band UI
            if is_select_mode == False:
                calculate_resistance()
                display.fill_rect(band_pos[current_band - 1][0],
                                  band_pos[current_band - 1][1],
                                  band_pos[current_band - 1][2],
                                  band_pos[current_band - 1][3],
                                  ui_elements[cursor[0]][cursor[1]].color)

            #go back to the selection mode
            is_select_mode = True



