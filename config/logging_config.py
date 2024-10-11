import logging.config

def setup_logging():
    logging.config.fileConfig('config/logging_config.ini')