import logging
import time


from typing import Optional, List, NoReturn
from threading import Thread, Lock

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import settings
from bets_utils import to_hash, get_base_url


class BaseBetParser(Thread):
    """
    базовый класс парсера сайта
    """

    def __init__(self, web_driver: webdriver, url: str,
                 driver_lock: Lock = None,
                 parent: Optional['BaseBetParser'] = None):
        super(BaseBetParser, self).__init__()
        logging.debug(
            f"Создается экземпляр {self.__class__.__name__} "
            f"с параметрами webdriver:{web_driver.name} url:{url}")
        # assert webdriver and url
        self.driver: webdriver = web_driver
        self.url = url.strip() if url else ''
        self.base_url = get_base_url(self.url)
        self.tab_name = to_hash(self.url)
        self.parent = parent
        self.driver_lock = Lock() if not driver_lock else driver_lock
        self.my_lock = Lock()
        self.children: List['BaseBetParser'] = []
        self.errors = {}
        self.idling = 0
        self.content = ''
        self.content_hash = None
        self.is_content_changed = False
        self.counter = 0
        pass

    def process(self) -> NoReturn:
        raise NotImplementedError

    def prepare(self) -> NoReturn:
        pass

    def check_changes(self) -> NoReturn:
        logging.debug(f"Проверяем состояние изменеия параметра ставок")
        pass

    def check_404(self) -> bool:
        return False

    @property
    def isErrorPage(self):
        res = self.check_404()
        if res:
            logging.critical(f"Ошибка 404! (url:{self.url})")
        return res

    def load_new_tab(self):
        """
        метод с помощью javascript создает в браузере новую вкладку
        и загружает в него url
        """
        js = f"window.open('{self.url}', '{self.tab_name}');"
        logging.debug(
            f"Выполняем скрипт по созданию новой вкладки:'{self.tab_name}'"
        )
        try:
            self.driver_lock.acquire()
            self.driver.execute_script(js)
        finally:
            self.driver_lock.release()
        logging.debug(f"Вкладка успешно создана.")

    def waiting_page_load(self, locator, timeout=None, attempts=None):
        """
        метод ожидает закгрузки контента
        locator - элемент по которому проверяют загрузку
        переменые timeout - время ожидания, attempts - кол-во попыток
        если все попытки завершились не удачей, вызывается метод для
        остановки обработчика класса
        Пример:
            waiting_page_load(locator=(By.ID, "content"))
        """
        timeout = settings.DOWNLOAD_TIMEOUT if not timeout else timeout
        attempts = settings.DOWNLOAD_ATTEMPTS if not attempts else attempts
        i = 0
        logging.debug(f"Ждем {timeout}сек. для загрузки контента "
                      f"(всего попыток {attempts})")
        try:
            self.driver_lock.acquire()
            self.driver.switch_to.window(self.tab_name)
            for i in range(1, attempts + 1):
                try:
                    logging.debug(f"Попытка {i}")
                    WebDriverWait(self.driver, timeout).until(
                        EC.visibility_of_element_located(locator))
                    logging.debug("данные успешно загруженны")
                    break
                except TimeoutException:
                    logging.warning(f"Время ожидания загрузки истекло.",
                                    exc_info=True)
                    self.driver.switch_to.window(self.tab_name)
        finally:
            self.driver_lock.release()

        if i == attempts:
            logging.critical(f"Использован лимит попыток на загрузку контента")
            self.stop()

    def stop(self):
        """
        Метод для остановки работы класса
        :return:
        """
        self.idling = settings.MAX_IDLE

    def close(self):
        # закрываем всех потомков
        for child in self.children:
            child.close()
        # удаляем себя из перечня предка
        if self.parent and self in self.parent.children:
            try:
                self.parent.my_lock.acquire()
                self.parent.children.remove(self)
            finally:
                self.parent.my_lock.release()
        # закрываем вкладку
        try:
            self.driver_lock.acquire()
            self.driver.switch_to.window(self.tab_name)
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        finally:
            self.driver_lock.release()
        logging.info(f"Поток {self.getName()} закрывается. "
                     f"Кол-во обработок:{self.counter}")

    def run(self) -> None:
        self.prepare()
        if not self.isErrorPage:
            while self.idling < settings.MAX_IDLE or len(self.children) > 0:
                self.process()
                self.check_changes()
                self.idling += 1
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
