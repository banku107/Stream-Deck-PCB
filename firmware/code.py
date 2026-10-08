"""Stream Deck PCB firmware (CircuitPython, Raspberry Pi Pico).

The Pico acts as a USB keyboard. Keys 1-4 send F13-F16, and each key's LED
lights while it is held.

Wiring:
  keys  GP2-GP5 -> switch -> GND   (internal pull-ups, pressed = LOW)
  LEDs  GP6-GP9 -> 330R -> LED -> GND   (HIGH = on)
"""
import time

import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

KEY_PINS = (board.GP2, board.GP3, board.GP4, board.GP5)
LED_PINS = (board.GP6, board.GP7, board.GP8, board.GP9)
KEYCODES = (Keycode.F13, Keycode.F14, Keycode.F15, Keycode.F16)

keyboard = Keyboard(usb_hid.devices)

keys = []
for pin in KEY_PINS:
    key = digitalio.DigitalInOut(pin)
    key.switch_to_input(pull=digitalio.Pull.UP)
    keys.append(key)

leds = []
for pin in LED_PINS:
    led = digitalio.DigitalInOut(pin)
    led.switch_to_output(value=False)
    leds.append(led)

was_pressed = [False] * 4
while True:
    for i in range(4):
        pressed = not keys[i].value
        if pressed != was_pressed[i]:
            was_pressed[i] = pressed
            leds[i].value = pressed
            if pressed:
                keyboard.press(KEYCODES[i])
            else:
                keyboard.release(KEYCODES[i])
    time.sleep(0.01)  # also acts as debounce
