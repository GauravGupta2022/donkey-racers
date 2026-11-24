import time
import board
from adafruit_pca9685 import PCA9685

# --- SETTINGS (Change these to match your board's wiring) ---
ESC_PIN = 3
SERVO_PIN = 12
# ------------------------------------------------------------

# 1. Connect to the PCA9685 board
i2c = board.I2C()
pca = PCA9685(i2c)
pca.frequency = 50  # Standard RC frequency (50Hz = 20ms period)

# 2. Simple helper function to send a pulse
def set_pulse(pin, pulse_ms):
    # Adafruit uses a 16-bit value (up to 65535). 
    # We calculate the pulse length as a fraction of the 20ms period.
    pca.channels[pin].duty_cycle = int((pulse_ms / 20.0) * 65535)

def enter_backward_mode():
    # 1. Neutral
    set_pulse(ESC_PIN, 1.5)
    time.sleep(1)

    # 2. Pulse between 1 and 1.5 ms (brake/reverse side)
    set_pulse(ESC_PIN, 1.4)
    time.sleep(1)

    # 3. Neutral again
    set_pulse(ESC_PIN, 1.5)
    time.sleep(1)

def enter_forward_mode():
    set_pulse(ESC_PIN, 1.5)
    time.sleep(1)
    set_pulse(ESC_PIN, 1.7) # Pulse between 1.5 and 2 ms (returning to forward mode)
    time.sleep(1)
    set_pulse(ESC_PIN, 1.5)
    time.sleep(1)



try:
    print("Holding neutral for 3 seconds to arm the ESC...")
    set_pulse(ESC_PIN, 1.5)   # 1.5ms is neutral/stop
    set_pulse(SERVO_PIN, 1.5) # 1.5ms is center steering
    time.sleep(3)

    print("Testing steering: Left, then Right...")
    set_pulse(SERVO_PIN, 1.2) # Left
    time.sleep(1)
    set_pulse(SERVO_PIN, 1.8) # Right
    time.sleep(1)
    set_pulse(SERVO_PIN, 1.5) # Back to center
    time.sleep(0.5)

    print("Testing throttle (make sure wheels are off the ground!)...")
    set_pulse(ESC_PIN, 1.6)   # Gentle forward throttle
    time.sleep(2)

    #extra credit portion
    print("Entering backward mode")
    enter_backward_mode()
    set_pulse(ESC_PIN, 1.2) #moves car backward
    time.sleep(2) 

    print("Entering forward mode again")
    enter_forward_mode()
    set_pulse(ESC_PIN, 1.7) #moves car forward
    time.sleep(2) 

    
finally:
    # This block ALWAYS runs, even if the code crashes or you hit Ctrl+C
    print("Test complete. Shutting down safely.")
    set_pulse(ESC_PIN, 1.5)   # Stop the motor
    set_pulse(SERVO_PIN, 1.5) # Center the steering
    time.sleep(1)
    
    # Turn off the PWM signals completely so the motors don't hum
    pca.channels[ESC_PIN].duty_cycle = 0
    pca.channels[SERVO_PIN].duty_cycle = 0
    pca.deinit()
