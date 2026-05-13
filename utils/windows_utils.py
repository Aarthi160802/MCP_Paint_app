import win32gui

def find_window(title_keyword):

    hwnds = []

    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)

        if title_keyword.lower() in title.lower():
            hwnds.append(hwnd)

    win32gui.EnumWindows(callback, None)

    return hwnds[0] if hwnds else None