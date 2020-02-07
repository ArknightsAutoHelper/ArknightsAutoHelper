from .termsize import get_terminal_size


class TermOp:
    class CursorSaver:
        def __init__(self, op):
            self.op = op

        def __enter__(self):
            self.op.save_cursor()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.op.restore_cursor()

    def __init__(self, fd):
        self.fd = fd
        self._keep_cursor_object = TermOp.CursorSaver(self)
        self.scroll = 0

    def save_cursor(self):
        self.fd.write(b"\0337")

    def restore_cursor(self):
        self.fd.write(b"\0338")

    def keep_cursor(self):
        return self._keep_cursor_object

    def move_cursor(self, x, y):
        self.fd.write(b"\033[%d;%df" % (y, x))

    def set_scroll_area(self, rows):
        w, h = get_terminal_size()
        self.scroll = rows
        # scroll up a bit to avoid visual glitch when the screen area shrinks by one row
        if rows > 0:
            self.fd.write(b"\n" * rows)
        # save cursor
        self.save_cursor()
        # set scroll region (this will place the cursor in the top left)
        self.fd.write(b"\033[0;%dr" % (h - rows))
        # restore cursor but ensure its inside the scrolling area
        self.restore_cursor()
        if rows > 0:
            self.fd.write(b"\033[%dA" % rows)

    def move_to_scroll_area(self):
        w, h = get_terminal_size()
        self.move_cursor(1, h-self.scroll+1)

    def clear_scroll_area(self):
        with self.keep_cursor():
            self.move_to_scroll_area()
            ctl = b'\033[B'.join([b'\033[0m\033[2K'] * self.scroll)
            self.fd.write(ctl)
