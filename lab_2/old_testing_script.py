"""Donkey Racers Lab 2: bench-test the ESC and steering via a PCA9685."""

import argparse
import time


def pulse_to_duty_cycle(pulse_us, frequency_hz):
    """Convert microseconds to PCA9685 ticks and encode them for Adafruit."""
    ticks = round(pulse_us * frequency_hz * 4096 / 1_000_000)
    return ticks << 4  # Adafruit's 16-bit API stores the 12-bit value here.


def test_cases(args):
    """Try steering alone, then a grid of forward throttle and steering."""
    steering = (
        ("center", args.center_us),
        ("left", args.left_us),
        ("right", args.right_us),
    )
    for direction, pulse_us in steering:
        yield f"Steering only / {direction}", args.neutral_us, pulse_us

    for level, fraction in (("low", 1 / 3), ("medium", 2 / 3), ("upper", 1)):
        throttle_us = round(
            args.neutral_us + fraction * (args.forward_us - args.neutral_us)
        )
        for direction, pulse_us in steering:
            yield f"{level} forward / {direction}", throttle_us, pulse_us


def run_hardware(args, cases):
    import board
    from adafruit_pca9685 import PCA9685

    i2c = board.I2C()
    try:
        pca = PCA9685(i2c, address=args.address)
        try:
            esc = pca.channels[args.esc_channel]
            servo = pca.channels[args.servo_channel]
            esc.duty_cycle = 0
            servo.duty_cycle = 0
            pca.frequency = args.frequency
            frequency = pca.frequency
            neutral = pulse_to_duty_cycle(args.neutral_us, frequency)
            center = pulse_to_duty_cycle(args.center_us, frequency)

            try:
                esc.duty_cycle = neutral
                servo.duty_cycle = center
                print("Holding neutral for ESC arming...", flush=True)
                time.sleep(args.arm_seconds)
                for label, throttle_us, steering_us in cases:
                    print(f"{label}: ESC {throttle_us} us, servo {steering_us} us",
                          flush=True)
                    servo.duty_cycle = pulse_to_duty_cycle(steering_us, frequency)
                    time.sleep(0.25)  # Let the steering settle before throttle.
                    esc.duty_cycle = pulse_to_duty_cycle(throttle_us, frequency)
                    time.sleep(0.6)
                    esc.duty_cycle = neutral
                    time.sleep(1)
            finally:
                # On normal exit, Ctrl+C or an error, try neutral first.
                try:
                    esc.duty_cycle = neutral
                    servo.duty_cycle = center
                    time.sleep(1)
                finally:
                    try:
                        esc.duty_cycle = 0
                    finally:
                        servo.duty_cycle = 0
        finally:
            pca.deinit()
    finally:
        i2c.deinit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--esc-channel", type=int, required=True, choices=range(16))
    parser.add_argument("--servo-channel", type=int, required=True, choices=range(16))
    parser.add_argument("--neutral-us", type=int, required=True, help="Verified ESC stop pulse")
    parser.add_argument("--forward-us", type=int, required=True, help="Approved bench-test throttle limit")
    parser.add_argument("--left-us", type=int, required=True, help="Safe left steering pulse")
    parser.add_argument("--center-us", type=int, required=True, help="Straight steering pulse")
    parser.add_argument("--right-us", type=int, required=True, help="Safe right steering pulse")
    parser.add_argument("--address", type=lambda value: int(value, 0), default=0x40)
    parser.add_argument("--frequency", type=int, default=50, choices=(50, 60))
    parser.add_argument("--arm-seconds", type=int, default=3, choices=range(1, 31))
    parser.add_argument("--run", action="store_true", help="Send PWM; default is preview only")
    args = parser.parse_args()

    if args.esc_channel == args.servo_channel:
        parser.error("ESC and steering must use different PCA9685 channels.")
    if not 0x08 <= args.address <= 0x77:
        parser.error("Enter a valid I2C device address.")
    if not 1000 <= args.neutral_us < args.forward_us <= 2000:
        parser.error("Use the lab's forward PWM range: 1000 <= neutral < forward <= 2000 us.")
    lower, upper = sorted((args.left_us, args.right_us))
    if not 1000 <= lower < args.center_us < upper <= 2000:
        parser.error("Steering center must be between left and right, within 1000–2000 us.")

    cases = list(test_cases(args))
    if not args.run:
        for label, throttle_us, steering_us in cases:
            print(f"{label}: ESC {throttle_us} us, servo {steering_us} us")
        print("Preview only. Add --run when the car is on a stand.")
        return

    print(f"PCA9685 {args.address:#04x} at {args.frequency} Hz; "
          f"ESC channel {args.esc_channel}, servo channel {args.servo_channel}.")
    if input("Raise the car with all wheels clear, then type RUN: ").strip() != "RUN":
        return
    try:
        run_hardware(args, cases)
    except KeyboardInterrupt:
        print("\nTest interrupted.")


if __name__ == "__main__":
    main()
