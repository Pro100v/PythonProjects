import logging
import re
import time
from abc import ABC
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
# from selenium import webdriver
from selenium.webdriver.common.by import By


import settings
from bets_utils import to_hash
from core.parser import BaseBetParser
from sites.ligastavok.data import LigastavokEventData


class LigastavokBase(BaseBetParser, ABC):
    """
    базовый класс для сайта https://www.ligastavok.ru
    """
    base_url = 'https://www.ligastavok.ru'

    # def __init__(self, web_driver: webdriver, url: str, mutex=None):
    #     super(LigastavokBase, self).__init__(
    #         web_driver=web_driver,
    #         url=url,
    #     )
    #     self.driver_lock = threading.Lock() if not mutex else mutex

    def prepare(self):
        logging.debug(f"Загружаем страницу по url:{self.url}")
        self.url = urljoin(self.base_url, self.url).strip()
        self.load_new_tab()
        self.waiting_page_load(locator=(By.ID, "content"))

    # def waiting_page_load(self):
    #     """
    #     метод ожидает закгрузки контента
    #     переменые timeout - время ожидания, attempts - кол-во попыток
    #     если все попытки завершились не удачей, вызывается метод для
    #     остановки обработчика класса
    #     """
    #     timeout = settings.DOWNLOAD_TIMEOUT
    #     attempts = settings.DOWNLOAD_ATTEMPTS
    #     i = 0
    #     try:
    #         self.driver_lock.acquire()
    #         self.driver.switch_to.window(self.tab_name)
    #         logging.debug(
    #             f"Вкладка создана. "
    #             f"Ждем {timeout} сек. для загрузки контента."
    #         )
    #         for i in range(1, attempts + 1):
    #             try:
    #                 logging.debug(f"Попытка {i}")
    #                 WebDriverWait(self.driver, timeout).until(
    #                     EC.visibility_of_element_located())
    #                 logging.debug("данные успешно загруженны")
    #                 break
    #             except TimeoutException:
    #                 logging.warning(f"Время ожидания загрузки истекло.",
    #                                 exc_info=True)
    #                 self.driver.switch_to.window(self.tab_name)
    #     finally:
    #         self.driver_lock.release()
    #
    #     if i == attempts:
    #         logging.critical(f"Достигнут лимит попыток на загрузку контента")
    #         self.stop()

    def check_404(self, ) -> bool:
        """
        проверка не является ли открытая страница ошибкой
        :return:
        """
        bs = BeautifulSoup(self.get_html_content(), "html.parser")
        element = bs.find_all('div', class_=re.compile('not-found'))
        return len(element) > 0

    def get_content(self):
        wd = self.driver
        try:
            self.driver_lock.acquire()
            wd.switch_to.window(self.tab_name)
            elem = wd.find_element_by_id("content")
        finally:
            self.driver_lock.release()
        return elem

    def get_html_content(self):
        html = self.get_content().get_attribute('innerHTML')
        return html

    def update_content(self):
        """
        метод загружает из driver в переменную класс content содержимое для
        последующей разбора данных
        :return:
        """
        logging.debug(f"Обновляем контент класса")
        html = self.get_html_content()
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

    def __init__(self, web_driver, url, driver_lock=None, parent=None):
        super(LigastavokLive, self).__init__(
            web_driver=web_driver,
            url=url,
            driver_lock=driver_lock,
            parent=parent,
        )
        self.bet_matches_url = set()
        self.bet_matches: List[LigastavokEventData] = []
        self.processed_data: List[LigastavokEventData] = []

    def process(self):
        logging.debug(f"Старт обработки контента страницы")
        self.update_content()
        if not self.is_content_changed:
            self.processed_data = []
            return
        logging.debug(f"Данные обновились. Загружаем контент в BeautifulSoup")
        # b_s = BeautifulSoup(self.get_content(), "lxml")
        all_events = self.content.find_all('div',
                                           class_=re.compile('bui-event-row'),
                                           itemtype="http://schema.org/Event")
        self.processed_data = [LigastavokEventData(event)
                               for event in all_events]

    def check_changes(self):
        new_events = [event for event in self.processed_data
                      if event.href not in self.bet_matches_url]
        logging.debug(f"Обнаружено новых событий: {len(new_events)}")
        for event in new_events:
            self.bet_matches_url.add(event.href)
            self.bet_matches.append(event)
            print(event)
            url = urljoin(self.base_url, event.href)
            event_parser = LigastavokEvent(
                web_driver=self.driver,
                url=url,
                driver_lock=self.driver_lock,
                parent=self,
            )
            try:
                self.my_lock.acquire()
                self.children.append(event_parser)
            finally:
                self.my_lock.release()
            event_parser.start()
            time.sleep(settings.BET_SLEEP)


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
