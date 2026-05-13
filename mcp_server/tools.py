from mcp_server.paint_controller import PaintController

paint = PaintController()

TOOLS = {
    "open_paint":     paint.open_paint,
    "draw_rectangle": paint.draw_rectangle,
    "set_color":      paint.set_color,
    "pick_color":     paint.pick_color,
    "fill_color":     paint.fill_color,
    "add_text":       paint.add_text,
    "save_image":     paint.save_image,
}