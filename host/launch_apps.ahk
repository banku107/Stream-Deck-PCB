; Optional companion script (AutoHotkey v2, Windows).
; Set a key in firmware/keymap.json to {"type": "keys", "keys": ["F13"]} (F14, F15, F16 for
; the others), then map those keys to anything here -- apps, folders, websites, macros.
; Put a shortcut to this file in shell:startup so it runs when you log in.
#Requires AutoHotkey v2.0

F13::Run "notepad.exe"
F14::Run "https://www.google.com"
F15::Run "explorer.exe"
F16::Run "calc.exe"
