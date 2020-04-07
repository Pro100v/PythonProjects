import logging
import time
import threading

from selenium import webdriver

import settings
from bets_utils import to_hash, get_base_url


class BaseBetParser(threading.Thread):
    """
    парсер страничек с лайвом
    """

    def __init__(self, web_driver: webdriver, url: str):
        super(BaseBetParser, self).__init__()
        logging.debug(
            f"Создается экземпляр {self.__class__.__name__} "
            f"с параметрами webdriver:{web_driver.name} url:{url}")
        # assert webdriver and url
        self.driver: webdriver = web_driver
        self.url = url.strip() if url else ''
        self.base_url = get_base_url(self.url)
        self.tab_name = to_hash(self.url)
        self.errors = {}
        self.idling = 0
        self.content = ''
        self.content_hash = None
        self.is_content_changed = False
        self.counter = 0
        pass

    def process(self):
        raise NotImplementedError

    def prepare(self):
        pass

    def check_changes(self):
        logging.debug(f"Проверяем состояние изменеия параметра ставок")
        self.idling += 1

    def load_new_tab(self):
        """
        метод с помощью javascript создает в браузере новую вкладку
        и загружает в него url
        """
        js = f"window.open('{self.url}', '{self.tab_name}');"
        logging.debug(
            f"Выполняем скрипт по созданию новой вкладки:'{self.tab_name}'"
        )
        self.driver.execute_script(js)

    def stop(self):
        """
        Метод для остановки работы класса
        :return:
        """
        self.idling = settings.MAX_IDLE

    def close(self):
        self.driver.switch_to.window(self.tab_name)
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def run(self) -> None:
        self.prepare()
        while self.idling < settings.MAX_IDLE:
            self.process()
            self.check_changes()
            self.counter += 1
            time.sleep(settings.BET_SLEEP)
        self.close()

    @classmethod
    def execute(cls, wb: webdriver, url: str):
        instance = cls(wb, url)
        instance.start()
        instance.join()
        # instance.prepare()
        # while instance.idling < settings.MAX_IDLE:
        #     instance.process()
        #     instance.check_changes()
        #     instance.counter += 1
        #     time.sleep(settings.BET_SLEEP)
        # instance.close()
