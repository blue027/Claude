"""
Simple Auto Clicker

  * Single spot  - pick one place on the screen and click it over and over.
  * Several spots - pick places in order and click them one after another,
                    looping, with a chosen wait between clicks.

Press Esc at any time to stop clicking.

Needs Python 3 and the "pynput" package:  pip install pynput
"""

import itertools
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

try:
    from pynput import keyboard, mouse
except ImportError:
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        "Auto Clicker",
        "The 'pynput' package is missing.\n\n"
        "Open a terminal and run:\n\n    pip install pynput",
    )
    sys.exit(1)


START_DELAY = 1.0      # seconds to wait after pressing Start, before the first click
MIN_INTERVAL = 0.01    # fastest allowed wait between clicks, in seconds

BUTTONS = {
    "Left": mouse.Button.left,
    "Right": mouse.Button.right,
    "Middle": mouse.Button.middle,
}


def enable_dpi_awareness():
    """On Windows, use real pixels so picked spots match where clicks land."""
    if sys.platform != "win32":
        return
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def screen_bounds(root):
    """(x, y, width, height) of the whole desktop, across all monitors if possible."""
    if sys.platform == "win32":
        import ctypes
        metric = ctypes.windll.user32.GetSystemMetrics
        x, y, w, h = metric(76), metric(77), metric(78), metric(79)
        if w and h:
            return x, y, w, h
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def popup_window(root):
    """A borderless, always-on-top window."""
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    return win


class EscWatcher:
    """Watches for the Esc key anywhere, even when this app is not focused."""

    def __init__(self, pressed=None):
        self.pressed = pressed or threading.Event()
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def _on_press(self, key):
        if key == keyboard.Key.esc:
            self.pressed.set()

    def stop(self):
        self._listener.stop()


class SpotPicker:
    """Covers the screen with a see-through layer. Click to pick spots.

    With multiple=False the first click picks the spot and closes the picker.
    With multiple=True every click adds a spot, until Esc or a right-click.
    """

    def __init__(self, root, multiple, on_done):
        self.root = root
        self.multiple = multiple
        self.on_done = on_done
        self.spots = []
        self.markers = []
        self.finished = False
        self.esc_job = None
        self.mouse = mouse.Controller()
        self.esc = EscWatcher()
        self.bold = tkfont.nametofont("TkDefaultFont").copy()
        self.bold.configure(weight="bold")

        self.bx, self.by, self.bw, self.bh = screen_bounds(root)

        self.overlay = popup_window(root)
        self.overlay.geometry(f"{self.bw}x{self.bh}+{self.bx}+{self.by}")
        try:
            self.overlay.attributes("-alpha", 0.3)
        except tk.TclError:
            pass
        canvas = tk.Canvas(self.overlay, bg="black", highlightthickness=0, cursor="crosshair")
        canvas.pack(fill="both", expand=True)
        canvas.bind("<Button-1>", self._on_click)
        canvas.bind("<Button-3>", lambda e: self._finish())
        canvas.bind("<Motion>", self._on_motion)

        self.hint = popup_window(root)
        self.hint_label = tk.Label(self.hint, bg="#222222", fg="white",
                                   justify="left", padx=10, pady=6)
        self.hint_label.pack()
        # A click that lands on the hint still counts as picking that spot.
        self.hint_label.bind("<Button-1>", self._on_click)
        self.hint_label.bind("<Button-3>", lambda e: self._finish())
        self._update_hint()

        self.overlay.focus_force()
        self._watch_esc()

    def _hint_text(self):
        x, y = self.mouse.position
        if self.multiple:
            lines = [
                f"Click the spots in order  (picked: {len(self.spots)})",
                "Esc or right-click when done",
            ]
        else:
            lines = ["Click the spot to auto-click", "Esc or right-click to cancel"]
        return "\n".join(lines + [f"x={int(x)}  y={int(y)}"])

    def _update_hint(self, event=None):
        self.hint_label.config(text=self._hint_text())
        if event is None:
            px, py = (int(v) for v in self.mouse.position)
        else:
            px, py = event.x_root, event.y_root
        self.hint.update_idletasks()
        w, h = self.hint.winfo_reqwidth(), self.hint.winfo_reqheight()
        # Keep the hint beside the cursor, flipping sides near the screen edge.
        x = px + 20 if px + 20 + w < self.bx + self.bw else px - 20 - w
        y = py + 20 if py + 20 + h < self.by + self.bh else py - 20 - h
        self.hint.geometry(f"+{x}+{y}")
        self.hint.lift()

    def _on_motion(self, event):
        self._update_hint(event)

    def _on_click(self, event):
        x, y = self.mouse.position
        self.spots.append((int(x), int(y)))
        if not self.multiple:
            self._finish()
            return
        self._add_marker(len(self.spots), event.x_root, event.y_root)
        for marker in self.markers:
            marker.lift()
        self._update_hint(event)

    def _add_marker(self, number, x, y):
        marker = popup_window(self.root)
        label = tk.Label(marker, text=str(number), bg="#e53935", fg="white",
                         font=self.bold, padx=4)
        label.pack()
        # Clicking on a marker picks that same spot again.
        label.bind("<Button-1>", self._on_click)
        label.bind("<Button-3>", lambda e: self._finish())
        marker.update_idletasks()
        w, h = marker.winfo_reqwidth(), marker.winfo_reqheight()
        marker.geometry(f"+{x - w // 2}+{y - h // 2}")
        self.markers.append(marker)

    def _watch_esc(self):
        if self.esc.pressed.is_set():
            self._finish()
        else:
            self.esc_job = self.overlay.after(50, self._watch_esc)

    def _finish(self):
        if self.finished:
            return
        self.finished = True
        if self.esc_job:
            self.overlay.after_cancel(self.esc_job)
        self.esc.stop()
        for win in self.markers + [self.hint, self.overlay]:
            win.destroy()
        self.on_done(self.spots)


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.single_spot = None
        self.sequence = []
        self.worker = None
        self.esc = None
        self.stop_event = threading.Event()
        self.clicks = 0

        root.title("Auto Clicker")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    # ---- window layout -------------------------------------------------

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        self.tabs = ttk.Notebook(main)
        self.tabs.pack(fill="both", expand=True)
        self._build_single_tab()
        self._build_sequence_tab()

        options = ttk.Frame(main)
        options.pack(fill="x", pady=(10, 0))
        ttk.Label(options, text="Mouse button:").pack(side="left")
        self.button_choice = tk.StringVar(value="Left")
        ttk.Combobox(options, textvariable=self.button_choice, values=list(BUTTONS),
                     state="readonly", width=8).pack(side="left", padx=6)

        self.start_button = ttk.Button(main, text="Start clicking", command=self._start_or_stop)
        self.start_button.pack(fill="x", pady=(10, 4), ipady=6)

        self.status = tk.StringVar(value="Pick a spot, then press Start. Press Esc to stop.")
        ttk.Label(main, textvariable=self.status, foreground="#555555").pack(anchor="w")

    def _build_single_tab(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Single spot")

        ttk.Label(tab, text="Spot:").grid(row=0, column=0, sticky="w")
        self.single_label = ttk.Label(tab, text="not picked yet", width=22)
        self.single_label.grid(row=0, column=1, sticky="w", padx=6)
        ttk.Button(tab, text="Pick spot", command=self._pick_single).grid(row=0, column=2, sticky="e")

        self.single_interval = tk.StringVar(value="0.5")
        self.single_count = tk.StringVar(value="0")
        self._number_row(tab, 1, "Click every", self.single_interval, "seconds")
        self._number_row(tab, 2, "Stop after", self.single_count, "clicks  (0 = until Esc)")
        tab.columnconfigure(1, weight=1)

    def _build_sequence_tab(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Several spots (in order)")

        list_frame = ttk.Frame(tab)
        list_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.spot_list = tk.Listbox(list_frame, height=7, width=30, activestyle="none")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.spot_list.yview)
        self.spot_list.config(yscrollcommand=scroll.set)
        self.spot_list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        buttons = ttk.Frame(tab)
        buttons.grid(row=0, column=3, sticky="n", padx=(8, 0))
        for text, command in [
            ("Add spots", self._pick_sequence),
            ("Remove", self._remove_spot),
            ("Move up", lambda: self._move_spot(-1)),
            ("Move down", lambda: self._move_spot(1)),
            ("Clear all", self._clear_spots),
        ]:
            ttk.Button(buttons, text=text, command=command).pack(fill="x", pady=1)

        self.seq_interval = tk.StringVar(value="0.5")
        self.seq_count = tk.StringVar(value="0")
        self._number_row(tab, 1, "Wait", self.seq_interval, "seconds between clicks")
        self._number_row(tab, 2, "Stop after", self.seq_count, "rounds  (0 = until Esc)")

    def _number_row(self, parent, row, before, var, after):
        ttk.Label(parent, text=before).grid(row=row, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(parent, textvariable=var, width=8).grid(row=row, column=1, sticky="w",
                                                          padx=6, pady=(10, 0))
        ttk.Label(parent, text=after).grid(row=row, column=2, columnspan=2, sticky="w",
                                           pady=(10, 0))

    # ---- picking spots -------------------------------------------------

    def _pick(self, multiple, on_done):
        self.root.withdraw()

        def done(spots):
            self.root.deiconify()
            self.root.lift()
            on_done(spots)

        # Give the window a moment to disappear before covering the screen.
        self.root.after(200, lambda: SpotPicker(self.root, multiple, done))

    def _pick_single(self):
        def done(spots):
            if spots:
                self.single_spot = spots[0]
                x, y = self.single_spot
                self.single_label.config(text=f"x={x}, y={y}")
        self._pick(False, done)

    def _pick_sequence(self):
        def done(spots):
            self.sequence.extend(spots)
            self._refresh_list()
            if spots:
                self.spot_list.see("end")
        self._pick(True, done)

    def _refresh_list(self, select=None):
        self.spot_list.delete(0, "end")
        for i, (x, y) in enumerate(self.sequence, start=1):
            self.spot_list.insert("end", f"{i}.   x={x}, y={y}")
        if select is not None:
            self.spot_list.selection_set(select)
            self.spot_list.see(select)

    def _selected(self):
        picked = self.spot_list.curselection()
        return picked[0] if picked else None

    def _remove_spot(self):
        i = self._selected()
        if i is not None:
            del self.sequence[i]
            self._refresh_list(select=min(i, len(self.sequence) - 1) if self.sequence else None)

    def _move_spot(self, step):
        i = self._selected()
        if i is None or not 0 <= i + step < len(self.sequence):
            return
        seq = self.sequence
        seq[i], seq[i + step] = seq[i + step], seq[i]
        self._refresh_list(select=i + step)

    def _clear_spots(self):
        self.sequence.clear()
        self._refresh_list()

    # ---- clicking ------------------------------------------------------

    def _read_settings(self):
        """Returns (spots, interval, rounds) or None if something is wrong."""
        single = self.tabs.index("current") == 0
        if single:
            spots = [self.single_spot] if self.single_spot else []
            interval_text, count_text = self.single_interval.get(), self.single_count.get()
            if not spots:
                messagebox.showinfo("Auto Clicker", "Pick a spot first.")
                return None
        else:
            spots = list(self.sequence)
            interval_text, count_text = self.seq_interval.get(), self.seq_count.get()
            if not spots:
                messagebox.showinfo("Auto Clicker", "Add at least one spot first.")
                return None

        try:
            interval = float(interval_text.replace(",", "."))
            if interval < MIN_INTERVAL:
                raise ValueError
        except ValueError:
            messagebox.showerror("Auto Clicker",
                                 f"The wait must be a number of seconds, at least {MIN_INTERVAL}.")
            return None
        try:
            rounds = int(count_text)
            if rounds < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Auto Clicker", "'Stop after' must be a whole number (0 or more).")
            return None
        return spots, interval, rounds

    def _start_or_stop(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            return

        settings = self._read_settings()
        if settings is None:
            return
        spots, interval, rounds = settings
        button = BUTTONS[self.button_choice.get()]

        self.clicks = 0
        self.stop_event.clear()
        self.esc = EscWatcher(self.stop_event)
        self.worker = threading.Thread(
            target=self._click_loop, args=(spots, interval, rounds, button), daemon=True)
        self.worker.start()

        self.start_button.config(text="Stop  (Esc)")
        self.status.set("Clicking... press Esc to stop.")
        # Get out of the way so the clicks don't land on this window.
        self.root.iconify()
        self._watch_worker()

    def _click_loop(self, spots, interval, rounds, button):
        """Runs in a background thread. Clicks the spots in order until done or stopped."""
        controller = mouse.Controller()
        stopped = self.stop_event.wait  # True as soon as Esc or Stop is pressed

        if stopped(START_DELAY):
            return
        first = True
        for _ in (itertools.count() if rounds == 0 else range(rounds)):
            for x, y in spots:
                if not first and stopped(interval):
                    return
                first = False
                controller.position = (x, y)
                controller.click(button)
                self.clicks += 1

    def _watch_worker(self):
        if self.worker.is_alive():
            self.root.after(50, self._watch_worker)
            return

        self.esc.stop()
        self.start_button.config(text="Start clicking")
        how = "Stopped" if self.stop_event.is_set() else "Finished"
        self.status.set(f"{how} after {self.clicks} click{'s' if self.clicks != 1 else ''}.")
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _on_close(self):
        self.stop_event.set()
        if self.esc:
            self.esc.stop()
        self.root.destroy()


def main():
    enable_dpi_awareness()
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
