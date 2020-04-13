import logging
import re
# import time
from abc import ABC
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
# from selenium import webdriver
from selenium.webdriver.common.by import By


# import settings
from bets_utils import to_hash
from core.dispatcher import Dispatcher
from core.parser import BaseBetParser
from sites.ligastavok.data import LigastavokEventData


class LigastavokBase(BaseBetParser, ABC):
    """
    базовый класс для сайта https://www.ligastavok.ru
    """
    base_url = 'https://www.ligastavok.ru'

    def prepare(self):
        logging.debug(f"Загружаем страницу по url:{self.url}")
        self.url = urljoin(self.base_url, self.url).strip()
        self.load_new_tab()
        self.waiting_page_load(locator=(By.ID, "content"))

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
        with self.driver_lock:
            wd.switch_to.window(self.tab_name)
            elem = wd.find_element_by_id("content")
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


# noinspection PyAttributeOutsideInit
class LigastavokLive(LigastavokBase):
    """
    класс разбора страницы с текущими событиями
    его задача собрать ссылки и запустить сыбытия для сбора всех ставок
    """
    def __post_init__(self):
        self.bet_matches_url = set()
        self.bet_matches: List[LigastavokEventData] = []
        self.processed_data: List[LigastavokEventData] = []
        self.dispatcher: Dispatcher = None

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
            # with self.my_lock:
            #     self.children.append(event_parser)
            # event_parser.start()
            # time.sleep(settings.BET_SLEEP)
            self.dispatcher.put(event_parser)


class LigastavokEvent(LigastavokBase):
    """
    класс разбора страницы с единственным событием
    """

    def process(self):
        logging.debug(f"Старт обработки страницы")
        self.update_content()
        pass


def main():
    pass


if __name__ == '__main__':
    main()
