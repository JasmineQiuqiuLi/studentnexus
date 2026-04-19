import csv
from datetime import datetime


# add a new log entry to the log file with the current timestamp, URL, and error message
def log_error(file_path, url, error):
    file_exists = file_path.exists()

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "url", "error_type", "error_message"])
        writer.writerow([
            datetime.now().isoformat(), 
            url, 
            type(error).__name__,
            str(error)
        ])

