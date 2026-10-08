"""Stream Deck PCB firmware (CircuitPython 9+, Raspberry Pi Pico).

The Pico shows up on the computer as a USB keyboard. Each of the 4 keys runs
an action read from keymap.json on the CIRCUITPY drive, so keys can be
re-programmed by editing that file -- no reflashing needed. Saving the file
makes CircuitPython reload this code automatically.

Wiring (see hardware/stream-deck.kicad_sch):
  keys  GP2-GP5 -> switch -> GND   (internal pull-ups, pressed = LOW)
  LEDs  GP6-GP9 -> 330R -> LED -> GND   (HIGH = on, optional)
"""
import json
import time

import board
import digitalio
import usb_hid
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

KEY_PINS = (board.GP2, board.GP3, board.GP4, board.GP5)
LED_PINS = (board.GP6, board.GP7, board.GP8, board.GP9)
KEYMAP_FILE = "/keymap.json"
DEBOUNCE_S = 0.02
RUN_BOX_DELAY_S = 0.4  # time for the Windows Run box to open

# Used when keymap.json is missing or broken: F13-F16 don't exist on normal
# keyboards, so they never clash and can be bound to anything on the PC.
FALLBACK_KEYMAP = [{"type": "keys", "keys": ["F%d" % (13 + i)]} for i in range(4)]

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer = ConsumerControl(usb_hid.devices)


def make_pin(pin, output):
    io = digitalio.DigitalInOut(pin)
    if output:
        io.switch_to_output(value=False)
    else:
        io.switch_to_input(pull=digitalio.Pull.UP)
    return io


def load_keymap():
    try:
        with open(KEYMAP_FILE) as f:
            keys = json.load(f)["keys"]
        if len(keys) < len(KEY_PINS):
            raise ValueError("keymap.json needs %d keys, found %d" % (len(KEY_PINS), len(keys)))
        return keys
    except (OSError, ValueError, KeyError) as e:
        print("Problem with keymap.json (%s); using F13-F16" % e)
        return FALLBACK_KEYMAP


def run(action):
    """Perform one key's action. Raises on a malformed action."""
    kind = action["type"]
    if kind == "keys":
        # A shortcut: every listed key pressed together, e.g. ["CONTROL", "SHIFT", "ESCAPE"]
        keyboard.send(*[getattr(Keycode, name.upper()) for name in action["keys"]])
    elif kind == "text":
        # Type out a string, e.g. an email address or a code snippet
        layout.write(action["text"])
    elif kind == "launch":
        # Windows: open the Run box (Win+R), type the program, website or path, press Enter
        keyboard.send(Keycode.GUI, Keycode.R)
        time.sleep(RUN_BOX_DELAY_S)
        layout.write(action["command"] + "\n")
    elif kind == "media":
        # Media keys, e.g. "PLAY_PAUSE", "MUTE", "VOLUME_INCREMENT", "SCAN_NEXT_TRACK"
        consumer.send(getattr(ConsumerControlCode, action["code"].upper()))
    else:
        raise ValueError("unknown action type %r" % kind)


def flash(leds, times=2, on_s=0.08):
    for _ in range(times):
        for led in leds:
            led.value = True
        time.sleep(on_s)
        for led in leds:
            led.value = False
        time.sleep(on_s)


keys = [make_pin(p, output=False) for p in KEY_PINS]
leds = [make_pin(p, output=True) for p in LED_PINS]
keymap = load_keymap()

# Start-up sweep across the key lights so you can see the board is alive
for led in leds:
    led.value = True
    time.sleep(0.1)
    led.value = False

was_pressed = [False] * len(keys)
while True:
    for i, key in enumerate(keys):
        pressed = not key.value
        if pressed == was_pressed[i]:
            continue
        time.sleep(DEBOUNCE_S)  # ignore contact bounce
        if (not key.value) != pressed:
            continue
        was_pressed[i] = pressed
        leds[i].value = pressed  # light the key while it is held
        if pressed:
            try:
                run(keymap[i])
            except Exception as e:  # a typo in keymap.json shouldn't crash the pad
                print("Key %d action failed: %s" % (i + 1, e))
                flash([leds[i]], times=3)
    time.sleep(0.005)
