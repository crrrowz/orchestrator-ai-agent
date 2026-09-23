import os
import logging

# Ensure quiet terminal execution
os.environ["OPENHANDS_SUPPRESS_BANNER"] = "1"
os.environ["LITELLM_LOG"] = "ERROR"

for _log_name in ["openhands", "litellm", "httpx", "httpcore", "urllib3"]:
    logging.getLogger(_log_name).setLevel(logging.ERROR)

__version__ = "0.1.0"
