import os
import shutil
import textwrap
import time

HEADERS = ["ID", "Name", "Description"]
ROWS = [
    [1, "Alice", "Senior engineer working on platform reliability and scaling systems."],
    [2, "Bob", "Frontend developer who loves React and design systems."],
    [3, "Charlie", "Intern - writes tests, fixes bugs, and learns Python!"],
]

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def draw_table(headers, rows):
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    n_cols = len(headers)
    border_space = n_cols * 3 + 1
    col_width = max(5, (terminal_width - border_space) // n_cols)

    def format_cell(content):
        wrapped = textwrap.wrap(str(content), col_width)
        return wrapped or [""]

    table_data = [headers] + rows
    formatted = [[format_cell(c) for c in row] for row in table_data]
    row_heights = [max(len(c) for c in row) for row in formatted]

    def draw_line():
        print("+" + "+".join(["-" * (col_width + 2)] * n_cols) + "+")

    for i, row in enumerate(formatted):
        draw_line()
        for line_index in range(row_heights[i]):
            print(
                "| " + " | ".join(
                    (row[col][line_index] if line_index < len(row[col]) else "").ljust(col_width)
                    for col in range(n_cols)
                ) + " |"
            )
    draw_line()

def render():
    clear_screen()
    draw_table(HEADERS, ROWS)
    print("\nResize the terminal — table will auto-adjust (Ctrl+C to exit).")

def main():
    last_size = shutil.get_terminal_size()
    render()
    try:
        while True:
            time.sleep(0.3)
            current_size = shutil.get_terminal_size()
            if current_size != last_size:
                last_size = current_size
                render()
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
