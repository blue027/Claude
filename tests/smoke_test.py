"""End-to-end check: picks spots through the overlay, clicks them, stops with Esc.

This moves and clicks the real mouse, so only run it on a machine you are not using
(or a virtual display):  python tests/smoke_test.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import autoclicker as ac  # noqa: E402
from pynput import keyboard, mouse  # noqa: E402

clicks = []


def record(x, y, button, pressed):
    if pressed:
        clicks.append((int(x), int(y), button.name))


def main():
    listener = mouse.Listener(on_click=record)
    listener.start()
    listener.wait()

    ac.enable_dpi_awareness()
    root = ac.tk.Tk()
    app = ac.AutoClickerApp(root)
    keys = keyboard.Controller()
    pointer = mouse.Controller()

    def pump(seconds):
        end = time.time() + seconds
        while time.time() < end:
            root.update()
            time.sleep(0.01)

    def press_esc():
        keys.press(keyboard.Key.esc)
        keys.release(keyboard.Key.esc)

    def wait_until_done(timeout):
        end = time.time() + timeout
        while app.worker.is_alive() and time.time() < end:
            pump(0.05)
        pump(0.3)
        assert not app.worker.is_alive(), "clicking did not stop"

    pump(0.5)

    # Pick three spots in order through the overlay, finish with Esc.
    app.tabs.select(1)
    app._pick_sequence()
    pump(1.0)
    wanted = [(150, 160), (400, 300), (600, 450)]
    for spot in wanted:
        pointer.position = spot
        pump(0.2)
        pointer.click(mouse.Button.left)
        pump(0.3)
    press_esc()
    pump(0.8)
    assert app.sequence == wanted, app.sequence
    assert root.state() == "normal", root.state()
    print("picked in order:", app.sequence)

    # Click the sequence twice, 0.1s apart.
    app.seq_interval.set("0.1")
    app.seq_count.set("2")
    clicks.clear()
    app._start_or_stop()
    wait_until_done(10)
    expected = [(x, y, "left") for x, y in wanted] * 2
    assert clicks == expected, clicks
    assert app.status.get() == "Finished after 6 clicks.", app.status.get()
    print("sequence ok:", app.status.get())

    # Pick a single spot, click it forever with the middle button, stop with Esc.
    app._pick_single()
    pump(1.0)
    pointer.position = (321, 234)
    pump(0.2)
    pointer.click(mouse.Button.left)
    pump(0.8)
    assert app.single_spot == (321, 234), app.single_spot
    app.tabs.select(0)
    app.single_interval.set("0.05")
    app.single_count.set("0")
    app.button_choice.set("Middle")
    clicks.clear()
    app._start_or_stop()
    pump(2.0)
    press_esc()
    wait_until_done(3)
    count = len(clicks)
    pump(0.5)
    assert count > 5 and len(clicks) == count, (count, len(clicks))
    assert set(clicks) == {(321, 234, "middle")}, set(clicks)
    assert app.status.get().startswith("Stopped after"), app.status.get()
    print("single spot + Esc ok:", app.status.get())

    listener.stop()
    root.destroy()
    print("ALL OK")


if __name__ == "__main__":
    main()
