import logging
import re
import threading
import time
from abc import ABC
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import settings
from bets_utils import to_hash
from core.parser import BaseBetParser
from sites.ligastavok.data import LigastavokEventData


class LigastavokBase(BaseBetParser, ABC):
    """
    базовый класс для сайта https://www.ligastavok.ru
    """
    base_url = 'https://www.ligastavok.ru'

    def __init__(self, web_driver: webdriver, url: str, mutex=None):
        super(LigastavokBase, self).__init__(
            web_driver=web_driver,
            url=url,
        )
        self.mutex = threading.Lock() if not mutex else mutex

    def prepare(self):
        self.url = urljoin(self.base_url, self.url.strip())
        logging.debug(f"Загружаем страницу по url:{self.url}")

        # js = f"window.open('{self.url}', '{self.tab_name}');"
        # logging.debug(
        #     f"Выполняем скрипт по созданию новой вкладки:'{self.tab_name}'"
        # )
        # self.driver.execute_script(js)
        # self.driver.get(self.url)
        self.load_new_tab()
        self.waiting_page_load()
        self.check_error_page()

    def waiting_page_load(self):
        """
        метод ожидает закгрузки контента
        переменые timeout - время ожидания, attempts - кол-во попыток
        если все попытки завершились не удачей, вызывается метод для
        остановки обработчика класса
        """
        timeout = settings.DOWNLOAD_TIMEOUT
        attempts = settings.DOWNLOAD_ATTEMPTS
        i = 0
        try:
            self.mutex.acquire()
            self.driver.switch_to.window(self.tab_name)
            logging.debug(
                f"Вкладка создана. "
                f"Ждем {timeout} сек. для загрузки контента."
            )
            for i in range(1, attempts + 1):
                try:
                    logging.debug(f"Попытка {i}")
                    WebDriverWait(self.driver, timeout).until(
                        EC.visibility_of_element_located((By.ID, "content")))
                    logging.debug("данные успешно загруженны")
                    break
                except TimeoutException:
                    logging.warning(f"Время ожидания загрузки истекло.",
                                    exc_info=True)
                    self.driver.switch_to.window(self.tab_name)
        finally:
            self.mutex.release()

        if i == attempts:
            logging.critical(f"Использован лимит попыток на загрузку контента")
            self.stop()

    def check_error_page(self, ):
        """
        проверка не является ли открытая страница ошибкой
        :return:
        """
        logging.debug(f"Проверка на ошибку 404 - страница не найдена")
        if not self.content or isinstance(self.content, (str,)):
            self.update_content()
        bs = self.content
        element = bs.find_all('div', class_=re.compile('not-found'))
        if len(element) > 0:
            logging.critical(f"Ошибка 404! (url:{self.url})")
            self.stop()
        else:
            logging.debug(f"Ошибка 404 не обнаружена")

    def update_content(self):
        """
        метод загружает из driver в переменную класс content содержимое для
        последующей разбора данных
        :return:
        """
        logging.debug(f"Обновляем контент класса")
        wd = self.driver
        try:
            self.mutex.acquire()
            wd.switch_to.window(self.tab_name)
            html = wd.find_element_by_id("content").get_attribute('innerHTML')
        finally:
            self.mutex.release()
        html_hash = to_hash(html)
        self.is_content_changed = self.content_hash != html_hash
        if self.is_content_changed:
            logging.debug(f"Состояние страницы изменилось")
            self.content = BeautifulSoup(html, "html.parser")
            self.content_hash = html_hash


class LigastavokLive(LigastavokBase):
    """
    класс разбора страницы с текущими событиями
    его задача собрать ссылки и запустить сыбытия для сбора всех ставок
    """
    processed_data: List[LigastavokEventData]
    bet_matches: List[LigastavokEventData]

    def __init__(self, web_driver: webdriver, url: str, mutex=None):
        super(LigastavokLive, self).__init__(
            web_driver=web_driver,
            url=url,
            mutex=mutex
        )
        self.bet_matches = []
        self.bet_matches_url = set()
        self.processed_data = []

    def process(self):
        logging.debug(f"Старт обработки контента страницы")
        self.processed_data = []
        self.update_content()
        if self.counter and not self.is_content_changed:
            return
        logging.debug(f"Загружаем контент в BeautifulSoup")
        # b_s = BeautifulSoup(self.get_content(), "lxml")
        # b_s = BeautifulSoup(self.content, "html.parser")
        b_s = self.content
        all_events = b_s.find_all('div', class_=re.compile('bui-event-row'),
                                  itemtype="http://schema.org/Event")
        self.processed_data = [LigastavokEventData(event) for event in
                               all_events]

    def check_changes(self):
        super(LigastavokLive, self).check_changes()
        new_events = [event for event in self.processed_data if
                      event.href not in self.bet_matches_url]
        logging.debug(f"Обнаружено новых событий: {len(new_events)}")
        for event in new_events:
            self.bet_matches_url.add(event.href)
            self.bet_matches.append(event)
            print(event)
            url = urljoin(self.base_url, event.href)
            LigastavokEvent(self.driver, url, self.mutex).start()
            time.sleep(settings.BET_SLEEP)

    # def get_content(self) -> str:
    #     return self.driver.find_element_by_id("content").get_attribute(
    #         'innerHTML')


class LigastavokEvent(LigastavokBase):
    """
    класс разбора страницы с единственным событием
    """

    def process(self):
        logging.debug(f"Старт обработки страницы")
        pass


def main():
    pass


if __name__ == '__main__':
    main()
