#!/usr/bin/env python3
"""
Improved Curses Drawing Application

Features:
- Drawing mode toggle
- Adjustable pen size
- Flood fill
- Undo/Redo support
- Rainbow and mirror modes
- Mouse and keyboard interaction

This version uses a DrawingApp class to encapsulate state and behavior.
"""

import curses
import random
from collections import deque
from typing import Optional, Tuple, Dict, List

# Type alias for a cell (color pair, character)
Cell = Tuple[int, str]


class DrawingApp:
    def __init__(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        self.max_y, self.max_x = stdscr.getmaxyx()

        # Initialize curses colors.
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)    # Cursor highlight.
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_BLUE, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_CYAN, -1)
        self.color_pairs = [2, 3, 4, 5, 6]  # Drawing colors.
        self.current_color = random.choice(self.color_pairs)

        # Drawing settings.
        self.pen_size: int = 1
        self.available_brush_chars: List[str] = ["█", "▓", "▒", "░"]
        self.brush_char: str = self.available_brush_chars[0]
        self.drawing_mode: bool = False
        self.rainbow_mode: bool = False
        self.mirror_mode: bool = False
        self.instructions_shown: bool = True

        # Initialize canvas state.
        # Maps (y, x) -> Cell (color, brush_char)
        self.drawn_blocks: Dict[Tuple[int, int], Cell] = {}
        self.undo_stack: List[List[Tuple[Tuple[int, int], Optional[Cell]]]] = []
        self.redo_stack: List[List[Tuple[Tuple[int, int], Optional[Cell]]]] = []

        # Set initial cursor position (ensuring drawing area is below instructions).
        self.cursor_y: int = max(1, self.max_y // 2)
        self.cursor_x: int = self.max_x // 2

        # Setup curses options.
        curses.curs_set(0)
        self.stdscr.clear()
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    def safe_draw(self, y: int, x: int, ch: str, color: Optional[int] = None) -> None:
        """Safely draw a character at (y, x) with an optional color pair."""
        try:
            if color is not None:
                self.stdscr.addstr(y, x, ch, curses.color_pair(color))
            else:
                self.stdscr.addstr(y, x, ch)
        except curses.error:
            pass

    def safe_move(self, y: int, x: int) -> None:
        """Safely move the cursor to (y, x) with clamping."""
        y = max(0, min(y, self.max_y - 1))
        x = max(0, min(x, self.max_x - 1))
        try:
            self.stdscr.move(y, x)
        except curses.error:
            pass

    def get_instructions(self) -> str:
        """Return the instruction string based on current modes."""
        return (
            "Arrow keys/mouse: move | d: toggle drawing mode (currently {}) | "
            "f: flood fill | e: erase area | c: change color | p: change pen size | "
            "x: change brush | u: undo | y: redo | m: toggle rainbow mode (currently {}) | "
            "v: toggle mirror mode (currently {}) | h: toggle instructions | "
            "r: clear canvas | s: save drawing | q: quit"
        ).format("ON" if self.drawing_mode else "OFF",
                 "ON" if self.rainbow_mode else "OFF",
                 "ON" if self.mirror_mode else "OFF")

    def display_instructions(self) -> None:
        """Display or clear the instructions line at the top."""
        self.stdscr.move(0, 0)
        self.stdscr.clrtoeol()
        if self.instructions_shown:
            self.safe_draw(0, 0, self.get_instructions())

    def draw_pen_area(self, highlight: bool = False) -> None:
        """Draw the pen area at the current cursor position."""
        for i in range(self.cursor_y, self.cursor_y + self.pen_size):
            for j in range(self.cursor_x, self.cursor_x + self.pen_size):
                if 1 <= i < self.max_y and 0 <= j < self.max_x:
                    if highlight:
                        self.safe_draw(i, j, self.brush_char, 1)
                    else:
                        cell = self.drawn_blocks.get((i, j))
                        if cell:
                            col, ch = cell
                            self.safe_draw(i, j, ch, col)
                        else:
                            self.safe_draw(i, j, " ")

    def record_changes(self, changes: List[Tuple[Tuple[int, int], Optional[Cell]]]) -> None:
        """Record changes for undo and clear redo stack."""
        if changes:
            self.undo_stack.append(changes)
            self.redo_stack.clear()

    def update_pen_area(self) -> None:
        """Apply drawing (or updating) to the pen area."""
        changes = []
        for i in range(self.cursor_y, self.cursor_y + self.pen_size):
            for j in range(self.cursor_x, self.cursor_x + self.pen_size):
                if 1 <= i < self.max_y and 0 <= j < self.max_x:
                    prev = self.drawn_blocks.get((i, j))
                    changes.append(((i, j), prev))
                    new_color = random.choice(self.color_pairs) if self.rainbow_mode else self.current_color
                    self.drawn_blocks[(i, j)] = (new_color, self.brush_char)
                    self.safe_draw(i, j, self.brush_char, new_color)
                    if self.mirror_mode:
                        mirror_j = self.max_x - j - 1
                        if 0 <= mirror_j < self.max_x:
                            prev_mirror = self.drawn_blocks.get((i, mirror_j))
                            changes.append(((i, mirror_j), prev_mirror))
                            self.drawn_blocks[(i, mirror_j)] = (new_color, self.brush_char)
                            self.safe_draw(i, mirror_j, self.brush_char, new_color)
        self.record_changes(changes)

    def erase_pen_area(self) -> None:
        """Erase the drawing in the pen area."""
        changes = []
        for i in range(self.cursor_y, self.cursor_y + self.pen_size):
            for j in range(self.cursor_x, self.cursor_x + self.pen_size):
                if 1 <= i < self.max_y and 0 <= j < self.max_x:
                    prev = self.drawn_blocks.get((i, j))
                    if (i, j) in self.drawn_blocks:
                        changes.append(((i, j), prev))
                        del self.drawn_blocks[(i, j)]
                        self.safe_draw(i, j, " ")
                    if self.mirror_mode:
                        mirror_j = self.max_x - j - 1
                        if 0 <= mirror_j < self.max_x and (i, mirror_j) in self.drawn_blocks:
                            prev_mirror = self.drawn_blocks.get((i, mirror_j))
                            changes.append(((i, mirror_j), prev_mirror))
                            del self.drawn_blocks[(i, mirror_j)]
                            self.safe_draw(i, mirror_j, " ")
        if changes:
            self.record_changes(changes)

    def iterative_flood_fill(self, start_y: int, start_x: int,
                               target: Optional[Cell], replacement: Cell) -> List[Tuple[Tuple[int, int], Optional[Cell]]]:
        """Perform an iterative flood fill and return the list of changes."""
        stack = deque()
        stack.append((start_y, start_x))
        changes = []
        while stack:
            y, x = stack.pop()
            if y < 1 or y >= self.max_y or x < 0 or x >= self.max_x:
                continue
            if self.drawn_blocks.get((y, x)) != target:
                continue
            changes.append(((y, x), self.drawn_blocks.get((y, x))))
            self.drawn_blocks[(y, x)] = replacement
            self.safe_draw(y, x, replacement[1], replacement[0])
            # Add neighbor cells.
            stack.extend([(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)])
        return changes

    def apply_flood_fill(self) -> None:
        """Apply flood fill from the current cursor position."""
        target = self.drawn_blocks.get((self.cursor_y, self.cursor_x))
        new_color = random.choice(self.color_pairs) if self.rainbow_mode else self.current_color
        replacement = (new_color, self.brush_char)
        if target == replacement:
            return
        changes = self.iterative_flood_fill(self.cursor_y, self.cursor_x, target, replacement)
        self.record_changes(changes)

    def redraw_all(self) -> None:
        """Clear and redraw the entire canvas."""
        self.stdscr.clear()
        self.display_instructions()
        for (i, j), (col, ch) in self.drawn_blocks.items():
            if 1 <= i < self.max_y and 0 <= j < self.max_x:
                self.safe_draw(i, j, ch, col)
        self.draw_pen_area(highlight=True)
        self.safe_move(self.cursor_y, self.cursor_x)
        self.stdscr.refresh()

    def undo_last(self) -> None:
        """Undo the last change."""
        if not self.undo_stack:
            return
        changes = self.undo_stack.pop()
        redo_changes = []
        for (i, j), prev in changes:
            current = self.drawn_blocks.get((i, j))
            redo_changes.append(((i, j), current))
            if prev is None:
                self.drawn_blocks.pop((i, j), None)
                self.safe_draw(i, j, " ")
            else:
                self.drawn_blocks[(i, j)] = prev
                col, ch = prev
                self.safe_draw(i, j, ch, col)
        self.redo_stack.append(redo_changes)

    def redo_last(self) -> None:
        """Redo the last undone change."""
        if not self.redo_stack:
            return
        changes = self.redo_stack.pop()
        undo_changes = []
        for (i, j), prev in changes:
            current = self.drawn_blocks.get((i, j))
            undo_changes.append(((i, j), current))
            if prev is None:
                self.drawn_blocks.pop((i, j), None)
                self.safe_draw(i, j, " ")
            else:
                self.drawn_blocks[(i, j)] = prev
                col, ch = prev
                self.safe_draw(i, j, ch, col)
        self.undo_stack.append(undo_changes)

    def save_drawing(self) -> None:
        """Save the current drawing to a text file."""
        try:
            with open("drawing.txt", "w") as f:
                for i in range(1, self.max_y):
                    line = ""
                    for j in range(self.max_x):
                        cell = self.drawn_blocks.get((i, j))
                        line += cell[1] if cell else " "
                    f.write(line.rstrip() + "\n")
        except Exception as e:
            # Optionally log error e.
            pass

    def process_key(self, key: int) -> bool:
        """
        Process a key press.
        Returns False if the application should exit.
        """
        # Toggle modes and update instructions.
        if key == ord('q'):
            return False
        elif key == ord('d'):
            self.drawing_mode = not self.drawing_mode
        elif key == ord('m'):
            self.rainbow_mode = not self.rainbow_mode
        elif key == ord('v'):
            self.mirror_mode = not self.mirror_mode
        elif key == ord('h'):
            self.instructions_shown = not self.instructions_shown
        elif key == ord('f'):
            self.apply_flood_fill()
        elif key == ord('u'):
            self.undo_last()
        elif key == ord('y'):
            self.redo_last()
        elif key == ord('r'):
            self.drawn_blocks.clear()
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.redraw_all()
            return True
        elif key == ord('s'):
            self.save_drawing()
        elif key == ord('c'):
            self.current_color = random.choice(self.color_pairs)
            if self.drawing_mode:
                self.update_pen_area()
        elif key == ord('p'):
            self.pen_size = self.pen_size + 1 if self.pen_size < 3 else 1
            self.cursor_y = min(self.cursor_y, self.max_y - self.pen_size)
            self.cursor_x = min(self.cursor_x, self.max_x - self.pen_size)
            if self.drawing_mode:
                self.update_pen_area()
        elif key == ord('x'):
            idx = self.available_brush_chars.index(self.brush_char)
            self.brush_char = self.available_brush_chars[(idx + 1) % len(self.available_brush_chars)]
            if self.drawing_mode:
                self.update_pen_area()
        elif key == ord('e'):
            self.erase_pen_area()
        elif key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            # Clear current highlight.
            self.draw_pen_area(highlight=False)
            if key == curses.KEY_UP:
                self.cursor_y = max(1, self.cursor_y - 1)
            elif key == curses.KEY_DOWN:
                self.cursor_y = min(self.max_y - self.pen_size, self.cursor_y + 1)
            elif key == curses.KEY_LEFT:
                self.cursor_x = max(0, self.cursor_x - 1)
            elif key == curses.KEY_RIGHT:
                self.cursor_x = min(self.max_x - self.pen_size, self.cursor_x + 1)
            if self.drawing_mode:
                self.update_pen_area()
        elif key == curses.KEY_MOUSE:
            self.handle_mouse()
        # After handling key, refresh display.
        self.display_instructions()
        self.draw_pen_area(highlight=True)
        self.safe_move(self.cursor_y, self.cursor_x)
        self.stdscr.refresh()
        return True

    def handle_mouse(self) -> None:
        """Handle mouse events."""
        try:
            _, x, y, _, _ = curses.getmouse()
            if y < 1 or x < 0 or y > self.max_y - self.pen_size or x > self.max_x - self.pen_size:
                return
            # Clear previous highlight.
            self.draw_pen_area(highlight=False)
            self.cursor_y, self.cursor_x = y, x
            if self.drawing_mode:
                self.update_pen_area()
        except curses.error:
            pass

    def run(self) -> None:
        """Main loop of the drawing application."""
        # Initial draw.
        self.display_instructions()
        self.draw_pen_area(highlight=True)
        self.safe_move(self.cursor_y, self.cursor_x)
        self.stdscr.refresh()

        while True:
            key = self.stdscr.getch()
            if not self.process_key(key):
                break


def main(stdscr: curses.window) -> None:
    app = DrawingApp(stdscr)
    app.run()


if __name__ == '__main__':
    curses.wrapper(main)

