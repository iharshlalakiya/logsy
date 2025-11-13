import os
import re
import sys
import tempfile

from logsy.logger import Logsy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

def test_console_logging(capsys):
    logger = Logsy(with_time=False, log_to_file=False, use_color=True, log_to_console=True)
    logger.info("Test info log")

    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert "Test info log" in captured.out
    assert "\033[" in captured.out  

def test_logging_with_time(capsys):
    logger = Logsy(with_time=True, log_to_file=False)
    logger.info("Test log with time")

    captured = capsys.readouterr()

    timestamp_pattern = r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]"
    
    assert re.search(timestamp_pattern, captured.out), "Timestamp missing or wrong format"
    assert "[INFO]" in captured.out
    assert "Test log with time" in captured.out

def test_file_logging():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.log")

        logger = Logsy(with_time=False, log_to_file=True, file_path=file_path, use_color=True, log_to_console=False)
        logger.error("Test error log")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "\033[" not in content
        assert "ERROR" in content
        assert "Test error log" in content

def test_custom_colors(capsys):
    custom_colors = {"INFO": "cyan", "ERROR": "magenta"}
    logger = Logsy(with_time=False, log_to_file=False, use_color=True, custom_colors=custom_colors)
    logger.info("Custom color info log")
    logger.error("Custom color error log")

    captured = capsys.readouterr()
    assert "\033[" in captured.out
    assert "Custom color info log" in captured.out
    assert "Custom color error log" in captured.out

def test_table_console_output(capsys):
    logger = Logsy(log_to_file=False, table_view=True, table_title="Test Table")
    logger.info("Table info log")
    logger.error("Table error log")

    captured = capsys.readouterr()
    # print(captured.out)

    assert "Test Table" in captured.out
    assert "Time" in captured.out
    assert "Level" in captured.out
    assert "File:Line" in captured.out
    assert "Message" in captured.out
    assert "INFO" in captured.out
    assert "Table info log" in captured.out
    assert "ERROR" in captured.out
    assert "Table error log" in captured.out

def test_table_responsive_width(capsys):
    logger = Logsy(log_to_file=False, table_view=True, table_title="Responsive Test")
    long_message = "This is a very long log message to test table responsiveness"
    logger.info(long_message)

    captured = capsys.readouterr()
    # print(captured.out)
    # assert long_message in captured.out
    assert "Message" in captured.out
    assert "Time" in captured.out
    assert "Level" in captured.out
    assert "File:Line" in captured.out