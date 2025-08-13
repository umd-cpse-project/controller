import tkinter as tk
from tkinter import ttk, messagebox

from devices import TMCStepper


class MotorPanel(ttk.LabelFrame):
    def __init__(self, master, name: str, motor, *, max_speed=4000, poll_ms=100):
        super().__init__(master, text=name, padding=(10, 8))
        self.motor = motor
        self.max_speed = max_speed
        self.poll_ms = poll_ms

        # State vars
        self.var_enabled = tk.BooleanVar(value=True)
        self.var_speed   = tk.IntVar(value=min(1000, getattr(self.motor, "target_speed", 1000)))
        self.var_jog     = tk.IntVar(value=200)    # steps per jog
        self.var_goto    = tk.IntVar(value=0)      # absolute steps
        self.var_pos     = tk.IntVar(value=0)      # current position (read-only)
        self.var_target  = tk.IntVar(value=0)      # target (read-only)
        self.var_curspeed= tk.IntVar(value=0)      # current speed (read-only)

        # --- Row 0: enable/disable + stop
        row0 = ttk.Frame(self)
        row0.grid(row=0, column=0, sticky="ew", pady=(0,6))
        ttk.Button(row0, text="Enable", command=self.enable).pack(side="left")
        ttk.Button(row0, text="Disable", command=self.disable).pack(side="left", padx=(6,0))
        ttk.Button(row0, text="STOP", style="Danger.TButton", command=self.stop).pack(side="right")

        # --- Row 1: speed control
        row1 = ttk.Frame(self)
        row1.grid(row=1, column=0, sticky="ew", pady=(0,6))
        ttk.Label(row1, text="Target speed (fullsteps/s):").pack(side="left")
        speed_spin = ttk.Spinbox(row1, from_=0, to=self.max_speed, textvariable=self.var_speed, width=8, increment=10)
        speed_spin.pack(side="left", padx=(6,0))
        ttk.Button(row1, text="Apply", command=self.apply_speed).pack(side="left", padx=(6,0))

        # --- Row 2: jog controls
        row2 = ttk.Frame(self)
        row2.grid(row=2, column=0, sticky="ew", pady=(0,6))
        ttk.Label(row2, text="Jog (steps):").pack(side="left")
        ttk.Spinbox(row2, from_=1, to=100000, textvariable=self.var_jog, width=8, increment=10).pack(side="left", padx=(6,0))
        ttk.Button(row2, text="⟵ Jog -", command=self.jog_negative).pack(side="left", padx=(12,0))
        ttk.Button(row2, text="Jog + ⟶", command=self.jog_positive).pack(side="left", padx=(6,0))

        # --- Row 3: goto absolute
        row3 = ttk.Frame(self)
        row3.grid(row=3, column=0, sticky="ew", pady=(0,6))
        ttk.Label(row3, text="Go to abs (steps):").pack(side="left")
        ttk.Spinbox(row3, from_=-10_000_000, to=10_000_000, textvariable=self.var_goto, width=10, increment=50).pack(side="left", padx=(6,0))
        ttk.Button(row3, text="Go", command=self.goto_abs).pack(side="left", padx=(6,0))
        ttk.Button(row3, text="Set as 0 (offset)", command=self.set_zero).pack(side="left", padx=(12,0))

        # --- Row 4: live readouts
        row4 = ttk.Frame(self)
        row4.grid(row=4, column=0, sticky="ew")
        ttk.Label(row4, text="Pos:").grid(row=0, column=0, sticky="w")
        ttk.Label(row4, textvariable=self.var_pos, width=12, anchor="e").grid(row=0, column=1, sticky="e", padx=(4,12))
        ttk.Label(row4, text="Target:").grid(row=0, column=2, sticky="w")
        ttk.Label(row4, textvariable=self.var_target, width=12, anchor="e").grid(row=0, column=3, sticky="e", padx=(4,12))
        ttk.Label(row4, text="Speed:").grid(row=0, column=4, sticky="w")
        ttk.Label(row4, textvariable=self.var_curspeed, width=8, anchor="e").grid(row=0, column=5, sticky="e")

        # Apply initial speed
        self.apply_speed()

        # Start polling loop to update UI
        self.after(self.poll_ms, self._poll)

    # ---- Commands ----
    def enable(self):
        try:
            self.motor.enable()
            self.var_enabled.set(True)
        except Exception as e:
            messagebox.showerror("Enable failed", str(e))

    def disable(self):
        try:
            self.motor.disable()
            self.var_enabled.set(False)
        except Exception as e:
            messagebox.showerror("Disable failed", str(e))

    def stop(self):
        try:
            self.motor.stop()
        except Exception as e:
            messagebox.showerror("Stop failed", str(e))

    def apply_speed(self):
        try:
            speed = int(self.var_speed.get())
            if speed < 0: speed = 0
            if speed > self.max_speed: speed = self.max_speed
            self.motor.target_speed = speed
            self.var_speed.set(speed)
        except Exception as e:
            messagebox.showerror("Set speed failed", str(e))

    def jog_positive(self):
        try:
            amt = int(self.var_jog.get())
            self.motor.target = self.motor.position + amt
        except Exception as e:
            messagebox.showerror("Jog + failed", str(e))

    def jog_negative(self):
        try:
            amt = int(self.var_jog.get())
            self.motor.target = self.motor.position - amt
        except Exception as e:
            messagebox.showerror("Jog - failed", str(e))

    def goto_abs(self):
        try:
            pos = int(self.var_goto.get())
            self.motor.target = pos
        except Exception as e:
            messagebox.showerror("Goto failed", str(e))

    def set_zero(self):
        """
        Set the current position as 'zero' by shifting the target and goto field.
        (This does NOT change the driver's internal coordinate; it just updates UI fields.)
        """
        try:
            offset = self.motor.position
            # Shift goto to keep same physical location if user presses Go later
            self.var_goto.set(int(self.var_goto.get()) - offset)
            messagebox.showinfo("Zero Set", f"Virtual zero set at current position ({offset} steps).")
        except Exception as e:
            messagebox.showerror("Set zero failed", str(e))

    # ---- Poller ----
    def _poll(self):
        try:
            # Read live state from motor
            self.var_pos.set(getattr(self.motor, "position", 0))
            self.var_target.set(getattr(self.motor, "target", 0))
            self.var_curspeed.set(getattr(self.motor, "speed", 0))
        except Exception:
            # Ignore transient read errors
            pass
        finally:
            self.after(self.poll_ms, self._poll)


class App(tk.Tk):
    def __init__(self, left_motor, right_motor):
        super().__init__()
        self.title("TMC Stepper Debugger")
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self._setup_styles()

        # Layout
        container = ttk.Frame(self, padding=10)
        container.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        # Panels
        self.left_panel  = MotorPanel(container, "Left Motor",  left_motor)
        self.right_panel = MotorPanel(container, "Right Motor", right_motor)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(8,0))

        # Global controls
        global_bar = ttk.Frame(container, padding=(0,8,0,0))
        global_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Button(global_bar, text="Enable ALL", command=self.enable_all).pack(side="left")
        ttk.Button(global_bar, text="Disable ALL", command=self.disable_all).pack(side="left", padx=(6,0))
        ttk.Button(global_bar, text="STOP ALL", style="Danger.TButton", command=self.stop_all).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_styles(self):
        self.style.configure("Danger.TButton", foreground="#a00")

    def enable_all(self):
        self.left_panel.enable()
        self.right_panel.enable()

    def disable_all(self):
        self.left_panel.disable()
        self.right_panel.disable()

    def stop_all(self):
        self.left_panel.stop()
        self.right_panel.stop()

    def on_close(self):
        # Try to stop & disable safely
        try: 
            self.left_panel.stop()
        except Exception:
            pass
        try:
            self.right_panel.stop()
        except Exception:
            pass
        try: 
            self.left_panel.disable()
        except Exception:
            pass
        try: 
            self.right_panel.disable()
        except Exception:
            pass
        self.destroy()


# ---------- WIRE UP YOUR MOTORS HERE ----------
def main():
    uart = "/dev/serial0"

    left = TMCStepper(
        control_pin=21, step_pin=16, dir_pin=20,
        uart=uart,
        current=1600,  # mA
    )
    right = TMCStepper(
        control_pin=5, step_pin=6, dir_pin=13,
        uart=uart,
        current=1600,  # mA
    )

    app = App(left, right)
    app.minsize(720, 320)
    app.mainloop()


if __name__ == "__main__":
    main()
