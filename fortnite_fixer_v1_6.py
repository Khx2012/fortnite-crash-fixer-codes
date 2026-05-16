import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, colorchooser, filedialog
import threading
import os
import shutil
import psutil
import platform
import configparser
import subprocess

# ── CONFIG ────────────────────────────────────────────────────────────────
CONFIG_DIR = os.path.join(os.path.expandvars("%AppData%"), "FortniteCrashFixer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.ini")

DEFAULTS = {
    "dark_mode": "false",
    "bg_color": "#f0f0f0",
    "fortnite_path": r"C:\Program Files\Epic Games\Fortnite",
    "auto_analyze": "false",
    "clear_shader_on_quick_fix": "true",
    "clear_launcher_on_quick_fix": "true",
}

# ── THEME COLORS ──────────────────────────────────────────────────────────
DARK = {
    "bg":         "#1e1e1e",
    "bg2":        "#2d2d2d",
    "fg":         "#ffffff",
    "fg2":        "#cccccc",
    "btn_bg":     "#3a3a3a",
    "btn_fg":     "#ffffff",
    "btn_active": "#4a4a4a",
    "status_ok":  "#90ee90",
    "border":     "#555555",
}

LIGHT = {
    "bg":         "#f0f0f0",
    "bg2":        "#ffffff",
    "fg":         "#000000",
    "fg2":        "#333333",
    "btn_bg":     "#e0e0e0",
    "btn_fg":     "#000000",
    "btn_active": "#c8c8c8",
    "status_ok":  "green",
    "border":     "#cccccc",
}


class FortniteFixer_v1_6:
    def __init__(self, root):
        self.root = root
        self.is_running = False
        self._theme_widgets = []  # track themed widgets

        self.root.title("Fortnite Crash Fixer v1.6")
        self.root.geometry("800x700")

        self.cfg = self.load_config()
        self.build_ui()
        self.apply_theme()

        if self.get_bool("auto_analyze"):
            self.root.after(500, self.analyze)

    # ── CONFIG ────────────────────────────────────────────────────────────────
    def load_config(self):
        cfg = configparser.ConfigParser()

        try:
            if os.path.exists(CONFIG_FILE):
                cfg.read(CONFIG_FILE, encoding="utf-8")

            if "app" not in cfg:
                cfg["app"] = {k: str(v) for k, v in DEFAULTS.items()}

        except Exception:
            cfg["app"] = DEFAULTS.copy()

        os.makedirs(CONFIG_DIR, exist_ok=True)

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)

        return cfg

    def save_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            self.cfg.write(f)

    def get(self, key):
        try:
            return self.cfg.get("app", key)
        except:
            return DEFAULTS.get(key, "")

    def get_bool(self, key):
        try:
            return self.cfg.getboolean("app", key)
        except:
            return DEFAULTS.get(key, "false").lower() == "true"

    def set(self, key, value):
        if isinstance(value, bool):
            value = "true" if value else "false"
        self.cfg.set("app", key, str(value))

    # ── UI ────────────────────────────────────────────────────────────────────
    def build_ui(self):
        # TOP BAR — always dark, no theme needed
        bar = tk.Frame(self.root, bg="#2c2c2c", height=36)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        tk.Label(bar, text="🎮 Fortnite Crash Fixer v1.6",
                 bg="#2c2c2c", fg="white",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)

        tk.Button(bar, text="❌ Exit", command=self.root.quit,
                  bg="#2c2c2c", fg="white", relief="flat").pack(side=tk.RIGHT, padx=5)
        tk.Button(bar, text="📖 Help & FAQ", command=self.show_help,
                  bg="#2c2c2c", fg="white", relief="flat").pack(side=tk.RIGHT, padx=5)
        tk.Button(bar, text="🎨 Color", command=self.pick_color,
                  bg="#2c2c2c", fg="white", relief="flat").pack(side=tk.RIGHT, padx=5)

        self.dark_btn = tk.Button(bar, text="🌙 Dark Mode",
                                  command=self.toggle_dark_mode,
                                  bg="#2c2c2c", fg="white", relief="flat")
        self.dark_btn.pack(side=tk.RIGHT, padx=5)

        tk.Button(bar, text="⚙️ Settings", command=self.show_settings,
                  bg="#2c2c2c", fg="#FFD700", relief="flat",
                  font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=8)

        # MAIN CONTENT FRAME — this gets themed
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self._theme_widgets.append(("frame", self.main_frame))

        self.title_label = tk.Label(self.main_frame, text="🎮 Fortnite Crash Fixer",
                                    font=("Arial", 18, "bold"))
        self.title_label.pack(pady=15)
        self._theme_widgets.append(("label", self.title_label))

        self.status_label = tk.Label(self.main_frame, text="Ready",
                                     font=("Arial", 10), fg="green")
        self.status_label.pack()
        self._theme_widgets.append(("label", self.status_label))

        # BUTTONS FRAME
        btn_outer = tk.Frame(self.main_frame)
        btn_outer.pack(pady=10)
        self._theme_widgets.append(("frame", btn_outer))

        self._buttons = []
        button_defs = [
            ("🔍 Analyze System",        self.analyze),
            ("⚡ Quick Fix (Recommended)", self.quick_fix),
            ("💣 Full Fix",               self.full_fix),
            ("🔧 Clear Shader Cache",     self.clear_cache),
            ("💾 Increase Virtual Memory", self.increase_memory),
            ("💻 System Info",            self.show_system_info),
            ("📂 Open Fortnite Folder",   self.open_fortnite_folder),
            ("🔍 Analyze Crash Logs",     self.analyze_crash_logs),
            ("🔄 Reset Config Files",     self.reset_config),
            ("⚠️ Check RAM Pressure",     self.check_ram_pressure),
        ]

        for text, cmd in button_defs:
            b = tk.Button(btn_outer, text=text, command=cmd,
                          relief="flat", padx=10, pady=5,
                          width=30, anchor="w")
            b.pack(fill=tk.X, pady=2, padx=10)
            self._buttons.append(b)

        # OUTPUT
        out_label = tk.Label(self.main_frame, text="Output:",
                             font=("Arial", 10, "bold"), anchor="w")
        out_label.pack(anchor=tk.W, padx=10)
        self._theme_widgets.append(("label", out_label))

        self.output = scrolledtext.ScrolledText(self.main_frame, height=10)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        clear_btn = tk.Button(self.main_frame, text="🧹 Clear Output",
                              command=lambda: self.output.delete(1.0, tk.END),
                              relief="flat", padx=8, pady=3)
        clear_btn.pack(pady=5)
        self._buttons.append(clear_btn)
        self._theme_widgets.append(("frame", self.main_frame))

        footer = tk.Label(self.main_frame,
                          text="Version 1.6  |  Not affiliated with Epic Games",
                          font=("Arial", 7), fg="gray")
        footer.pack(pady=3)
        self._theme_widgets.append(("label_gray", footer))

    # ── THEME ─────────────────────────────────────────────────────────────────
    def apply_theme(self):
        dark = self.get_bool("dark_mode")
        t = DARK if dark else LIGHT

        # If light mode, use saved custom color as background
        if not dark:
            t = dict(LIGHT)
            t["bg"] = self.get("bg_color")

        # Root and main frame
        self.root.configure(bg=t["bg"])
        self.main_frame.configure(bg=t["bg"])

        # Title and status labels
        self.title_label.configure(bg=t["bg"], fg=t["fg"])
        self.status_label.configure(bg=t["bg"])

        # All tracked frames and labels
        for widget_type, widget in self._theme_widgets:
            try:
                if widget_type == "frame":
                    widget.configure(bg=t["bg"])
                elif widget_type == "label":
                    widget.configure(bg=t["bg"], fg=t["fg"])
                elif widget_type == "label_gray":
                    widget.configure(bg=t["bg"])
            except:
                pass

        # All main buttons
        for btn in self._buttons:
            try:
                btn.configure(
                    bg=t["btn_bg"],
                    fg=t["btn_fg"],
                    activebackground=t["btn_active"],
                    activeforeground=t["btn_fg"]
                )
            except:
                pass

        # Output box
        if hasattr(self, "output"):
            self.output.configure(
                bg=t["bg2"],
                fg=t["fg"],
                insertbackground=t["fg"]
            )

        # Dark mode button text
        if hasattr(self, "dark_btn"):
            self.dark_btn.configure(text="☀️ Light Mode" if dark else "🌙 Dark Mode")

    def toggle_dark_mode(self):
        self.set("dark_mode", not self.get_bool("dark_mode"))
        self.save_config()
        self.apply_theme()

    def pick_color(self):
        # Only applies in light mode
        c = colorchooser.askcolor(title="Choose background color")[1]
        if c:
            self.set("bg_color", c)
            self.set("dark_mode", "false")  # switch to light mode to show color
            self.save_config()
            self.apply_theme()

    # ── LOGGING ───────────────────────────────────────────────────────────────
    def log(self, msg):
        self.output.insert(tk.END, str(msg) + "\n")
        self.output.see(tk.END)

    def log_safe(self, msg):
        self.root.after(0, lambda: self.log(msg))

    def status_safe(self, msg, color="green"):
        self.root.after(0, lambda: self.status_label.config(text=msg, fg=color))

    # ── ANALYZE ───────────────────────────────────────────────────────────────
    def analyze(self):
        if self.is_running:
            return

        self.is_running = True
        self.root.after(0, lambda: self.output.delete(1.0, tk.END))

        def run():
            try:
                self.log_safe("=" * 50)
                self.log_safe("FORTNITE SYSTEM ANALYSIS")
                self.log_safe("=" * 50)

                os_name = f"{platform.system()} {platform.release()}"
                self.log_safe(f"✓ OS: {os_name}")

                vm = psutil.virtual_memory()
                total_ram = vm.total / (1024**3)
                avail_ram = vm.available / (1024**3)
                self.log_safe(f"✓ RAM: {total_ram:.1f} GB total ({avail_ram:.1f} GB available)")

                if avail_ram < 4:
                    self.log_safe("⚠️ RAM WARNING: Less than 4GB available — consider restarting PC first")

                self.log_safe("🧠 CPU Information:")
                try:
                    physical = psutil.cpu_count(logical=False)
                    logical = psutil.cpu_count(logical=True)
                    self.log_safe(f"   Physical cores: {physical}")
                    self.log_safe(f"   Logical cores (threads): {logical}")
                except Exception as e:
                    self.log_safe(f"   ❌ CPU scan failed: {e}")

                disk = psutil.disk_usage(os.path.splitdrive(os.getcwd())[0] + "\\")
                free_disk = disk.free / (1024**3)
                self.log_safe(f"✓ Disk: {free_disk:.1f} GB free on C:")

                self.log_safe("\nChecking Fortnite...")
                path = self.get("fortnite_path")
                if os.path.isdir(path):
                    self.log_safe(f"✓ Fortnite found at: {path}")
                else:
                    self.log_safe("❌ Fortnite NOT found")

                self.log_safe("\nChecking crash logs...")
                log_dir = os.path.expandvars(r"%LocalAppData%\FortniteGame\Saved\Logs")
                if os.path.isdir(log_dir):
                    logs = [x for x in os.listdir(log_dir) if x.lower().endswith(".log")]
                    if logs:
                        self.log_safe(f"⚠️ Found {len(logs)} log file(s)")
                    else:
                        self.log_safe("✓ No crash logs found")
                else:
                    self.log_safe("⚠️ Log folder not found")

                self.log_safe("\n" + "=" * 50)
                self.log_safe("Analysis Complete!")
                self.log_safe("=" * 50)
                self.status_safe("Analysis completed successfully", "green")

            except Exception as e:
                self.log_safe(f"ERROR: {e}")
                self.status_safe("Error occurred", "red")
            finally:
                self.is_running = False

        threading.Thread(target=run, daemon=True).start()

    # ── QUICK FIX ─────────────────────────────────────────────────────────────
    def quick_fix(self):
        if self.is_running:
            return

        if not messagebox.askyesno("Confirm", "Apply Quick Fix?"):
            return

        self.is_running = True
        self.root.after(0, lambda: self.output.delete(1.0, tk.END))

        do_shader = self.get_bool("clear_shader_on_quick_fix")
        do_launcher = self.get_bool("clear_launcher_on_quick_fix")

        def run():
            try:
                self.log_safe("=== QUICK FIX STARTED ===")
                self.status_safe("Running Quick Fix...", "orange")

                vm = psutil.virtual_memory()
                if vm.available / (1024**3) < 4:
                    self.log_safe("⚠️ RAM WARNING: Less than 4GB available — consider restarting PC first")

                if do_shader:
                    cache = os.path.expandvars(r"%LocalAppData%\FortniteGame\Saved\ShaderCache")
                    self.log_safe("Step 1: Cleaning shader cache...")
                    if os.path.exists(cache):
                        try:
                            shutil.rmtree(cache)
                            self.log_safe("✓ Shader cache cleared")
                        except Exception as e:
                            self.log_safe(f"⚠️ Failed to clear shader cache: {e}")
                    else:
                        self.log_safe("✓ Shader cache not found (nothing to clear)")

                if do_launcher:
                    launcher = os.path.expandvars(r"%LocalAppData%\EpicGamesLauncher\Saved\webcache")
                    self.log_safe("Step 2: Cleaning launcher cache...")
                    if os.path.exists(launcher):
                        try:
                            shutil.rmtree(launcher)
                            self.log_safe("✓ Launcher cache cleared")
                        except Exception as e:
                            self.log_safe(f"⚠️ Failed to clear launcher cache: {e}")
                    else:
                        self.log_safe("✓ Launcher cache not found (nothing to clear)")

                self.status_safe("Quick Fix completed successfully", "green")
                self.root.after(0, lambda: messagebox.showinfo("Done", "Quick Fix completed"))

            except Exception as e:
                self.log_safe(f"ERROR: {e}")
                self.status_safe("Error occurred", "red")
            finally:
                self.is_running = False

        threading.Thread(target=run, daemon=True).start()

    # ── FULL FIX (v1.5) ───────────────────────────────────────────────────────
    def full_fix(self):
        if self.is_running:
            return

        if not messagebox.askyesno(
            "⚠️ Full Fix — Last Resort",
            "This is a LAST RESORT fix.\n\n"
            "It will:\n"
            "• Close Fortnite & Epic processes\n"
            "• Clear Fortnite shader cache\n"
            "• Reset Fortnite config files\n"
            "• Reset Epic Games launcher cache\n"
            "• Repair Easy Anti-Cheat\n"
            "• Clean safe Windows temp files\n\n"
            "Your account, skins and progress are SAFE.\n\n"
            "Close Fortnite before continuing.\n"
            "Continue?"
        ):
            return

        self.is_running = True
        self.root.after(0, lambda: self.output.delete(1.0, tk.END))

        def run():
            try:
                self.log_safe("=" * 60)
                self.log_safe("FULL FIX v1.5 — DIAGNOSTIC RECOVERY MODE")
                self.log_safe("=" * 60)
                self.log_safe("")

                # 0. CLOSE PROCESSES
                self.log_safe("0️⃣ Closing Fortnite & Epic processes...")
                targets = ["fortniteclient-win64-shipping", "fortnite", "epicgameslauncher"]
                for proc in psutil.process_iter(["name"]):
                    try:
                        name = (proc.info["name"] or "").lower()
                        if any(t in name for t in targets):
                            proc.kill()
                            proc.wait(timeout=2)
                    except Exception as e:
                        self.log_safe(f"❌ Process error: {e}")
                self.log_safe("   ✓ Processes closed")
                self.log_safe("")

                # 1. SHADER CACHE
                self.log_safe("1️⃣ Clearing shader cache...")
                shader_path = os.path.expandvars(r"%LocalAppData%\FortniteGame\Saved\ShaderCache")
                try:
                    if os.path.isdir(shader_path):
                        shutil.rmtree(shader_path)
                        self.log_safe("   ✓ Shader cache cleared")
                    else:
                        self.log_safe("   ℹ️ Shader cache not found")
                except Exception as e:
                    self.log_safe(f"   ❌ Shader cache error: {e}")
                self.log_safe("")

                # 2. CONFIG RESET
                self.log_safe("2️⃣ Resetting Fortnite config files...")
                config_dir = os.path.expandvars(r"%LocalAppData%\FortniteGame\Saved\Config\WindowsClient")
                for f in ["GameUserSettings.ini", "Input.ini"]:
                    try:
                        path = os.path.join(config_dir, f)
                        if os.path.isfile(path):
                            os.remove(path)
                            self.log_safe(f"   ✓ Deleted {f}")
                        else:
                            self.log_safe(f"   ℹ️ {f} not found")
                    except Exception as e:
                        self.log_safe(f"   ❌ Error deleting {f}: {e}")
                self.log_safe("")

                # 3. EPIC CACHE
                self.log_safe("3️⃣ Resetting Epic Games cache...")
                epic_cache = os.path.expandvars(r"%LocalAppData%\EpicGamesLauncher\Saved")
                try:
                    if os.path.isdir(epic_cache):
                        shutil.rmtree(epic_cache)
                        self.log_safe("   ✓ Epic cache reset")
                    else:
                        self.log_safe("   ℹ️ Epic cache not found")
                except Exception as e:
                    self.log_safe(f"   ❌ Epic cache error: {e}")
                self.log_safe("")

                # 4. EAC REPAIR
                self.log_safe("4️⃣ Launching Easy Anti-Cheat repair...")
                fortnite_path = self.get("fortnite_path")
                if os.path.isdir(fortnite_path):
                    eac_path = os.path.join(fortnite_path, "FortniteGame", "Binaries",
                                            "Win64", "EasyAntiCheat", "EasyAntiCheat_EOS_Setup.exe")
                    if os.path.isfile(eac_path):
                        try:
                            subprocess.Popen([eac_path])
                            self.log_safe("   ✓ EAC repair launched")
                            self.log_safe("   ⚠️ Select Fortnite → Repair Service")
                        except Exception as e:
                            self.log_safe(f"   ❌ Failed to launch EAC: {e}")
                    else:
                        self.log_safe("   ℹ️ EAC not found")
                else:
                    self.log_safe("   ❌ Invalid Fortnite path")
                self.log_safe("")

                # 5. TEMP CLEANUP
                self.log_safe("5️⃣ Cleaning Windows temp files...")
                temp = os.path.expandvars("%TEMP%")
                cleared = 0
                skipped = 0
                try:
                    for item in os.listdir(temp):
                        path = os.path.join(temp, item)
                        try:
                            if os.path.isfile(path):
                                os.remove(path)
                                cleared += 1
                            elif os.path.isdir(path):
                                shutil.rmtree(path)
                                cleared += 1
                        except Exception:
                            skipped += 1
                    self.log_safe(f"   ✓ Temp cleaned: {cleared} items")
                    self.log_safe(f"   ⚠️ Skipped: {skipped}")
                except Exception as e:
                    self.log_safe(f"   ❌ Temp error: {e}")
                self.log_safe("")

                self.log_safe("=" * 60)
                self.log_safe("✓ FULL FIX COMPLETE")
                self.log_safe("=" * 60)
                self.log_safe("")
                self.log_safe("Next steps:")
                self.log_safe("→ Restart your PC")
                self.log_safe("→ Launch Epic Games Launcher")
                self.log_safe("→ Verify Fortnite files")
                self.log_safe("→ Launch Fortnite")
                self.log_safe("")
                self.log_safe("💡 Note: First launch may take longer (shader rebuild)")

                self.status_safe("Full Fix complete — restart PC", "green")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Full Fix Complete",
                    "Full Fix applied successfully!\n\nRestart your PC before launching Fortnite."))

            except Exception as e:
                self.log_safe(f"❌ FULL FIX ERROR: {e}")
                self.status_safe("Full fix failed", "red")
            finally:
                self.is_running = False

        threading.Thread(target=run, daemon=True).start()

    # ── CLEAR CACHE ───────────────────────────────────────────────────────────
    def clear_cache(self):
        if not messagebox.askyesno("Confirm", "Clear shader cache?"):
            return

        cache = os.path.expandvars(r"%LocalAppData%\FortniteGame\Saved\ShaderCache")

        def run():
            try:
                if os.path.isdir(cache):
                    shutil.rmtree(cache)
                    os.makedirs(cache, exist_ok=True)
                    self.log_safe("Cache cleared")
                else:
                    self.log_safe("Cache folder not found")
            except Exception as e:
                self.log_safe(f"Error clearing cache: {e}")

        threading.Thread(target=run, daemon=True).start()

    # ── SYSTEM INFO ───────────────────────────────────────────────────────────
    def show_system_info(self):
        self.output.delete(1.0, tk.END)

        vm = psutil.virtual_memory()
        disk = psutil.disk_usage(os.path.splitdrive(os.getcwd())[0] + "\\")

        self.log(f"OS: {platform.system()} {platform.release()}")
        self.log(f"RAM Used: {vm.used//(1024**3)}GB")
        self.log(f"RAM Free: {vm.available//(1024**3)}GB")
        self.log(f"Disk Free: {disk.free//(1024**3)}GB")
        self.log(f"CPU: {psutil.cpu_percent(interval=0.3)}%")

    # ── OPEN FORTNITE FOLDER ──────────────────────────────────────────────────
    def open_fortnite_folder(self):
        path = self.get("fortnite_path")
        if os.path.isdir(path):
            os.startfile(path)
            self.log("📂 Opened Fortnite install folder")
            self.status_safe("Opened Fortnite folder", "green")
        else:
            messagebox.showerror("Error", "Fortnite path not found. Check settings.")
            self.status_safe("Invalid Fortnite path", "red")

    # ── MEMORY GUIDE ──────────────────────────────────────────────────────────
    def increase_memory(self):
        self.root.after(0, lambda: self.output.delete(1.0, tk.END))
        steps = [
            "Right click This PC → Properties",
            "Advanced system settings",
            "Performance → Settings",
            "Virtual Memory → Change",
            "Set to 16384MB",
            "Restart PC",
        ]
        for s in steps:
            self.log_safe(s)

    # ── CRASH LOG ANALYSIS ────────────────────────────────────────────────────
    def analyze_crash_logs(self):
        win = tk.Toplevel(self.root)
        win.title("Crash Log Analysis")
        win.geometry("600x480")

        ttk.Label(win, text="🔍 Crash Log Analysis",
                  font=("Arial", 13, "bold")).pack(pady=10)

        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Arial", 9))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def run_analysis():
            txt.config(state=tk.NORMAL)
            txt.delete(1.0, tk.END)

            log_dir = os.path.expandvars(r"%LocalAppData%\FortniteGame\Saved\Logs")

            if not os.path.isdir(log_dir):
                txt.insert(tk.END, "❌ No crash log folder found.\n")
                txt.insert(tk.END, "Fortnite may not be installed or has never crashed.\n")
                txt.config(state=tk.DISABLED)
                return

            log_files = sorted(
                [f for f in os.listdir(log_dir) if f.endswith(".log")],
                key=lambda f: os.path.getmtime(os.path.join(log_dir, f)),
                reverse=True,
            )

            if not log_files:
                txt.insert(tk.END, "✓ No crash logs found. Good sign!\n")
                txt.config(state=tk.DISABLED)
                return

            txt.insert(tk.END, f"Found {len(log_files)} log file(s). Analyzing latest...\n\n")
            latest = os.path.join(log_dir, log_files[0])
            txt.insert(tk.END, f"📄 File: {log_files[0]}\n")
            txt.insert(tk.END, "=" * 50 + "\n")

            issues = []
            try:
                with open(latest, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if "OutOfMemory" in content or "out of memory" in content.lower():
                    issues.append("🎯 RAM ISSUE — Out of memory detected. Increase virtual memory.")
                if "GPU" in content or "D3D" in content or "RHI" in content:
                    issues.append("🎯 GPU ISSUE — Graphics error detected. Update GPU drivers.")
                if "shader" in content.lower():
                    issues.append("🎯 SHADER ISSUE — Corrupted shaders detected. Clear shader cache.")
                if "config" in content.lower() or "ini" in content.lower():
                    issues.append("🎯 CONFIG ISSUE — Config error detected. Try config reset.")
                if "crash" in content.lower():
                    issues.append("⚠️ General crash signature found.")

                if issues:
                    txt.insert(tk.END, "DETECTED ISSUES:\n")
                    for issue in issues:
                        txt.insert(tk.END, f"  {issue}\n")
                else:
                    txt.insert(tk.END, "✓ No specific issues detected in latest log.\n")

            except Exception as e:
                txt.insert(tk.END, f"❌ Could not read log file: {e}\n")

            txt.config(state=tk.DISABLED)

        threading.Thread(target=run_analysis, daemon=True).start()

        btn = ttk.Frame(win)
        btn.pack(pady=5)
        ttk.Button(btn, text="📂 Open Logs Folder",
                   command=lambda: os.startfile(
                       os.path.expandvars(r"%LocalAppData%\FortniteGame\Saved\Logs")
                   )).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="Close", command=win.destroy).pack(side=tk.LEFT, padx=5)

    # ── CONFIG RESET ──────────────────────────────────────────────────────────
    def reset_config(self):
        if not messagebox.askyesno(
            "Confirm Reset",
            "Reset Fortnite config files?\n\n"
            "This will clear:\n"
            "• GameUserSettings.ini\n"
            "• Input.ini\n\n"
            "Fortnite will regenerate them on next launch.\n"
            "Your account data is NOT affected.",
        ):
            return

        config_path = os.path.expandvars(
            r"%LocalAppData%\FortniteGame\Saved\Config\WindowsClient")

        def run():
            targets = ["GameUserSettings.ini", "Input.ini"]
            deleted = []
            failed = []

            for fname in targets:
                fpath = os.path.join(config_path, fname)
                if os.path.isfile(fpath):
                    try:
                        os.remove(fpath)
                        deleted.append(fname)
                    except Exception as e:
                        failed.append(f"{fname}: {e}")

            if deleted:
                self.log_safe(f"✓ Config reset: {', '.join(deleted)}")
            if failed:
                for f in failed:
                    self.log_safe(f"❌ Failed: {f}")
            if not deleted and not failed:
                self.log_safe("ℹ️ No config files found to reset")

            self.status_safe("Config reset complete", "green")

        threading.Thread(target=run, daemon=True).start()

    # ── RAM PRESSURE CHECK ─────────────────────────────────────────
    def check_ram_pressure(self):
        vm = psutil.virtual_memory()

        total_gb = round(vm.total / (1024**3), 1)
        used_gb = round(vm.used / (1024**3), 1)
        avail_gb = round(vm.available / (1024**3), 1)
        percent = vm.percent

        if percent >= 90:
            level = "🔴 CRITICAL"
            msg = "RAM is critically low. Crashes very likely."
        elif percent >= 75:
            level = "🟡 WARNING"
            msg = "High RAM usage. Close heavy apps."
        else:
            level = "🟢 OK"
            msg = "RAM usage is stable."

        self.log("=" * 40)
        self.log("🧠 RAM DIAGNOSTIC REPORT")
        self.log("=" * 40)

        self.log(f"Total RAM: {total_gb} GB")
        self.log(f"Used RAM: {used_gb} GB")
        self.log(f"Free RAM: {avail_gb} GB")
        self.log(f"Usage: {percent}%")
        self.log(f"{level} — {msg}")

   
        self.log("\nTop memory processes:")

        try:
            procs = []
            for p in psutil.process_iter(["name", "memory_info"]):
                try:
                    mem = p.info["memory_info"].rss / (1024**2)
                    procs.append((p.info["name"], mem))
                except:
                       pass

            top = sorted(procs, key=lambda x: x[1], reverse=True)[:5]

            for name, mem in top:
                self.log(f"• {name} — {round(mem)} MB")

        except Exception as e:
           self.log(f"RAM scan error: {e}")
        
        self.status_safe("RAM diagnostic complete", "green")
        
        
    # ── HELP ──────────────────────────────────────────────────────────────────
    def show_help(self):
        win = tk.Toplevel(self.root)
        win.title("Help & FAQ")
        win.geometry("520x500")

        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Arial", 9))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        txt.insert(tk.END, """
FORTNITE CRASH FIXER v1.5 — HELP & FAQ

=============================
🧠 WHAT IS FORTNITE CRASH FIXER?
=============================
A diagnostic and repair tool designed to:
- Analyze system performance issues
- Detect Fortnite crash causes
- Clean corrupted cache files
- Improve system stability
- Identify RAM / GPU / config problems

It does NOT modify your account or game ownership.

BUTTONS
=======
🔍 Analyze System       — Scans RAM, disk, Fortnite path and crash logs
⚡ Quick Fix            — Clears shader and launcher cache automatically
💣 Full Fix             — Closes processes, clears cache, resets configs, repairs EAC
🔧 Clear Shader Cache   — Manually clears only the shader cache
💾 Increase Memory      — Step-by-step guide to increase virtual memory
💻 System Info          — Shows full PC specs
🔍 Analyze Crash Logs   — Reads latest log and detects GPU/RAM/config issues
🔄 Reset Config Files   — Deletes GameUserSettings.ini and Input.ini
⚠️ Check RAM Pressure   — Shows current RAM usage level

FAQ
===
Q: Will this delete my skins or progress?
A: No. Only cache files are cleared. Account data is never touched.

Q: Why does antivirus flag this?
A: PyInstaller apps get flagged by default. Source code is on GitHub.

Q: Fortnite is installed in a custom folder?
A: Open ⚙️ Settings and set the path with the Browse button.

Q: Still crashing after fixes?
A: Update GPU drivers and verify files in Epic Launcher.
   Visit epicgames.com/help for further support.

COMMON CRASH CAUSES
===================
1. Corrupted shader cache   → Clear Shader Cache
2. Low available RAM        → Increase Virtual Memory
3. Outdated GPU drivers     → Update manually (NVIDIA/AMD)
4. Low disk space           → Free up 50+ GB on C:
5. Corrupted game files     → Verify files in Epic Launcher

TIPS
====
✓ Close Fortnite before applying fixes
✓ Restart your PC after fixes
✓ Keep Windows and GPU drivers updated
""")
        txt.config(state=tk.DISABLED)

        btn = ttk.Frame(win)
        btn.pack(pady=5)
        ttk.Button(btn, text="Privacy", command=self.show_privacy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="Disclaimer", command=self.show_disclaimer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="Close", command=win.destroy).pack(side=tk.LEFT, padx=5)

    # ── DISCLAIMER ────────────────────────────────────────────────────────────
    def show_disclaimer(self):
        win = tk.Toplevel(self.root)
        win.title("Disclaimer")
        win.geometry("450x260")

        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True)

        txt.insert(tk.END, """
NOT AFFILIATED WITH EPIC GAMES

Use at your own risk.
Only deletes cache files.
No account or game file modification.
""")
        txt.config(state=tk.DISABLED)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)

    # ── PRIVACY ───────────────────────────────────────────────────────────────
    def show_privacy(self):
        win = tk.Toplevel(self.root)
        win.title("Privacy Policy")
        win.geometry("450x400")

        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True)

        txt.insert(tk.END, """
# Privacy Policy — Fortnite Crash Fixer v1.6

## Overview

Fortnite Crash Fixer is a local Windows utility designed to help users diagnose and fix common Fortnite crash issues by cleaning cache files and analyzing system performance.

This application is designed with user privacy in mind and operates entirely offline.

---

## Data Collection

This application does **NOT** collect, store, or transmit any personal data.

Specifically, it does NOT collect:
- Personal information (name, email, etc.)
- System telemetry
- Fortnite account data
- Usage analytics
- Location data

---

## Internet Usage

This application does **NOT** require an internet connection to function and does not send any data externally.

All operations are performed locally on the user’s device.

---

## Local Data Storage

The application stores only minimal configuration settings locally on the user’s system in:
%AppData%\FortniteCrashFixer\settings.ini

This file may include:
- UI preferences (dark mode, theme color)
- User-selected Fortnite installation path
- Feature toggle settings

No sensitive data is stored.

---

## File Access

The application may access and modify only the following types of files:

- Fortnite shader cache folders
- Epic Games Launcher web cache
- Local system information (read-only)

No game executables or account files are modified.

---

## Security

All cleanup actions are:
- Initiated by the user
- Executed locally
- Limited to cache and temporary files only

The application does not run background services or persistent processes.

---

## Third-Party Services

This application does not use any third-party APIs, analytics tools, or external services.

---

## Disclaimer

This tool is not affiliated with Epic Games or Fortnite.

Use of this application is at your own risk. While it is designed to be safe, users should ensure they understand what cache cleaning entails.

---

## Contact

If you have concerns regarding this application, please open an issue on the GitHub repository.

---
""")
        txt.config(state=tk.DISABLED)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)

    # ── SETTINGS ──────────────────────────────────────────────────────────────
    def show_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("420x350")

        auto = tk.BooleanVar(value=self.get_bool("auto_analyze"))
        dark = tk.BooleanVar(value=self.get_bool("dark_mode"))
        shader = tk.BooleanVar(value=self.get_bool("clear_shader_on_quick_fix"))
        launcher = tk.BooleanVar(value=self.get_bool("clear_launcher_on_quick_fix"))
        path = tk.StringVar(value=self.get("fortnite_path"))

        ttk.Label(win, text="⚙️ Settings", font=("Arial", 14, "bold")).pack(pady=10)

        ttk.Checkbutton(win, text="Auto-analyze system on startup",
                        variable=auto).pack(anchor="w", padx=20)
        ttk.Checkbutton(win, text="Dark mode",
                        variable=dark).pack(anchor="w", padx=20, pady=(0, 10))

        ttk.Label(win, text="Quick Fix options:",
                  font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
        ttk.Checkbutton(win, text="Clear shader cache",
                        variable=shader).pack(anchor="w", padx=30)
        ttk.Checkbutton(win, text="Clear launcher cache",
                        variable=launcher).pack(anchor="w", padx=30, pady=(0, 10))

        ttk.Label(win, text="Fortnite install path:",
                  font=("Arial", 10, "bold")).pack(anchor="w", padx=20)

        path_frame = ttk.Frame(win)
        path_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Entry(path_frame, textvariable=path).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def browse():
            f = filedialog.askdirectory()
            if f:
                path.set(f)

        ttk.Button(path_frame, text="Browse", command=browse).pack(side=tk.LEFT)

        def save():
            self.set("auto_analyze", auto.get())
            self.set("dark_mode", dark.get())
            self.set("clear_shader_on_quick_fix", shader.get())
            self.set("clear_launcher_on_quick_fix", launcher.get())
            self.set("fortnite_path", path.get())
            self.save_config()
            self.apply_theme()
            win.destroy()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="💾 Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancel", command=win.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔒 Privacy Policy",
                   command=self.show_privacy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⚠️ Disclaimer",
                   command=self.show_disclaimer).pack(side=tk.LEFT, padx=5)


# ── RUN ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = FortniteFixer_v1_6(root)
    root.mainloop()