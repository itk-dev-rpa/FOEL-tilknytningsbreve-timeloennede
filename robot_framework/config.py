"""This module contains configuration constants used across the framework"""

# The number of times the robot retries on an error before terminating.
from datetime import date


MAX_RETRY_COUNT = 3

# Whether the robot should be marked as failed if MAX_RETRY_COUNT is reached.
FAIL_ROBOT_ON_TOO_MANY_ERRORS = True

# Error screenshot config
SMTP_SERVER = "smtp.adm.aarhuskommune.dk"
SMTP_PORT = 25
SCREENSHOT_SENDER = "robot@friend.dk"

# Constants
LOOK_BACK_DAYS = 30
WARNING_DAYS = 20
GLOBAL_CUTOFF_DATE = date(2026, 7, 15)  # TODO
WARNINGS_RECEIVER = "gbhm@aarhus.dk"  # TODO
WARNINGS_SENDER = "robot@friend.dk"  # TODO

# Constant/Credential names
ERROR_EMAIL = "Error Email"


# The name of the job queue
QUEUE_NAME_LETTERS = "Tilknytningsbreve Timelønnede"
QUEUE_NAME_WARNINGS = "Tilknytningsbreve Timelønnede Advarsler"

