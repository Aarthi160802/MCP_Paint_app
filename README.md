# MCP Paint Agent

An AI agent that autonomously controls **Microsoft Paint** using Google Gemini as the LLM backend and Windows UI Automation (pywinauto) for reliable, coordinate-independent tool selection.

---

## Demo

[![MCP Paint Agent Demo](https://img.youtube.com/vi/dpLLvs2DJiA/0.jpg)](https://youtu.be/dpLLvs2DJiA)

---

## Architecture

```
User Input (task)
    └── main.py
            ├── GeminiClient      — sends task + history to Gemini, receives JSON action
            ├── AgentLoop         — step-by-step Perceive → Plan → Act loop
            └── TOOLS (dict)
                    └── PaintController  — executes actions on MS Paint via pywinauto + pyautogui
```

The agent runs a **Perceive → Plan → Act** loop:
1. LLM receives the task and full previous action history
2. LLM responds with a single JSON action
3. Agent dispatches the action to the matching tool
4. Result is logged and appended to history
5. Repeat until `{"action": "finish"}`

---

## Project Structure

```
Assignment-4-MCP_Paint_App/
├── main.py                     # Entry point — reads API key from .env, runs agent
├── requirements.txt            # Python dependencies
├── test.py                     # Mouse coordinate calibration utility
│
├── agent/
│   └── agent_loop.py           # Core loop with step-by-step timing and logging
│
├── config/
│   └── settings.py             # All configurable coordinates, paths, and constants
│
├── llm/
│   ├── gemini_client.py        # Gemini API wrapper with per-step prompt logging
│   └── action_parser.py        # Parses JSON responses from the LLM
│
├── mcp_server/
│   ├── paint_controller.py     # All Paint automation logic (8 tools)
│   ├── tools.py                # TOOLS dict mapping action names to controller methods
│   └── server.py               # FastMCP server (alternative MCP protocol transport)
│
├── prompts/
│   └── system_prompt.py        # System prompt: defines all actions, rules, canvas reference
│
├── utils/
│   ├── logger.py               # Timestamped dual-output logger (file + console)
│   └── windows_utils.py        # win32gui window-finding helper
│
└── logs/                       # Auto-created; one timestamped log file per run
```

---

## Setup

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Configure API key
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```

### 3. Configure save path
Edit `config/settings.py`:
```python
SAVE_PATH = r"C:\Users\YourName\Desktop\paint_output.png"
```

### 4. Run
```
python main.py
```

Enter a task when prompted. Example task using all tools:
```
Open Paint, draw a rectangle, fill the inside of the rectangle with yellow color,
write "Hello" inside it and save the image.
```

---

## Implemented Tools

### `open_paint`
Opens Microsoft Paint, waits for it to load, and maximizes the window.

- **UIA method:** `Application(backend="uia").start("mspaint")`
- **Returns:** `"Paint opened"`

---

### `draw_rectangle`
Selects the Rectangle shape tool and draws it on the canvas by drag.

- **Tool selection:** UIA `ListItem` named `"Rectangle"` in the Shapes panel — fully coordinate-independent
- **Drawing:** `mouseDown → moveTo → mouseUp` (more reliable than `dragTo`)
- **Coordinates (settings.py):** `RECTANGLE_START_X/Y` → `RECTANGLE_END_X/Y`
- **Fallback:** Clicks `RECTANGLE_TOOL_X/Y` if UIA fails
- **Returns:** `"Rectangle drawn"`

---

### `set_color(color_name)`
Sets the active foreground color by name using Paint's **Edit Colors** dialog.

- **Must be called before `fill_color`** when a specific color is required
- **Dialog access:** UIA click on "Edit colors" button → Win32 backend to interact with the embedded classic dialog
- **RGB fields:** Directly targeted by confirmed Win32 control IDs — `Red=706`, `Green=707`, `Blue=708`
- **Supported colors:**

| Name | RGB |
|---|---|
| black | (0, 0, 0) |
| white | (255, 255, 255) |
| red | (255, 0, 0) |
| green | (0, 128, 0) |
| lime | (0, 255, 0) |
| blue | (0, 0, 255) |
| yellow | (255, 255, 0) |
| orange | (255, 165, 0) |
| purple | (128, 0, 128) |
| pink | (255, 192, 203) |
| cyan | (0, 255, 255) |
| magenta | (255, 0, 255) |
| brown | (165, 42, 42) |
| gray / grey | (128, 128, 128) |
| navy | (0, 0, 128) |
| teal | (0, 128, 128) |
| maroon | (128, 0, 0) |

- **Returns:** `"Color set to '<name>' (R=x, G=y, B=z)"`

---

### `fill_color(x, y)`
Flood-fills an enclosed region of the canvas at pixel `(x, y)` with the current foreground color.

- **Tool selection:** UIA `Button` named `"Fill with color"`
- **Tip:** Call `set_color` first to ensure the correct fill color is active
- **Returns:** `"Color filled at (x, y)"`

---

### `pick_color(x, y)`
Activates the eyedropper and samples the color at canvas pixel `(x, y)`, making it the new foreground color.

- **Tool selection:** UIA `Button` named `"Color picker"`
- **Returns:** `"Color picked from (x, y)"`

---

### `add_text(text)`
Selects the Text tool, draws a text box, and types the given text.

- **Auto-resets foreground color to black** before activating the Text tool — ensures text is always readable regardless of any prior `set_color` or `fill_color` calls
- **Tool selection:** UIA `Button` named `"Text"`
- **Text box:** Drag from `TEXT_X/Y` to `TEXT_X+150, TEXT_Y+60`
- **Typing:** `pyautogui.write(text, interval=0.05)`
- **Returns:** `"Text added: <text>"`

---

### `save_image`
Saves the canvas to a file via the Save As dialog.

- **Trigger:** `Ctrl+S` (opens Save As for an Untitled file)
- **Path input:** Full path copied to clipboard via `win32clipboard`, then `Ctrl+A + Ctrl+V` into the filename field — handles backslashes safely
- **Overwrite:** Second `Enter` auto-confirms the overwrite dialog if file already exists
- **Output path:** `SAVE_PATH` in `settings.py`
- **Returns:** `"Image saved to <path>"`

---

### `finish`
Signals the agent loop to stop. Handled entirely in `AgentLoop` — no Paint interaction.

---

## Configuration (`config/settings.py`)

| Setting | Default | Description |
|---|---|---|
| RECTANGLE_TOOL_X/Y | 441, 64 | Fallback pixel coords for Rectangle tool (UIA is primary) |
| TEXT_TOOL_X/Y | 280, 69 | Fallback pixel coords for Text tool |
| RECTANGLE_START_X/Y | 300, 300 | Top-left corner of rectangle on canvas |
| RECTANGLE_END_X/Y | 700, 550 | Bottom-right corner of rectangle on canvas |
| TEXT_X/Y | 400, 380 | Where the text box starts (should be inside the rectangle) |
| SAVE_PATH | Desktop\paint_output.png | Full path where the image is saved |

---

## How Tool Selection Works (UIA vs Coordinates)

```
_click_uia(win, "Rectangle", "ListItem")
    |
    +-- SUCCESS: pywinauto finds control by accessibility name
    |           Works regardless of window size, position, or screen DPI
    |
    +-- FAILURE: falls back to pyautogui.click(RECTANGLE_TOOL_X, RECTANGLE_TOOL_Y)
                 Requires calibrated coordinates for your specific screen setup
```

To recalibrate fallback coordinates:
1. Open Paint manually
2. Run `python test.py` in a second terminal
3. Hover over the toolbar button and note the X, Y
4. Update the relevant setting in `settings.py`

---

## Logging

Each run creates a timestamped log file in `logs/`:
```
logs/run_20260514_103022.log
```

The agent logs every step with full detail:
```
============================================================
AGENT STARTED
Task: Open Paint, draw a rectangle, fill with yellow, write Hello, save
============================================================

--- STEP 1 ---
History so far: 0 action(s) completed
[LLM] Sending task + history to Gemini...
[LLM]   Task            : Open Paint, draw a rectangle...
[LLM]   Actions so far  : 0
[LLM] Response received in 1.23s
[LLM] Raw response:
{"action": "open_paint"}
[PARSE] Action: 'open_paint'  |  Full JSON: {'action': 'open_paint'}
[TOOL] Executing: 'open_paint'
[TOOL] 'open_paint' completed in 4.01s  |  Result: Paint opened

--- STEP 2 ---
[LLM]   Last action     : {'action': 'open_paint'}
[LLM]   Last result     : Paint opened
...
============================================================
AGENT FINISHED after 8 step(s)
============================================================
```

---

## Typical Execution Sequence

For the task `"Open Paint, draw a rectangle, fill the inside with yellow, write Hello inside it, save the image"`:

| Step | Action | Details |
|---|---|---|
| 1 | open_paint | Launches mspaint, maximizes window |
| 2 | draw_rectangle | UIA selects Rectangle ListItem, drags (300,300)→(700,550) |
| 3 | set_color "yellow" | Opens Edit Colors dialog, sets R=255 G=255 B=0 via Win32 IDs |
| 4 | fill_color (500,425) | UIA selects Fill tool, clicks center of rectangle |
| 5 | add_text "Hello" | Auto-sets black, UIA selects Text tool, types "Hello" |
| 6 | save_image | Ctrl+S, clipboard pastes full path, Enter to confirm |
| 7 | finish | Agent loop exits |

---

## Additional Paint Functions (Not Yet Implemented)

These can be added to `PaintController`, registered in `TOOLS` and `server.py`, and added to the system prompt:

| Function | UIA Control | Notes |
|---|---|---|
| draw_circle | ListItem "Oval" | Same drag logic as rectangle |
| draw_line | ListItem "Line" | Same drag logic |
| draw_triangle | ListItem "Triangle" | Same drag logic |
| draw_arrow | ListItem "Right arrow" etc. | Same drag logic |
| erase(x1,y1,x2,y2) | Button "Eraser" | Drag over area |
| crop | Button "Crop" | Select region then click Crop |
| resize_canvas | Button "Resize" | Interact with Resize dialog |
| zoom_in / zoom_out | Button "Zoom in" / "Zoom out" | Single click |
| undo | — | pyautogui.hotkey("ctrl", "z") |
| redo | — | pyautogui.hotkey("ctrl", "y") |
| clear_canvas | — | Ctrl+A then Delete |
| change_brush | Button "Brushes" | Click then select size |
| set_color_rgb(r,g,b) | Button "Edit colors" | Extend set_color with raw RGB input |

All available shape names (verified via live UIA inspection on Windows 11 Paint):
Line, Curve, Oval, Rectangle, Rounded rectangle, Polygon, Triangle, Right triangle,
Diamond, Pentagon, Hexagon, Right arrow, Left arrow, Up arrow, Down arrow,
Four-point star, Five-point star, Six-point star, Rounded rectangular callout,
Oval callout, Cloud callout, Heart, Lightning
