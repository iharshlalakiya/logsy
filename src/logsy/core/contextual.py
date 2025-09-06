import inspect
import datetime
import os
from .utils import COLOR_MAP
class Logsy:
    DEFAULT_COLORS = {
        "INFO": COLOR_MAP["blue"],
        "WARNING": COLOR_MAP["yellow"],
        "ERROR": COLOR_MAP["red"],
        "DEBUG": COLOR_MAP["cyan"],
    }

    def __init__(self, with_time=True, log_to_file=True, file_path="logs/app.log",use_color=True, custom_colors=None, log_to_console=True):

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

        if custom_colors:
            for level, color_name in custom_colors.items():
                if color_name.lower() in COLOR_MAP:
                    self.colors[level.upper()] = COLOR_MAP[color_name.lower()]

        if self.log_to_file:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

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
    
    def log(self, level, message):

        """Log message to console and optionally to file."""
        
        log_message = self._build_message(level, message)

        if self.log_to_console:
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