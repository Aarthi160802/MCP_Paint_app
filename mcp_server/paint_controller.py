import ctypes
import time

import pyautogui
from pywinauto import Application

from config.settings import *
from utils.logger import logger

# Make pyautogui use physical pixel coordinates (matches pywinauto UIA coords)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Named colors → (R, G, B)
COLOR_MAP = {
    "black":   (0,   0,   0),
    "white":   (255, 255, 255),
    "red":     (255, 0,   0),
    "green":   (0,   128, 0),
    "lime":    (0,   255, 0),
    "blue":    (0,   0,   255),
    "yellow":  (255, 255, 0),
    "orange":  (255, 165, 0),
    "purple":  (128, 0,   128),
    "pink":    (255, 192, 203),
    "cyan":    (0,   255, 255),
    "magenta": (255, 0,   255),
    "brown":   (165, 42,  42),
    "gray":    (128, 128, 128),
    "grey":    (128, 128, 128),
    "navy":    (0,   0,   128),
    "teal":    (0,   128, 128),
    "maroon":  (128, 0,   0),
}

# Win32 control IDs inside Paint's "Edit Colors" dialog (ChooseColor API)
_CTRL_RED   = 706
_CTRL_GREEN = 707
_CTRL_BLUE  = 708


class PaintController:

    def __init__(self):
        self.app = None

    def _get_window(self):
        """Connect to the running Paint window via UIA."""
        try:
            if self.app is None:
                self.app = Application(backend="uia").connect(title_re=".*Paint.*")
            return self.app.top_window()
        except Exception as e:
            logger.error(f"Could not connect to Paint window: {e}")
            return None

    def focus_paint_window(self):
        logger.info("Focusing Paint window")
        win = self._get_window()
        if win:
            win.set_focus()
            time.sleep(0.5)
            return True
        return False

    def open_paint(self):
        logger.info("Opening Paint")
        self.app = Application(backend="uia").start("mspaint")
        time.sleep(3)
        win = self.app.top_window()
        win.maximize()
        time.sleep(1)
        return "Paint opened"

    def _click_uia(self, win, title, control_type):
        """Click a UIA control by title and type. Returns True on success."""
        try:
            ctrl = win.child_window(title=title, control_type=control_type)
            ctrl.click_input()
            logger.info(f"Clicked UIA {control_type}: '{title}'")
            return True
        except Exception:
            return False

    def draw_rectangle(self):
        logger.info("Drawing rectangle")
        win = self._get_window()
        if win is None:
            return "Error: Paint window not found"
        win.set_focus()
        time.sleep(0.5)

        # Rectangle is a ListItem in the Shapes panel — use UIA (coordinate-independent).
        found = self._click_uia(win, "Rectangle", "ListItem")
        if not found:
            logger.warning("UIA ListItem 'Rectangle' not found — falling back to coordinates")
            pyautogui.click(RECTANGLE_TOOL_X, RECTANGLE_TOOL_Y)
        time.sleep(0.5)

        # Draw rectangle: explicit mouseDown → moveTo → mouseUp
        pyautogui.moveTo(RECTANGLE_START_X, RECTANGLE_START_Y, duration=0.4)
        time.sleep(0.2)
        pyautogui.mouseDown(button="left")
        time.sleep(0.2)
        pyautogui.moveTo(RECTANGLE_END_X, RECTANGLE_END_Y, duration=1.5)
        time.sleep(0.2)
        pyautogui.mouseUp(button="left")
        time.sleep(1)

        # Click somewhere neutral to deselect the shape tool
        pyautogui.click(RECTANGLE_START_X - 50, RECTANGLE_START_Y - 50)
        time.sleep(0.3)
        return "Rectangle drawn"

    def add_text(self, text):
        logger.info(f"Writing text: {text}")
        win = self._get_window()
        if win is None:
            return "Error: Paint window not found"

        # Always write text in black regardless of the current foreground color
        self.set_color("black")

        win.set_focus()
        time.sleep(0.5)

        # Text is a Button in the toolbar
        found = self._click_uia(win, "Text", "Button")
        if not found:
            logger.warning("UIA Button 'Text' not found — falling back to coordinates")
            pyautogui.click(TEXT_TOOL_X, TEXT_TOOL_Y)
        time.sleep(0.5)

        # Draw a text box inside the rectangle
        pyautogui.moveTo(TEXT_X, TEXT_Y, duration=0.3)
        time.sleep(0.2)
        pyautogui.mouseDown(button="left")
        time.sleep(0.2)
        pyautogui.moveTo(TEXT_X + 150, TEXT_Y + 60, duration=0.5)
        time.sleep(0.2)
        pyautogui.mouseUp(button="left")
        time.sleep(0.5)

        # Type the text
        pyautogui.write(text, interval=0.05)
        time.sleep(1)

        # Click outside the text box to commit it
        pyautogui.click(RECTANGLE_START_X - 50, RECTANGLE_START_Y - 50)
        time.sleep(0.5)
        return f"Text added: {text}"

    def set_color(self, color_name: str):
        key = color_name.lower().strip()
        if key not in COLOR_MAP:
            supported = ", ".join(sorted(COLOR_MAP.keys()))
            return f"Error: Unknown color '{color_name}'. Supported: {supported}"

        r, g, b = COLOR_MAP[key]
        logger.info(f"Setting foreground color to '{color_name}' (R={r}, G={g}, B={b})")

        win = self._get_window()
        if win is None:
            return "Error: Paint window not found"
        win.set_focus()
        time.sleep(0.5)

        # Open the Edit Colors dialog via UIA
        self._click_uia(win, "Edit colors", "Button")
        time.sleep(1.5)

        # The dialog is a Win32 dialog embedded inside Paint — use win32 backend to target it
        app_win32 = Application(backend="win32").connect(process=self.app.process)
        dlg = app_win32.window(title="Edit Colors")
        dlg.wait("ready", timeout=5)

        # Set Red, Green, Blue using confirmed Win32 control IDs (706, 707, 708)
        for ctrl_id, value in [(_CTRL_RED, r), (_CTRL_GREEN, g), (_CTRL_BLUE, b)]:
            field = dlg.child_window(control_id=ctrl_id)
            field.set_edit_text(str(value))
            time.sleep(0.1)

        # Confirm
        dlg.child_window(title="OK").click_input()
        time.sleep(0.5)

        logger.info(f"Foreground color set to '{color_name}' (R={r}, G={g}, B={b})")
        return f"Color set to '{color_name}' (R={r}, G={g}, B={b})"

    def pick_color(self, x: int, y: int):
        logger.info(f"Picking color from canvas position ({x}, {y})")
        win = self._get_window()
        if win is None:
            return "Error: Paint window not found"
        win.set_focus()
        time.sleep(0.5)

        found = self._click_uia(win, "Color picker", "Button")
        if not found:
            logger.warning("UIA Button 'Color picker' not found — tool may not activate")
        time.sleep(0.5)

        pyautogui.click(x, y)
        logger.info(f"Sampled color at ({x}, {y}) — now set as foreground color")
        time.sleep(0.5)
        return f"Color picked from ({x}, {y})"

    def fill_color(self, x: int, y: int):
        logger.info(f"Filling region at ({x}, {y}) with current foreground color")
        win = self._get_window()
        if win is None:
            return "Error: Paint window not found"
        win.set_focus()
        time.sleep(0.5)

        found = self._click_uia(win, "Fill with color", "Button")
        if not found:
            logger.warning("UIA Button 'Fill with color' not found — tool may not activate")
        time.sleep(0.5)

        pyautogui.click(x, y)
        logger.info(f"Flood-fill applied at ({x}, {y})")
        time.sleep(0.5)
        return f"Color filled at ({x}, {y})"

    def save_image(self):
        import win32clipboard

        logger.info(f"Saving image to: {SAVE_PATH}")
        win = self._get_window()
        if win is None:
            return "Error: Paint window not found"
        win.set_focus()
        time.sleep(0.5)

        # Ctrl+S opens the Save As dialog for an Untitled file
        pyautogui.hotkey("ctrl", "s")
        time.sleep(2)

        # Copy the full path to the clipboard (handles backslashes safely)
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(SAVE_PATH, win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        time.sleep(0.2)

        # Select all text in the filename field and paste the path
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)

        # Press Enter to confirm save
        pyautogui.press("enter")
        time.sleep(1.5)

        # Press Enter again to confirm overwrite if the file already exists
        pyautogui.press("enter")
        time.sleep(1)

        logger.info(f"Image saved to {SAVE_PATH}")
        return f"Image saved to {SAVE_PATH}"