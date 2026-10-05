import os
import ctypes
import psutil
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import pygetwindow as gw
import pyautogui
import pytesseract
from PIL import ImageGrab
import pyperclip
import time
import subprocess

class SystemController:
    def __init__(self):
        # Configure pytesseract path if standard
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # --- Power & Session Management ---
    def shutdown(self):
        os.system("shutdown /s /t 5")
        return "Shutting down the computer in 5 seconds."

    def restart(self):
        os.system("shutdown /r /t 5")
        return "Restarting the computer in 5 seconds."

    def sleep(self):
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Putting computer to sleep."

    def lock_screen(self):
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked."

    def get_battery_status(self):
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = "plugged in" if battery.power_plugged else "on battery"
            return f"The battery is at {percent} percent and is currently {plugged}."
        return "Battery status is unavailable."

    # --- Hardware Control ---
    def set_volume(self, level, mute=False):
        try:
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            if mute:
                volume.SetMute(1, None)
                return "Audio muted."
            else:
                volume.SetMute(0, None)
                # Ensure level is between 0 and 100
                level = max(0, min(100, level))
                # level is roughly -65.25 to 0.0, but we can use scalar 0.0 to 1.0
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                return f"Volume set to {level} percent."
        except Exception as e:
            return f"Failed to adjust volume. {e}"

    def set_brightness(self, level):
        try:
            sbc.set_brightness(level)
            return f"Brightness set to {level} percent."
        except Exception as e:
            return f"Failed to adjust brightness. {e}"

    # --- Window & App Automation ---
    def open_application(self, app_name):
        # Simple start command for common apps
        try:
            subprocess.Popen(f"start {app_name}", shell=True)
            return f"Opening {app_name}."
        except Exception as e:
            return f"Failed to open {app_name}."

    def switch_window(self, window_title_keyword):
        windows = gw.getWindowsWithTitle(window_title_keyword)
        if windows:
            win = windows[0]
            try:
                if win.isMinimized:
                    win.restore()
                win.activate()
                return f"Switched focus to {win.title}."
            except Exception as e:
                return f"Found the window but couldn't activate it."
        return f"Could not find a window matching {window_title_keyword}."

    def close_active_window(self):
        try:
            win = gw.getActiveWindow()
            if win:
                title = win.title
                win.close()
                return f"Closed {title}."
            return "No active window found."
        except Exception as e:
            return "Failed to close the window."

    def type_dictation(self, text):
        try:
            pyautogui.write(text, interval=0.02)
            return "Dictation complete."
        except Exception as e:
            return "Failed to type."

    def read_clipboard(self):
        try:
            text = pyperclip.paste()
            if text:
                return f"Clipboard contains: {text}"
            return "The clipboard is empty."
        except Exception as e:
            return "Failed to read the clipboard."

    # --- Vision & OCR ---
    def read_screen(self):
        try:
            screenshot = ImageGrab.grab()
            text = pytesseract.image_to_string(screenshot)
            text = " ".join(text.split()) # clean up whitespace
            if text:
                # Limit length to avoid infinite reading
                if len(text) > 1000:
                    text = text[:1000] + "... and more."
                return f"I see the following text on screen: {text}"
            return "I couldn't detect any readable text on the screen."
        except Exception as e:
            return "Failed to perform optical character recognition. Ensure Tesseract is installed."
