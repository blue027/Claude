# Auto Clicker

A small auto clicker for your PC.

- **Single spot**: pick one place on the screen and it gets clicked over and over.
- **Several spots (in order)**: pick several places, and they get clicked one after
  another in that order, looping, with the wait you choose between clicks.
- **Press `Esc` at any time to stop.**

## Getting it

**Easiest (Windows, no Python needed):** download `AutoClicker.exe` from this repo's
**Actions** tab → latest **Build Windows app** run → **Artifacts** →
`AutoClicker-windows`. Unzip it and double-click `AutoClicker.exe`.
Windows may show a "Windows protected your PC" warning because the file isn't signed.
Click **More info → Run anyway**.

**With Python (Windows / Mac / Linux):**

```
pip install pynput
python autoclicker.py
```

On Windows you can also just double-click `run.bat`. It installs `pynput` if it's
missing, then starts the app.

## How to use

### One spot
1. Open the **Single spot** tab and click **Pick spot**.
2. The screen dims. Click the place you want auto-clicked.
3. Set **Click every** (seconds) and **Stop after** (clicks; `0` = keep going until Esc).
4. Click **Start clicking**. The window minimizes and clicking starts after 1 second.
5. Press **Esc** to stop.

### Several spots in order
1. Open the **Several spots (in order)** tab and click **Add spots**.
2. The screen dims. Click each place in the order you want. A numbered red marker
   shows each one. Press **Esc** (or right-click) when you're done.
3. Use **Remove / Move up / Move down / Clear all** to fix the list if needed.
   You can press **Add spots** again to add more at the end.
4. Set **Wait** (seconds between clicks) and **Stop after** (rounds through the whole
   list; `0` = keep going until Esc).
5. Click **Start clicking**, then press **Esc** to stop.

You can switch the **Mouse button** to Right or Middle.

## Notes

- If the game or app you're clicking is running **as administrator**, run the auto
  clicker as administrator too. Otherwise Windows blocks both the clicks and the Esc key.
- The Esc press also reaches whatever app you have open (for example, it might close a
  menu in a game).
- On macOS, allow the app (Terminal/Python) under **System Settings → Privacy &
  Security → Accessibility** and **Input Monitoring**.
- `tests/smoke_test.py` moves and clicks the real mouse to test everything, so only
  run it on a machine you're not using.
