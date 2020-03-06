from selenium import webdriver
from selenium.common.exceptions import WebDriverException

import logging
import os.path
import time
import datetime

from dataclasses import dataclass, field
import typing


@dataclass
class BetEvent:
    type_event: str = "Unknown"
    date_event: typing.Union[datetime.date, str] = "Unknown"
    tournament: str = "Unknown"
    home_team: str = "Unknown"
    guest_team: str = "Unknown"
    scoring: str = "Unknown"




def set_logging(logging_level=logging.INFO):
    format = "%(asctime)s (%(threadName)-9s): %(message)s"
    # log_lvl = logging.INFO  # logging.INFO /  logging.DEBUG  / logging.WARNING
    try:
        log_lvl = logging._checkLevel(logging_level)
    except:
        log_lvl = logging.INFO

    logging.basicConfig(format=format, level=log_lvl,
                        datefmt="%d/%m/%Y %H:%M:%S")
    # logging.getLogger().setLevel(logging.DEBUG)
    # logging.getLogger().setLevel(logging.WARNING)


def main_file_exists_sample():
    msg = 'exists' if os.path.exists('../ligastavokscraper.py') else 'not exists'
    print(msg)

    try:
        drv = webdriver.Chrome(executable_path='')
    except WebDriverException as err:
        print("err", err)
        drv = webdriver.Chrome()


def main_multi_tab():
    logging.debug("Создаем экземпляр web_driver = webdriver.Chrome()")
    web_driver = webdriver.Chrome()
    url_1 = "https://www.ligastavok.ru/bets/live"
    logging.info(f"Открываем url:{url_1} на browser:{web_driver.name}")
    web_driver.get(url_1)

    timer = 3
    logging.debug(f"перед сном на {timer}")
    time.sleep(timer)
    logging.debug(f"проснулись")
    url_2 = "https://www.ligastavok.ru/bets/live/soccer/egipet-id-276/2-i-divizion-id-150/petrodzhet-el-zarka-id-13270115"
    new_tab = "tab2"
    # js = f"window.open('about:blank', '{new_tab}');"
    js = f"window.open('{url_2}', '{new_tab}');"
    logging.debug(f"выполняем скрипт по созданию новой вкладки:'{new_tab}'")
    web_driver.execute_script(js)
    # web_driver.switch_to.window(new_tab)
    # logging.info(f"Открываем url:{url_2} на tab:{new_tab}  browser:{web_driver.name}")
    # web_driver.get(url_2)

    time.sleep(180)


if __name__ == "__main__":
    set_logging(logging.DEBUG)
    main_multi_tab()
