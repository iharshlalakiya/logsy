import inspect
import datetime
import os
import re
import shutil
import textwrap

from .utils import COLOR_MAP

class Logsy:
    
    DEFAULT_COLORS = {
        "INFO": COLOR_MAP["blue"],
        "WARNING": COLOR_MAP["yellow"],
        "ERROR": COLOR_MAP["red"],
        "DEBUG": COLOR_MAP["cyan"],
    }

    def __init__(
        self, 
        with_time=True, 
        log_to_file=True, 
        file_path="logs/app.log", 
        use_color=True, 
        custom_colors=None, 
        log_to_console=True, 
        table_view=False, 
        table_title=None
    ):

        """
        Args:
            with_time (bool): Include timestamp in logs. Default: True
            log_to_file (bool): Save logs to file. Default: True
            file_path (str): Log file path. Default: "logs/app.log
            use_color (bool): Print logs with colors. Default: True
            custom_colors (dict): User-defined color codes for log levels.
                                  Example: {"INFO": "blue", "CUSTOM": "green"}
            log_to_console (bool): Output logs to console. Default: True
            table_view (bool): Display logs in table format. Default: False
            table_title (str): Title for table view. Default: None
        """
        self.with_time = with_time
        self.log_to_file = log_to_file
        self.file_path = file_path
        self.use_color = use_color
        self.colors = self.DEFAULT_COLORS.copy()
        self.log_to_console = log_to_console
        self.table_view = table_view
        self.table_title = table_title if table_view else None
        self.header_printed = False

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

    def get_context(self):

        """
        Get file name and line number where the log was called.
        
        Returns:
            tuple: (filename, line_number)
        """

        frame = inspect.currentframe().f_back.f_back
        filename = frame.f_code.co_filename.split("/")[-1]
        line_number = frame.f_lineno
        return filename, line_number
    
    def get_timestamp(self):

        """
        Return formatted timestamp.
        
        Returns:
            str: Current timestamp in 'YYYY-MM-DD HH:MM:SS' format
        """

        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def apply_color(self, level, message):

        """
        Apply ANSI color to console output.
        
        Args:
            level (str): Log level
            message (str): Message to colorize
            
        Returns:
            str: Colorized message or plain message if colors disabled
        """

        if not self.use_color:
            return message
        return f"{self.colors.get(level.upper(), COLOR_MAP['reset'])}{message}{COLOR_MAP['reset']}"
    
    def build_message(self, level, message):

        """
        Build the log string with timestamp, level, context, and message.
        
        Args:
            level (str): Log level
            message (str): Log message
            
        Returns:
            str: Formatted and colored log message
        """

        filename, line_number = self.get_context()
        parts = []

        if self.with_time:
            parts.append(f"[{self.get_timestamp()}]")

        parts.append(f"[{level.upper()}]")
        parts.append(f"{filename}:{line_number}")
        parts.append(f"- {message}")

        log_str = " ".join(parts)
        return self.apply_color(level, log_str)
    
    def get_terminal_width(self):

        """
        Get terminal width with fallback.
        
        Returns:
            int: Terminal width in columns (default: 120)
        """

        try:
            return shutil.get_terminal_size().columns
        except:
            return 120  
    
    def strip_ansi_codes(self, text):

        """
        Remove ANSI color codes from text for accurate length calculation.
        
        Args:
            text (str): Text containing ANSI codes
            
        Returns:
            str: Plain text without ANSI codes
        """

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def calculate_optimal_widths(self):

        """
        Calculate optimal column widths based on terminal size.
        
        Returns:
            dict: Column widths for time, level, file_line, and message
        """

        if self._auto_column_widths:
            return self._auto_column_widths
            
        terminal_width = self.get_terminal_width()
        border_width = 13 if self.with_time else 10  
        available_width = terminal_width - border_width
        
        
        min_widths = {
            "time": 19 if self.with_time else 0,  
            "level": 8,     
            "file_line": 15, 
            "message": 20  
        }
        
        if available_width < sum(min_widths.values()):
            self._auto_column_widths = min_widths
        else:
            extra_space = available_width - sum(min_widths.values())
            
            self._auto_column_widths = {
                "time": min_widths["time"] + int(extra_space * 0.10) if self.with_time else 0,
                "level": min_widths["level"],  # Keep level column fixed
                "file_line": min_widths["file_line"] + int(extra_space * 0.20),
                "message": min_widths["message"] + int(extra_space * 0.70)
            }
        
        return self._auto_column_widths
    
    def wrap_text(self, text, width):

        """
        Wrap text to specified width, returning list of lines.
        
        Args:
            text (str): Text to wrap
            width (int): Maximum width per line
            
        Returns:
            list: List of wrapped text lines
        """

        if len(text) <= width:
            return [text]

        wrapped_lines = textwrap.wrap(text, width=width, break_long_words=True, 
                                    break_on_hyphens=True, expand_tabs=False)
        return wrapped_lines if wrapped_lines else [text]
    
    def print_table_header(self):

        """
        Print table header with calculated column widths.
        """

        widths = self.calculate_optimal_widths()

        border_chars = 13 if self.with_time else 10
        total_width = sum(widths[k] for k in widths if k != 'time' or self.with_time) + border_chars
        
        if self.table_title:
            print(self.table_title.center(total_width))
        
        if self.with_time:
            print(f"┏{'━'*widths['time']}┳{'━'*widths['level']}┳{'━'*widths['file_line']}┳{'━'*widths['message']}┓")
        else:
            print(f"┏{'━'*widths['level']}┳{'━'*widths['file_line']}┳{'━'*widths['message']}┓")
        
        if self.with_time:
            print(f"┃{'Time':^{widths['time']}}┃{'Level':^{widths['level']}}┃"
                  f"{'File:Line':^{widths['file_line']}}┃{'Message':^{widths['message']}}┃")

            print(f"┡{'━'*widths['time']}╇{'━'*widths['level']}╇{'━'*widths['file_line']}╇{'━'*widths['message']}┩")
        else:
            print(f"┃{'Level':^{widths['level']}}┃"
                  f"{'File:Line':^{widths['file_line']}}┃{'Message':^{widths['message']}}┃")

            print(f"┡{'━'*widths['level']}╇{'━'*widths['file_line']}╇{'━'*widths['message']}┩")
    
    def print_table_row(self, level, message):

        """
        Print one log entry in table format with automatic content wrapping.
        
        Args:
            level (str): Log level
            message (str): Log message
        """

        timestamp = self.get_timestamp() if self.with_time else ""
        filename, line_number = self.get_context()
        file_line = f"{filename}:{line_number}"
        level_upper = level.upper()
        
        widths = self.calculate_optimal_widths()
        
        if not self.header_printed:
            self.print_table_header()
            self.header_printed = True
        
        timestamp_lines = self.wrap_text(timestamp, widths["time"]) if timestamp else [""]
        level_lines = self.wrap_text(level_upper, widths["level"])
        file_line_lines = self.wrap_text(file_line, widths["file_line"])
        message_lines = self.wrap_text(message, widths["message"])
        
        max_lines = max(
            len(timestamp_lines) if timestamp else 1,
            len(level_lines),
            len(file_line_lines), 
            len(message_lines)
        )
        
        while len(timestamp_lines) < max_lines:
            timestamp_lines.append("")
        while len(level_lines) < max_lines:
            level_lines.append("")
        while len(file_line_lines) < max_lines:
            file_line_lines.append("")
        while len(message_lines) < max_lines:
            message_lines.append("")
        
        for i in range(max_lines):
            timestamp_content = timestamp_lines[i] if self.with_time else ""
            level_content = level_lines[i]
            file_line_content = file_line_lines[i]
            message_content = message_lines[i]
            
            if level_content and i == 0: 
                colored_level = self.apply_color(level_upper, level_content)
                level_padding = widths["level"] + (len(colored_level) - len(self.strip_ansi_codes(colored_level)))
            else:
                colored_level = level_content
                level_padding = widths["level"]
            
            if self.with_time:
                print(f"┃{timestamp_content:<{widths['time']}}┃{colored_level:<{level_padding}}┃"
                      f"{file_line_content:<{widths['file_line']}}┃{message_content:<{widths['message']}}┃")
            else:
                print(f"┃{colored_level:<{level_padding}}┃"
                      f"{file_line_content:<{widths['file_line']}}┃{message_content:<{widths['message']}}┃")
        
        self._row_count += 1
    
    def print_table_footer(self):

        """
        Print table bottom border.
        """

        widths = self.calculate_optimal_widths()
        if self.with_time:
            print(f"└{'─'*widths['time']}┴{'─'*widths['level']}┴{'─'*widths['file_line']}┴{'─'*widths['message']}┘")
        else:
            print(f"└{'─'*widths['level']}┴{'─'*widths['file_line']}┴{'─'*widths['message']}┘")
    
    def log(self, level, message):

        """
        Log message to console and optionally to file.
        
        Args:
            level (str): Log level (INFO, WARNING, ERROR, DEBUG, or custom)
            message (str): Message to log
        """
        
        log_message = self.build_message(level, message)

        if self.log_to_console:
            if self.table_view:
                self.print_table_row(level, message)
            else:
                print(log_message)

        if self.log_to_file:
            with open(self.file_path, "a", encoding="utf-8") as f:
                clean_message = log_message
                for code in COLOR_MAP.values():
                    clean_message = clean_message.replace(code, "")
                f.write(clean_message + "\n")

    def info(self, message): 

        """
        Log an INFO level message.
        
        Args:
            message (str): Message to log
        """

        self.log("INFO", message)

    def warning(self, message): 

        """
        Log a WARNING level message.
        
        Args:
            message (str): Message to log
        """

        self.log("WARNING", message)

    def error(self, message): 

        """
        Log an ERROR level message.
        
        Args:
            message (str): Message to log
        """

        self.log("ERROR", message)

    def debug(self, message): 

        """
        Log a DEBUG level message.
        
        Args:
            message (str): Message to log
        """

        self.log("DEBUG", message)