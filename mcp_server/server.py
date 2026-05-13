from mcp.server.fastmcp import FastMCP

from mcp_server.paint_controller import PaintController

paint = PaintController()

mcp = FastMCP("Paint-MCP")

@mcp.tool()
def open_paint():
    return paint.open_paint()

@mcp.tool()
def draw_rectangle():
    return paint.draw_rectangle()

@mcp.tool()
def set_color(color_name: str):
    return paint.set_color(color_name)

@mcp.tool()
def pick_color(x: int, y: int):
    return paint.pick_color(x, y)

@mcp.tool()
def fill_color(x: int, y: int):
    return paint.fill_color(x, y)

@mcp.tool()
def add_text(text: str):
    return paint.add_text(text)

@mcp.tool()
def save_image():
    return paint.save_image()

if __name__ == "__main__":
    mcp.run()