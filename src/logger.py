import logging


LOGGER = logging.getLogger("CSFE")
LOGGER.setLevel(logging.DEBUG)  # Set the minimum level for capturing logs

# Console handler for logging to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Console only shows INFO and above

# Set format for log messages
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Add handlers to the LOGGER
LOGGER.addHandler(console_handler)
