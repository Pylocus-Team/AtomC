#!/usr/bin/env python3
"""
AtomC Developer Console TUI (v1.0)
Advanced Terminal User Interface for Rynx toolchain orchestration.
"""

import sys
import os
import time
import msvcrt
import shutil
import subprocess
from pathlib import Path

# --- Configuration & Constants ---
PROJECT_NAME = "AtomC Project"
CONSOLE_VERSION = "1.0 (TUI)"

# Force UTF-8 if possible
try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    USE_UNICODE = True
except Exception:
    USE_UNICODE = False

if USE_UNICODE:
    # Box drawing characters (Unicode)
    BOX_H = "─"
    BOX_V = "│"
    BOX_TL = "┌"
    BOX_TR = "┐"
    BOX_BL = "└"
    BOX_BR = "┘"
    BOX_VR = "├"
    BOX_VL = "┤"
    BOX_HT = "┴"
    BOX_HB = "┬"
    BOX_X = "┼"
else:
    # Fallback ASCII
    BOX_H = "-"
    BOX_V = "|"
    BOX_TL = "+"
    BOX_TR = "+"
    BOX_BL = "+"
    BOX_BR = "+"
    BOX_VR = "+"
    BOX_VL = "+"
    BOX_HT = "+"
    BOX_HB = "+"
    BOX_X = "+"

# --- State Management ---
class State:
    def __init__(self):
        self.mode = "COMMAND"  # COMMAND, NAVIGATION
        self.output_lines = []
        self.command_buffer = ""
        self.cursor_pos = 0  # In command buffer
        self.selected_file_index = 0
        self.files_list = []
        self.status_msg = "READY"
        self.last_exit_code = 0
        self.running = True
        self.project_root = os.getcwd()
        self.ensure_dirs()
        self.refresh_file_list()

    def ensure_dirs(self):
        os.makedirs("build", exist_ok=True)
        os.makedirs("bin", exist_ok=True)

    def refresh_file_list(self):
        """Walks src, build, bin to populate explorer."""
        self.files_list = []
        # Add src files
        if os.path.isdir("src"):
            for f in os.listdir("src"):
                self.files_list.append(f"src/{f}")
        # Add build files
        if os.path.isdir("build"):
            for f in os.listdir("build"):
                self.files_list.append(f"build/{f}")
        # Add bin files
        if os.path.isdir("bin"):
            for f in os.listdir("bin"):
                self.files_list.append(f"bin/{f}")
        
        # Also check root examples if strictly following mapped strictue
        # For simplicity, we stick to the 3 main folders for the explorer view as requested
        # But we can add root files if needed.

    def log(self, text, type="INFO"):
        """Adds text to output window."""
        prefix = "  "
        if type == "CMD": prefix = "> "
        elif type == "SUCCESS": prefix = "✔ "
        elif type == "ERROR": prefix = "✖ "
        elif type == "WARN": prefix = "! "
        
        # Split multiline output
        for line in text.split('\n'):
            self.output_lines.append(f"{prefix}{line}")
            
    def clear_log(self):
        self.output_lines = []

# --- Renderer ---
class Renderer:
    def __init__(self, state):
        self.state = state
        # Enable VT100 in Windows (Python 3.8+ usually handles this via colorama or os, 
        # but pure msvcrt/print works in modern Windows Terminal)
        os.system('') 
    
    def clear_screen(self):
        print("\033[2J\033[H", end="")

    def move_cursor(self, y, x):
        print(f"\033[{y};{x}H", end="")

    def draw_box(self, x, y, w, h, title=""):
        # Top
        self.move_cursor(y, x)
        print(BOX_TL + BOX_H * (w - 2) + BOX_TR, end="")
        if title:
            self.move_cursor(y, x + 2)
            print(f" {title} ", end="")
        
        # Sides
        for i in range(1, h - 1):
            self.move_cursor(y + i, x)
            print(BOX_V + " " * (w - 2) + BOX_V, end="")
            
        # Bottom
        self.move_cursor(y + h - 1, x)
        print(BOX_BL + BOX_H * (w - 2) + BOX_BR, end="")

    def render(self):
        w, h = shutil.get_terminal_size((120, 30))
        self.clear_screen()
        
        # 1. Main Frame
        self.draw_box(1, 1, w, h, f"AtomC Developer Console — {PROJECT_NAME}")
        
        # 2. Layout Dimensions
        header_h = 3
        footer_h = 3
        middle_h = h - header_h - footer_h
        
        explorer_w = 30
        output_w = w - explorer_w - 4
        
        # 3. Headers (Tabs area)
        self.move_cursor(2, 3)
        print(f"Current File: {self.get_current_selection()}", end="")
        
        # Separator Line below header
        self.move_cursor(3, 1)
        print(BOX_VR + BOX_H * (w - 2) + BOX_VL, end="")

        # 4. Vertical Separator between Explorer and Output
        for i in range(middle_h):
            self.move_cursor(4 + i, explorer_w + 2)
            print(BOX_V, end="")
            
        # 5. File Explorer Content
        self.move_cursor(4, 3)
        print("\033[1msrc/ build/ bin/\033[0m", end="") # Bold
        for i, f in enumerate(self.state.files_list):
            if 4 + i + 1 >= 4 + middle_h: break # Clip
            self.move_cursor(5 + i, 3)
            marker = "> " if i == self.state.selected_file_index else "  "
            print(f"{marker}{f}", end="")

        # 6. Output Content
        # Draw last N lines that fit
        output_x = explorer_w + 4
        output_h = middle_h - 1
        visible_lines = self.state.output_lines[-output_h:]
        for i, line in enumerate(visible_lines):
            self.move_cursor(4 + i, output_x)
            # Simple color coding
            color = ""
            if "✔" in line: color = "\033[92m" # Green
            elif "✖" in line or "ERROR" in line: color = "\033[91m" # Red
            elif "> " in line: color = "\033[94m" # Blue
            
            clean_line = line[:output_w]
            print(f"{color}{clean_line}\033[0m", end="")

        # 7. Horizontal Separator above Command Palette
        footer_y = h - 2
        self.move_cursor(footer_y - 1, 1)
        print(BOX_VR + BOX_H * (w - 2) + BOX_VL, end="")

        # 8. Command Palette
        self.move_cursor(footer_y, 3)
        prompt = "Command Palette: "
        print(f"{prompt}{self.state.command_buffer}", end="")
        
        # 9. Status Bar
        self.move_cursor(h, 3)
        status = f"Status: {self.state.status_msg} | Errors: {self.state.last_exit_code} | Mode: {self.state.mode}"
        print(status, end="")

        # Cursor placement
        if self.state.mode == "COMMAND":
            self.move_cursor(footer_y, 3 + len(prompt) + self.state.cursor_pos)
        else:
            # Hide cursor mostly
            self.move_cursor(h, w-1)
            
        sys.stdout.flush()

    def get_current_selection(self):
        if 0 <= self.state.selected_file_index < len(self.state.files_list):
            return self.state.files_list[self.state.selected_file_index]
        return "None"

# --- Logic & Toolchain ---
class Logic:
    def __init__(self, state):
        self.state = state
        self.tool_modules = {
            "rxc": "atomc.tools.rxc",
            "rxopt": "atomc.tools.rxopt",
            "rxld": "atomc.tools.rxld",
            "rxrun": "atomc.tools.rxrun",
        }

    def execute_command(self, cmd_line):
        self.state.log(cmd_line, "CMD")
        parts = cmd_line.strip().split()
        if not parts: return

        tool = parts[0].lower()
        args = parts[1:]

        if tool == "exit":
            self.state.running = False
            return
        elif tool == "help":
            self.state.log("Commands: rxc, rxopt, rxld, rxrun, exit")
            return
        elif tool not in self.tool_modules:
            self.state.log(f"Unknown command: {tool}", "ERROR")
            return

        # STRICT REWRITING LOGIC (Same as previous console)
        # We need to map args to build/ dir automatically
        final_args = self.rewrite_args(tool, args)
        if final_args is None: 
            return # rewriting failed/error logged

        # Execute
        try:
            cmd = [sys.executable, "-m", self.tool_modules[tool]] + final_args
            
            # Capture output
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                self.state.log(result.stdout.strip())
            if result.stderr:
                self.state.log(result.stderr.strip(), "ERROR")
            
            self.state.last_exit_code = result.returncode
            if result.returncode == 0:
                self.state.log(f"{tool} finished successfully", "SUCCESS")
                self.state.refresh_file_list() # Files might have changed
            else:
                self.state.log(f"{tool} failed with code {result.returncode}", "ERROR")
                
        except Exception as e:
            self.state.log(str(e), "ERROR")

    def rewrite_args(self, tool, args):
        """Implement strict folder mappings."""
        new_args = []
        input_file = None
        
        # Heuristic Rewrite
        skip = False
        for i, arg in enumerate(args):
            if skip: 
                skip = False
                continue
            
            if arg == "-o":
                if i+1 < len(args):
                    val = Path(args[i+1]).name
                    target = "build"
                    if tool == "rxld": target = "bin"
                    
                    new_args.append("-o")
                    new_args.append(str(Path(target) / val))
                    skip = True
                else:
                    new_args.append(arg)
            elif not arg.startswith("-") and input_file is None:
                # This is the INPUT file
                val = arg # Keep path as user typed for rxc source?
                input_file = val
                
                # Logic:
                # rxc input is source (usually explicit path like src/f.ryx or just f.ryx)
                # rxopt input is .ro (must be in build/)
                # rxld input is .opt.ro (must be in build/)
                # rxrun input is .rxe (must be in bin/)
                
                if tool == "rxc":
                    # Keep user input as is, but verify existence?
                    if not os.path.exists(val):
                        # Try src/
                        if os.path.exists(f"src/{val}"): val = f"src/{val}"
                    new_args.append(val)
                elif tool in ["rxopt", "rxld"]:
                    # Input comes from build
                    name = Path(val).name
                    path = str(Path("build") / name)
                    if not os.path.exists(path):
                        self.state.log(f"RX210/220: Input file not found {path}", "ERROR")
                        return None
                    new_args.append(path)
                elif tool == "rxrun":
                    # Input comes from bin
                    name = Path(val).name
                    path = str(Path("bin") / name)
                    if not os.path.exists(path):
                        self.state.log(f"RX301: Executable not found {path}", "ERROR")
                        return None
                    new_args.append(path)
            else:
                new_args.append(arg)
                
        return new_args

# --- Main App ---
def main():
    state = State()
    renderer = Renderer(state)
    logic = Logic(state)
    
    state.log("Welcome to AtomC TUI. Use command palette below.")
    
    while state.running:
        renderer.render()
        
        # Raw Input Handling (Windows)
        # msvcrt.getch() returns bytes
        ch = msvcrt.getch()
        
        if ch == b'\x00' or ch == b'\xe0': # Special keys
            ch2 = msvcrt.getch()
            # Handle arrows
            if ch2 == b'H': # UP
                state.selected_file_index = max(0, state.selected_file_index - 1)
            elif ch2 == b'P': # DOWN
                state.selected_file_index = min(len(state.files_list) - 1, state.selected_file_index + 1)
        
        elif ch == b'\r': # Enter
            cmd = state.command_buffer.strip()
            state.command_buffer = ""
            state.cursor_pos = 0
            if cmd:
                logic.execute_command(cmd)
                
        elif ch == b'\x08': # Backspace
            if len(state.command_buffer) > 0:
                state.command_buffer = state.command_buffer[:-1]
                state.cursor_pos = len(state.command_buffer)
                
        else:
            try:
                char = ch.decode('utf-8')
                if char.isprintable():
                    state.command_buffer += char
                    state.cursor_pos += 1
            except:
                pass

    # Cleanup
    print("\033[2J\033[H", end="")
    print("AtomC TUI Terminated.")

if __name__ == "__main__":
    main()
