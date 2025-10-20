import logging

# Configure logging
logging.basicConfig(
    filename='search_features/logs/output.log',  # Log file path
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='w'  # Overwrites file each run, use 'a' to append
)

# Create a logger
logger = logging.getLogger(__name__)

# Optional: Add console output too
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

