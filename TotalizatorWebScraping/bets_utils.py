import logging

def set_logging(logging_level=logging.INFO):
    format = "%(asctime)s (%(threadName)-9s): %(message)s"
    # log_lvl = logging.INFO  # logging.INFO /  logging.DEBUG  / logging.WARNING
    try:
        log_lvl = logging._checkLevel(logging_level)
    except:
        log_lvl = logging.INFO

    logging.basicConfig(format=format, level=log_lvl,
                        datefmt="%d/%m/%Y %H:%M:%S")