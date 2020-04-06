import logging
import time

from selenium import webdriver

import settings


class BaseBetParser(object):
    """
    парсер страничек с лайвом
    """

    def __init__(self, web_driver: webdriver, url: str):
        logging.debug(
            f"Создается экземпляр {self.__class__.__name__} "
            f"с параметрами webdriver:{web_driver.name} url:{url}")
        # assert webdriver and url
        self.driver = web_driver
        self.url = url
        self.errors = {}
        self.idling = 0
        self.hash_content = None
        pass

    def process(self):
        raise NotImplementedError

    def prepare(self):
        pass

    def check_changes(self):
        logging.debug(f"Проверяем состояние изменеия параметра ставок")
        self.idling += 1

    @classmethod
    def execute(cls, wb: webdriver, url: str):
        instance = cls(wb, url)
        instance.prepare()
        while instance.idling < settings.MAX_IDLE:
            instance.process()
            instance.check_changes()
            time.sleep(settings.BET_SLEEP)
