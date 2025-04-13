# ------------------------------
# New Helper Functions for Browsing Directories
# ------------------------------

def browse_list_menu(stdscr, current_path, root_path):
    """
    Displays a list-style menu that shows folders and Python scripts in the current_path.
    A ".. (Back)" item is shown if not in the root, and ESC returns back.
    """
    curses.curs_set(0)
    # Build a list of items: add a "Back" option if not at the root.
    items = []
    if current_path != root_path:
        items.append(".. (Back)")
    try:
        entries = os.listdir(current_path)
    except Exception as e:
        stdscr.addstr(0, 0, "Error reading directory!")
        stdscr.getch()
        return None
    # List directories and .py files
    folders = sorted([d for d in entries if os.path.isdir(os.path.join(current_path, d))])
    scripts = sorted([f for f in entries if os.path.isfile(os.path.join(current_path, f)) and f.endswith(".py")])
    # Mark folders with a trailing slash
    folders = [d + "/" for d in folders]
    items.extend(folders)
    items.extend(scripts)
    current_row = 0
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        title = f"Browsing: {current_path}"
        stdscr.addstr(1, 2, title[:width-4])
        # Display each item in the list
        for idx, item in enumerate(items):
            x = 4
            y = 3 + idx
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, item[:width-8])
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, item[:width-8])
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(items) - 1:
            current_row += 1
        elif key in [10, 13]:  # Enter key
            selection = items[current_row]
            if selection.startswith(".."):
                return None  # Go back (i.e. exit this level)
            full_path = os.path.join(current_path, selection.rstrip("/"))
            if os.path.isdir(full_path):
                # Recursively browse the selected folder
                result = browse_list_menu(stdscr, full_path, root_path)
                if result is not None:
                    return result
                # Otherwise, continue in the current folder
            elif os.path.isfile(full_path) and full_path.endswith(".py"):
                return full_path  # Selected a script; return its full path
        elif key == 27:  # ESC key pressed
            return None

# ------------------------------
# Modified List Menu Integration
# ------------------------------

def run_list_menu():
    """
    Uses a curses-based list menu that supports folder navigation and ESC as “back.”
    """
    scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    def curses_browse(stdscr):
        selected = browse_list_menu(stdscr, scripts_path, scripts_path)
        return selected
    selected_script = curses.wrapper(curses_browse)
    if not selected_script:
        print("No script selected. Exiting.")
        return
    try:
        ret = os.system(f"cd {os.path.dirname(selected_script)} && python3 {os.path.basename(selected_script)}")
        if (ret >> 8) == 2:
            print("\nScript terminated by KeyboardInterrupt. Exiting gracefully...")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Exiting gracefully...")
        sys.exit(0)

# ------------------------------
# New Helper Function for Grid Menu Browsing
# ------------------------------

def browse_grid_menu(stdscr, current_path, root_path):
    """
    Displays a grid-style menu that shows folders and Python scripts.
    Includes a ".. (Back)" option when not at the root, and supports ESC to go back.
    """
    curses.curs_set(0)
    items = []
    if current_path != root_path:
        items.append(".. (Back)")
    try:
        entries = os.listdir(current_path)
    except Exception as e:
        stdscr.addstr(0, 0, "Error reading directory!")
        stdscr.getch()
        return None
    folders = sorted([d for d in entries if os.path.isdir(os.path.join(current_path, d))])
    scripts = sorted([f for f in entries if os.path.isfile(os.path.join(current_path, f)) and f.endswith(".py")])
    folders = [d + "/" for d in folders]
    items.extend(folders)
    items.extend(scripts)
    friendly_names = items  # The names to display
    num_items = len(items)

    # Initialize colors for grid display
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_MAGENTA, -1)
    curses.init_pair(3, curses.COLOR_WHITE, -1)

    selected_index = 0
    while True:
        stdscr.clear()
        term_height, term_width = stdscr.getmaxyx()
        ICON_WIDTH = max(15, term_width // 5)
        ICON_HEIGHT = max(7, term_height // 6)
        max_cols = term_width // ICON_WIDTH

        # Draw the grid cells
        for idx in range(num_items):
            i = (idx) // max_cols
            j = (idx) % max_cols
            y = i * ICON_HEIGHT
            x = j * ICON_WIDTH
            highlight = (idx == selected_index)
            color = curses.color_pair(1) if highlight else curses.color_pair(2)
            # Draw box borders
            for col in range(x, x+ICON_WIDTH):
                stdscr.addch(y, col, curses.ACS_HLINE, color)
                stdscr.addch(y+ICON_HEIGHT-1, col, curses.ACS_HLINE, color)
            for row in range(y, y+ICON_HEIGHT):
                stdscr.addch(row, x, curses.ACS_VLINE, color)
                stdscr.addch(row, x+ICON_WIDTH-1, curses.ACS_VLINE, color)
            stdscr.addch(y, x, curses.ACS_ULCORNER, color)
            stdscr.addch(y, x+ICON_WIDTH-1, curses.ACS_URCORNER, color)
            stdscr.addch(y+ICON_HEIGHT-1, x, curses.ACS_LLCORNER, color)
            stdscr.addch(y+ICON_HEIGHT-1, x+ICON_WIDTH-1, curses.ACS_LRCORNER, color)
            # Center the item text
            name = friendly_names[idx]
            wrapped = textwrap.wrap(name, ICON_WIDTH-4)
            start_y = y + (ICON_HEIGHT - len(wrapped)) // 2
            for line in wrapped:
                line_x = x + (ICON_WIDTH - len(line)) // 2
                stdscr.addstr(start_y, line_x, line, curses.color_pair(3))
                start_y += 1

        instructions = "Arrow Keys: Move | Enter: Select | ESC: Back"
        stdscr.addstr(term_height-1, 0, instructions[:term_width-1], curses.color_pair(3))
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            if selected_index - max_cols >= 0:
                selected_index -= max_cols
        elif key == curses.KEY_DOWN:
            if selected_index + max_cols < num_items:
                selected_index += max_cols
        elif key == curses.KEY_LEFT:
            if selected_index % max_cols > 0:
                selected_index -= 1
        elif key == curses.KEY_RIGHT:
            if (selected_index % max_cols) < (max_cols - 1) and (selected_index + 1) < num_items:
                selected_index += 1
        elif key in [10, 13]:  # Enter
            selection = items[selected_index]
            if selection.startswith(".."):
                return None
            full_path = os.path.join(current_path, selection.rstrip("/"))
            if os.path.isdir(full_path):
                result = browse_grid_menu(stdscr, full_path, root_path)
                if result is not None:
                    return result
            elif os.path.isfile(full_path) and full_path.endswith(".py"):
                return full_path
        elif key == 27:  # ESC key
            return None

# ------------------------------
# Modified Grid Menu Integration
# ------------------------------

def run_grid_menu():
    """
    Uses a curses-based grid menu that supports folder navigation and ESC to return.
    """
    scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    def curses_browse(stdscr):
        return browse_grid_menu(stdscr, scripts_path, scripts_path)
    selected_script = curses.wrapper(curses_browse)
    if not selected_script:
        print("No script selected. Exiting.")
        return
    try:
        ret = os.system(f"cd {os.path.dirname(selected_script)} && python3 {os.path.basename(selected_script)}")
        if (ret >> 8) == 2:
            print("\nScript terminated by KeyboardInterrupt. Exiting gracefully...")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Exiting gracefully...")
        sys.exit(0)
