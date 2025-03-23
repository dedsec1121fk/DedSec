#!/usr/bin/env python3
import os
import curses
import shutil
import time

def list_items(path):
    """
    Return a sorted list of items in the directory (directories first, then files).
    """
    try:
        items = os.listdir(path)
        items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        return items
    except Exception as e:
        return []

def safe_addnstr(win, y, x, string, n, attr=0):
    """
    Safely add a string using addnstr. If an error occurs (e.g. if the string doesn't fit),
    it will be caught.
    """
    try:
        win.addnstr(y, x, string, n, attr)
    except curses.error:
        pass

def prompt(stdscr, prompt_str):
    """
    Prompt for user input on the bottom line and return the entered string.
    This version safely writes the prompt, truncating if needed.
    """
    curses.echo()
    max_cols = curses.COLS if curses.COLS > 0 else 80
    max_line = curses.LINES - 1 if curses.LINES > 1 else 0
    safe_addnstr(stdscr, max_line, 0, prompt_str, max_cols)
    stdscr.clrtoeol()
    stdscr.refresh()
    try:
        user_input = stdscr.getstr(max_line, len(prompt_str)).decode("utf-8")
    except Exception:
        user_input = ""
    curses.noecho()
    return user_input

def show_info(stdscr, path, item):
    """
    Display file/directory info (size, last modified, permissions) on the bottom two lines.
    """
    full_path = os.path.join(path, item)
    try:
        stats = os.stat(full_path)
        info = (f"Size: {stats.st_size} bytes | "
                f"Modified: {time.ctime(stats.st_mtime)} | "
                f"Mode: {oct(stats.st_mode)}")
    except Exception as e:
        info = f"Error retrieving info: {e}"
    safe_addnstr(stdscr, curses.LINES - 2, 0, info, curses.COLS)
    stdscr.clrtoeol()
    stdscr.refresh()
    stdscr.getch()  # Wait for any key press

def show_help(stdscr):
    """
    Display help/instructions for using the file manager.
    """
    stdscr.clear()
    help_text = [
        "DedSec File Manager - Help",
        "",
        "Navigation:",
        "  ↑ / ↓         : Move through items",
        "  Enter         : Open directory or show operations menu for files",
        "  b             : Back (pop previous folder from history)",
        "  p             : Previous folder (pop from history)",
        "",
        "Operations (via 'o' or Enter on files):",
        "  Open          : Open file with termux-open or enter directory",
        "  Info          : View file/directory details",
        "  Delete        : Delete an item (confirmation required)",
        "  Rename        : Rename an item",
        "  Copy          : Copy an item to a destination",
        "  Move          : Move an item to a destination",
        "  Cancel        : Cancel operation",
        "",
        "Other Commands:",
        "  n             : Create new file or directory",
        "  s             : Search/filter items (empty resets)",
        "  h             : Show this help screen",
        "  q             : Quit the file manager",
        "",
        "Press any key to return..."
    ]
    for idx, line in enumerate(help_text):
        if idx < curses.LINES - 1:
            safe_addnstr(stdscr, idx, 0, line, curses.COLS)
    stdscr.refresh()
    stdscr.getch()

def operations_menu(stdscr, current_path, item):
    """
    Show a pop-up menu with file/directory operations.
    Returns the chosen option.
    """
    options = ["Open", "Info", "Delete", "Rename", "Copy", "Move", "Cancel"]
    selected = 0
    height = len(options) + 2
    width = max(len(opt) for opt in options) + 4
    start_y = max(0, (curses.LINES - height) // 2)
    start_x = max(0, (curses.COLS - width) // 2)
    win = curses.newwin(height, width, start_y, start_x)
    win.keypad(True)
    win.box()
    while True:
        for i, option in enumerate(options):
            attr = curses.A_REVERSE if i == selected else 0
            safe_addnstr(win, i + 1, 2, option, width - 4, attr)
        win.refresh()
        key = win.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(options) - 1:
            selected += 1
        elif key in [10, 13]:
            return options[selected]
        elif key == 27:  # Escape key cancels.
            return "Cancel"

def dedsec_file_manager(stdscr):
    """
    Main file manager function that runs in the curses window.
    """
    curses.curs_set(0)
    stdscr.keypad(True)
    
    # Set starting folder to the parent of the home directory.
    home = os.path.expanduser("~")
    current_path = os.path.dirname(home)
    history = []  # Stack for previous directories.
    items = list_items(current_path)
    selected = 0
    scroll_offset = 0
    message = ""
    
    while True:
        stdscr.clear()
        header = [
            "DedSec File Manager",
            f"Path: {current_path}",
            ("Keys: ↑/↓ Navigate | Enter: Open/Op. Menu | o: Operations | n: New | "
             "b: Back | p: Prev | s: Search | h: Help | q: Quit")
        ]
        for i, line in enumerate(header):
            attr = curses.A_BOLD if i < 2 else curses.A_DIM
            safe_addnstr(stdscr, i, 0, line, curses.COLS, attr)
        num_header = len(header)
        available_lines = curses.LINES - num_header - 3
        
        # Build display list (add back option if history exists).
        display_items = []
        if history:
            display_items.append("..")
        display_items.extend(items)
        
        # Adjust scroll_offset to keep selected item visible.
        if selected < scroll_offset:
            scroll_offset = selected
        elif selected >= scroll_offset + available_lines:
            scroll_offset = selected - available_lines + 1
        
        for idx in range(scroll_offset, min(len(display_items), scroll_offset + available_lines)):
            line = (idx - scroll_offset) + num_header + 1
            text = f"> {display_items[idx]}" if idx == selected else f"  {display_items[idx]}"
            attr = curses.A_REVERSE if idx == selected else 0
            safe_addnstr(stdscr, line, 2, text, curses.COLS - 2, attr)
        
        if message:
            safe_addnstr(stdscr, curses.LINES - 3, 0, message, curses.COLS)
            stdscr.clrtoeol()
        stdscr.refresh()
        
        key = stdscr.getch()
        message = ""
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(display_items) - 1:
            selected += 1
        elif key == curses.KEY_RESIZE:
            continue
        elif key in (ord('b'), ord('p')):
            if history:
                current_path = history.pop()
                items = list_items(current_path)
                selected = 0
                scroll_offset = 0
            else:
                message = "No previous folder."
        elif key in [10, 13]:
            chosen = display_items[selected]
            if chosen == "..":
                if history:
                    current_path = history.pop()
                    items = list_items(current_path)
                    selected = 0
                    scroll_offset = 0
                else:
                    message = "Already at starting directory."
            else:
                full_path = os.path.join(current_path, chosen)
                if os.path.isdir(full_path):
                    history.append(current_path)
                    current_path = full_path
                    items = list_items(current_path)
                    selected = 0
                    scroll_offset = 0
                else:
                    op = operations_menu(stdscr, current_path, chosen)
                    if op == "Open":
                        os.system(f"termux-open '{full_path}'")
                    elif op == "Info":
                        show_info(stdscr, current_path, chosen)
                    elif op == "Delete":
                        ans = prompt(stdscr, f"Delete '{chosen}'? (y/n): ")
                        if ans.lower() == 'y':
                            try:
                                if os.path.isdir(full_path):
                                    shutil.rmtree(full_path)
                                else:
                                    os.remove(full_path)
                                message = "Deleted successfully."
                            except Exception as e:
                                message = f"Error deleting: {e}"
                    elif op == "Rename":
                        newname = prompt(stdscr, f"Rename '{chosen}' to: ")
                        if newname:
                            target = os.path.join(current_path, newname)
                            if os.path.exists(target):
                                message = "Name already exists."
                            else:
                                try:
                                    os.rename(full_path, target)
                                    message = "Renamed successfully."
                                except Exception as e:
                                    message = f"Error renaming: {e}"
                    elif op == "Copy":
                        dest = prompt(stdscr, f"Copy '{chosen}' to (destination path): ")
                        if dest:
                            try:
                                if os.path.isdir(full_path):
                                    shutil.copytree(full_path, dest)
                                else:
                                    shutil.copy2(full_path, dest)
                                message = "Copied successfully."
                            except Exception as e:
                                message = f"Error copying: {e}"
                    elif op == "Move":
                        dest = prompt(stdscr, f"Move '{chosen}' to (destination path): ")
                        if dest:
                            try:
                                shutil.move(full_path, dest)
                                message = "Moved successfully."
                            except Exception as e:
                                message = f"Error moving: {e}"
                    items = list_items(current_path)
                    selected = 0
                    scroll_offset = 0
        elif key == ord('o'):
            chosen = display_items[selected]
            if chosen == "..":
                if history:
                    current_path = history.pop()
                    items = list_items(current_path)
                    selected = 0
                    scroll_offset = 0
                else:
                    message = "Already at starting directory."
            else:
                full_path = os.path.join(current_path, chosen)
                op = operations_menu(stdscr, current_path, chosen)
                if op == "Open":
                    if os.path.isdir(full_path):
                        history.append(current_path)
                        current_path = full_path
                        items = list_items(current_path)
                        selected = 0
                        scroll_offset = 0
                    else:
                        os.system(f"termux-open '{full_path}'")
                elif op == "Info":
                    show_info(stdscr, current_path, chosen)
                elif op == "Delete":
                    ans = prompt(stdscr, f"Delete '{chosen}'? (y/n): ")
                    if ans.lower() == 'y':
                        try:
                            if os.path.isdir(full_path):
                                shutil.rmtree(full_path)
                            else:
                                os.remove(full_path)
                            message = "Deleted successfully."
                        except Exception as e:
                            message = f"Error deleting: {e}"
                        items = list_items(current_path)
                        selected = 0
                        scroll_offset = 0
                elif op == "Rename":
                    newname = prompt(stdscr, f"Rename '{chosen}' to: ")
                    if newname:
                        target = os.path.join(current_path, newname)
                        if os.path.exists(target):
                            message = "Name already exists."
                        else:
                            try:
                                os.rename(full_path, target)
                                message = "Renamed successfully."
                            except Exception as e:
                                message = f"Error renaming: {e}"
                        items = list_items(current_path)
                elif op == "Copy":
                    dest = prompt(stdscr, f"Copy '{chosen}' to (destination path): ")
                    if dest:
                        try:
                            if os.path.isdir(full_path):
                                shutil.copytree(full_path, dest)
                            else:
                                shutil.copy2(full_path, dest)
                            message = "Copied successfully."
                        except Exception as e:
                            message = f"Error copying: {e}"
                        items = list_items(current_path)
                elif op == "Move":
                    dest = prompt(stdscr, f"Move '{chosen}' to (destination path): ")
                    if dest:
                        try:
                            shutil.move(full_path, dest)
                            message = "Moved successfully."
                        except Exception as e:
                            message = f"Error moving: {e}"
                        items = list_items(current_path)
        elif key == ord('n'):
            kind = prompt(stdscr, "Create File (f) or Directory (d)? ")
            if kind.lower() == 'f':
                fname = prompt(stdscr, "Enter new file name: ")
                if fname:
                    try:
                        with open(os.path.join(current_path, fname), 'w') as f:
                            f.write("")
                        message = "File created."
                    except Exception as e:
                        message = f"Error creating file: {e}"
            elif kind.lower() == 'd':
                dname = prompt(stdscr, "Enter new directory name: ")
                if dname:
                    try:
                        os.mkdir(os.path.join(current_path, dname))
                        message = "Directory created."
                    except Exception as e:
                        message = f"Error creating directory: {e}"
            items = list_items(current_path)
            selected = 0
            scroll_offset = 0
        elif key == ord('s'):
            query = prompt(stdscr, "Search (leave empty to reset): ")
            if query:
                filtered = [f for f in list_items(current_path) if query.lower() in f.lower()]
                if filtered:
                    items = filtered
                    selected = 0
                    scroll_offset = 0
                    message = f"Showing results for '{query}'. Press 'b' to go back."
                else:
                    message = "No matching items found."
            else:
                items = list_items(current_path)
                selected = 0
                scroll_offset = 0
        elif key == ord('h'):
            show_help(stdscr)
        elif key == ord('q'):
            break
        else:
            continue

def main():
    curses.wrapper(dedsec_file_manager)

if __name__ == "__main__":
    main()
