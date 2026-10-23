import machine
import utime
import urandom

# Define GPIO pins for buttons, LEDs, and buzzer
button_pins = [13, 12, 11, 10] # Assign the pins at your own convenience
led_pins = [18, 19, 20, 21]
buzzer_pin = 9

# Define button objects
buttons = [machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP) for pin in button_pins]

# Define LED objects and turn them off
leds = [machine.Pin(pin, machine.Pin.OUT) for pin in led_pins]
for led in leds:
    led.off()

# Define the GPIO pin connected to the buzzer
buzzer_pwm = machine.Pin(buzzer_pin, machine.Pin.OUT)

# Create a PWM object for the buzzer
buzzer = machine.PWM(buzzer_pwm)

# Constants
tones = [1047, 1175, 1319, 1397]

def play_led(led):
    led.on()
    utime.sleep(0.2)
    led.off()
    

def play_tone(tone):
    # Set the desired frequency and duty cycle
    duty_cycle = 1500  # Set volume (0~65535)
    buzzer.freq(tone)
    buzzer.duty_u16(duty_cycle)

    # Play the tone for 2 seconds
    utime.sleep(0.2)

    # Turn off the PWM to stop the sound
    buzzer.duty_u16(0)
    
def you_win():
    for i in range(4):
        play_led(leds[i])
    
    # Setup melody, True to add a cadence 
    melody = [
        (tones[0], False),
        (tones[1], False),
        (tones[2], True),
        (tones[2], True),
        (tones[2], True),
        (tones[2], False),
        (tones[3], False),
        (tones[1], True),
        (tones[1], True),
        (tones[1], True),
        (tones[1], False),
        (tones[2], False),
        (tones[0], True),
        (tones[0], True),
        (tones[0], True),
    ]

    # Play melody
    for tone, pause in melody:
        play_tone(tone)
        if pause:
            utime.sleep(0.2)
    
    # Restart the game
    setup()
    loop()

def you_lost():
    for i in range(3):
        for led in leds:
            led.on()
        # Delay to keep all LEDs on for a certain duration (adjust as needed)
        utime.sleep(0.2)
        for led in leds:
            led.off()
        play_tone(tones[2])
        utime.sleep(0.2)
    
    # Restart the game
    setup()
    loop()

def setup():
    urandom.seed(utime.ticks_us())
    for led in leds:
        led.off()
    print("Welcome to the Memory Game!")

def loop():

    # Start a new game
    current_level = 1
    button_sequence = []

    button_sequence.append(urandom.randint(0, 3))

    while current_level <= 10:  # Adjust the number of levels as needed
        print("Level", current_level)
        utime.sleep(1)

        # Show the sequence to the user
        for button_num in button_sequence:
            leds[button_num].on()
            play_tone(tones[button_num])
            leds[button_num].off()
            utime.sleep(0.2)

        # Get user input
        user_sequence = []
        button_states = [0] * len(buttons)
        for _ in range(current_level):
            while True:
                for i, button in enumerate(buttons):
                    current_state = button.value()
                    if current_state == button_states[i]:
                        leds[i].on()
                        play_tone(tones[i])
                        leds[i].off()
                        user_sequence.append(i)
                        print("Button " + str(i+1) + " pressed")
                        utime.sleep(0.2)  # Debounce the button with a small delay
                        
                        # Check for a loss immediately after the user press
                        if user_sequence[-1] != button_sequence[len(user_sequence) - 1]:
                            you_lost()
                            print("Wrong! You Lost.")
                            return  # Exit the game loop
                        break
                        
                if len(user_sequence) == current_level:
                    break

        if current_level == len(user_sequence):
            print("Correct!")
            current_level += 1
            button_sequence.append(urandom.randint(0, 3))

    if current_level > 10:
        you_win()
        print("You Won!")

if __name__ == "__main__":
    setup()
    loop()
