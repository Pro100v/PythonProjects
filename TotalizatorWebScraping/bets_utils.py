import logging
import os
import platform

import settings

CHROME = "chrome".upper()
FIREFOX = "firefox".upper()


def set_logging(logging_level=logging.INFO):
    format = "%(asctime)s (%(threadName)-9s): %(message)s"
    # log_lvl = logging.INFO  # logging.INFO / logging.DEBUG / logging.WARNING
    try:
        log_lvl = logging._checkLevel(logging_level)
    except Exception:
        log_lvl = logging.INFO

    logging.basicConfig(format=format, level=log_lvl,
                        datefmt="%d/%m/%Y %H:%M:%S")


def get_webdriver_path(browser=CHROME) -> str:
    system_version = platform.system().upper()
    driver_path = ""
    if browser == CHROME:
        driver_path = settings.PATH_CHROMEDRIVER.split('/')
    if browser == FIREFOX:
        raise NotImplementedError()
    assert driver_path

    # parent = app_path()
    if system_version.startswith("LINUX"):
        return app_path(*driver_path, "chromedriver")
    if system_version.startswith("WINDOWS"):
        return app_path(*driver_path, "chromedriver.exe")
    if system_version.startswith("DARWIN"):
        return app_path(*driver_path, "chromedriver-mac")


def app_path(*args):
    path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(path, *args)


def clr_txt(s: str) -> str:
    return s.replace('\\n', '').replace('\\t', '').replace("', '", '').strip()
