import inspect
import datetime
import os
import re
import shutil
import textwrap
import weakref
from .utils import COLOR_MAP

# Global registry to track all active Logsy instances
_active_loggers = weakref.WeakSet()

def _cleanup_all_tables():
    """Close all active table loggers."""
    for logger in list(_active_loggers):
        if logger.table_view and logger._header_printed and not logger._footer_printed:
            logger._print_table_footer()

class Logsy:
    DEFAULT_COLORS = {
        "INFO": COLOR_MAP["blue"],
        "WARNING": COLOR_MAP["yellow"],
        "ERROR": COLOR_MAP["red"],
        "DEBUG": COLOR_MAP["cyan"],
    }

    def __init__(self, with_time=True, log_to_file=True, file_path="logs/app.log", use_color=True, custom_colors=None, log_to_console=True, table_view=False, table_title=None):
        """
        Args:
            with_time (bool): include timestamp in logs.
            log_to_file (bool): save logs to file.
            file_path (str): log file path (default: logs/app.log).
            use_color (bool): print logs with colors (default: True).
            custom_colors (dict): user-defined color codes for log levels.
                                  Example: {"INFO": "\033[94m"}
        """
        self.with_time = with_time
        self.log_to_file = log_to_file
        self.file_path = file_path
        self.use_color = use_color
        self.colors = self.DEFAULT_COLORS.copy()
        self.log_to_console = log_to_console
        self.table_view = table_view
        self.table_title = table_title if table_view else None
        self._header_printed = False
        self._footer_printed = False
        self._auto_column_widths = None
        self._row_count = 0

        if custom_colors:
            for level, color_name in custom_colors.items():
                if color_name.lower() in COLOR_MAP:
                    self.colors[level.upper()] = COLOR_MAP[color_name.lower()]

        if self.log_to_file:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
        # Register this instance for cleanup
        if self.table_view:
            _active_loggers.add(self)

    def _get_context(self):
        """Get file name and line number where the log was called."""
        frame = inspect.currentframe().f_back.f_back
        filename = frame.f_code.co_filename.split("/")[-1]
        line_number = frame.f_lineno
        return filename, line_number
    
    def _get_timestamp(self):
        """Return formatted timestamp."""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _apply_color(self, level, message):
        """Apply ANSI color to console output."""
        if not self.use_color:
            return message
        return f"{self.colors.get(level.upper(), COLOR_MAP['reset'])}{message}{COLOR_MAP['reset']}"
    
    def _build_message(self, level, message):
        """Build the log string with timestamp, level, context, and message."""
        filename, line_number = self._get_context()
        parts = []

        if self.with_time:
            parts.append(f"[{self._get_timestamp()}]")

        parts.append(f"[{level.upper()}]")
        parts.append(f"{filename}:{line_number}")
        parts.append(f"- {message}")

        log_str = " ".join(parts)
        return self._apply_color(level, log_str)
    
    def _get_terminal_width(self):
        """Get terminal width with fallback."""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 120  # Fallback width
    
    def _strip_ansi_codes(self, text):
        """Remove ANSI color codes from text for accurate length calculation."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def _calculate_optimal_widths(self):
        """Calculate optimal column widths based on terminal size."""
        if self._auto_column_widths:
            return self._auto_column_widths
            
        terminal_width = self._get_terminal_width()
        border_width = 13 if self.with_time else 10  # ┃ symbols and spaces
        available_width = terminal_width - border_width
        
        # Minimum required widths
        min_widths = {
            "time": 19 if self.with_time else 0,  # "YYYY-MM-DD HH:MM:SS"
            "level": 8,     # "WARNING"  
            "file_line": 15, # "filename.py:123"
            "message": 20   # Minimum message width
        }
        
        # Calculate optimal distribution
        if available_width < sum(min_widths.values()):
            # Terminal too narrow, use minimums
            self._auto_column_widths = min_widths
        else:
            # Distribute extra space intelligently
            extra_space = available_width - sum(min_widths.values())
            
            # Priority: 70% to message, 20% to file_line, 10% to time
            self._auto_column_widths = {
                "time": min_widths["time"] + int(extra_space * 0.10) if self.with_time else 0,
                "level": min_widths["level"],  # Keep level column fixed
                "file_line": min_widths["file_line"] + int(extra_space * 0.20),
                "message": min_widths["message"] + int(extra_space * 0.70)
            }
        
        return self._auto_column_widths
    
    def _wrap_text(self, text, width):
        """Wrap text to specified width, returning list of lines."""
        if len(text) <= width:
            return [text]
        
        # Use textwrap to handle word boundaries properly
        wrapped_lines = textwrap.wrap(text, width=width, break_long_words=True, 
                                    break_on_hyphens=True, expand_tabs=False)
        return wrapped_lines if wrapped_lines else [text]
    
    def _print_table_header(self):
        """Print table header with calculated column widths."""
        widths = self._calculate_optimal_widths()
        
        # Calculate total width
        border_chars = 13 if self.with_time else 10
        total_width = sum(widths[k] for k in widths if k != 'time' or self.with_time) + border_chars
        
        # Title
        if self.table_title:
            print(self.table_title.center(total_width))
        
        # Top border
        if self.with_time:
            print(f"┏{'━'*widths['time']}┳{'━'*widths['level']}┳{'━'*widths['file_line']}┳{'━'*widths['message']}┓")
        else:
            print(f"┏{'━'*widths['level']}┳{'━'*widths['file_line']}┳{'━'*widths['message']}┓")
        
        # Header row
        if self.with_time:
            print(f"┃{'Time':^{widths['time']}}┃{'Level':^{widths['level']}}┃"
                  f"{'File:Line':^{widths['file_line']}}┃{'Message':^{widths['message']}}┃")
            # Header separator
            print(f"┡{'━'*widths['time']}╇{'━'*widths['level']}╇{'━'*widths['file_line']}╇{'━'*widths['message']}┩")
        else:
            print(f"┃{'Level':^{widths['level']}}┃"
                  f"{'File:Line':^{widths['file_line']}}┃{'Message':^{widths['message']}}┃")
            # Header separator
            print(f"┡{'━'*widths['level']}╇{'━'*widths['file_line']}╇{'━'*widths['message']}┩")
    
    def _print_table_row(self, level, message):
        """Print one log entry in table format with automatic content wrapping."""
        timestamp = self._get_timestamp() if self.with_time else ""
        filename, line_number = self._get_context()
        file_line = f"{filename}:{line_number}"
        level_upper = level.upper()
        
        widths = self._calculate_optimal_widths()
        
        # Print header if not printed yet
        if not self._header_printed:
            self._print_table_header()
            self._header_printed = True
        
        # Wrap content for each column
        timestamp_lines = self._wrap_text(timestamp, widths["time"]) if timestamp else [""]
        level_lines = self._wrap_text(level_upper, widths["level"])
        file_line_lines = self._wrap_text(file_line, widths["file_line"])
        message_lines = self._wrap_text(message, widths["message"])
        
        # Find the maximum number of lines needed
        max_lines = max(
            len(timestamp_lines) if timestamp else 1,
            len(level_lines),
            len(file_line_lines), 
            len(message_lines)
        )
        
        # Pad shorter columns with empty strings
        while len(timestamp_lines) < max_lines:
            timestamp_lines.append("")
        while len(level_lines) < max_lines:
            level_lines.append("")
        while len(file_line_lines) < max_lines:
            file_line_lines.append("")
        while len(message_lines) < max_lines:
            message_lines.append("")
        
        # Print each line of the row
        for i in range(max_lines):
            timestamp_content = timestamp_lines[i] if self.with_time else ""
            level_content = level_lines[i]
            file_line_content = file_line_lines[i]
            message_content = message_lines[i]
            
            # Apply color to level content (only if it has content)
            if level_content and i == 0:  # Only color the first line of level
                colored_level = self._apply_color(level_upper, level_content)
                level_padding = widths["level"] + (len(colored_level) - len(self._strip_ansi_codes(colored_level)))
            else:
                colored_level = level_content
                level_padding = widths["level"]
            
            # Print the row
            if self.with_time:
                print(f"┃{timestamp_content:<{widths['time']}}┃{colored_level:<{level_padding}}┃"
                      f"{file_line_content:<{widths['file_line']}}┃{message_content:<{widths['message']}}┃")
            else:
                print(f"┃{colored_level:<{level_padding}}┃"
                      f"{file_line_content:<{widths['file_line']}}┃{message_content:<{widths['message']}}┃")
        
        self._row_count += 1
    
    def _print_table_footer(self):
        """Print table bottom border."""
        if self.table_view and self._header_printed and not self._footer_printed:
            widths = self._calculate_optimal_widths()
            if self.with_time:
                print(f"└{'─'*widths['time']}┴{'─'*widths['level']}┴{'─'*widths['file_line']}┴{'─'*widths['message']}┘")
            else:
                print(f"└{'─'*widths['level']}┴{'─'*widths['file_line']}┴{'─'*widths['message']}┘")
            self._footer_printed = True
    
    def close_table(self):
        """Manually close the table by printing the footer."""
        self._print_table_footer()
    
    def log(self, level, message):
        """Log message to console and optionally to file."""
        log_message = self._build_message(level, message)

        if self.log_to_console:
            if self.table_view:
                self._print_table_row(level, message)
            else:
                print(log_message)

        if self.log_to_file:
            with open(self.file_path, "a", encoding="utf-8") as f:
                clean_message = log_message
                for code in COLOR_MAP.values():
                    clean_message = clean_message.replace(code, "")
                f.write(clean_message + "\n")

    def info(self, message): self.log("INFO", message)
    def warning(self, message): self.log("WARNING", message)
    def error(self, message): self.log("ERROR", message)
    def debug(self, message): self.log("DEBUG", message)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - prints footer."""
        self.close_table()
        return False
    
    def __del__(self):
        """Destructor - attempt to close table when object is garbage collected."""
        try:
            self.close_table()
        except:
            pass  # Ignore errors during cleanup

# Try to register cleanup at module level
try:
    import atexit
    atexit.register(_cleanup_all_tables)
except:
    pass  # If atexit fails, we still have other mechanisms