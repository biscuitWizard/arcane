import os
import logging

def setup_logging():
    logging_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=logging_level,
        format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s"
    )
