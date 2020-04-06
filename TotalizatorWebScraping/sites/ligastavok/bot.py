import hashlib
import logging
import re
from abc import ABC
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import settings
from core.parser import BaseBetParser
from sites.ligastavok.data import LigastavokEventData


class LigastavokBase(BaseBetParser, ABC):
    """
    базовый класс для сайта https://www.ligastavok.ru
    """
    home_link = 'https://www.ligastavok.ru'

    def prepare(self):
        logging.debug(f"Переходим по url:{self.url}")
        self.tab_name = hashlib.md5(str(self.url).encode()).hexdigest()

        js = f"window.open('{self.url}', '{self.tab_name}');"
        logging.debug(
            f"выполняем скрипт по созданию новой вкладки:'{self.tab_name}'"
        )
        self.driver.execute_script(js)
        # self.driver.get(self.url)

        timeout = 30
        self.driver.switch_to.window(self.tab_name)
        logging.debug(f"ждем в течении {timeout} сек. для загрузки контента")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.ID, "content")))
        except TimeoutException:
            logging.debug(
                f"время ожидания загрузки контента превысело {timeout} сек. ")
            # self.errors.
            # todo: добавить сообщение об ошибке.
            # todo: Понять почему ошибки словарем сделаны
            self.idling = settings.MAX_IDLE
            return
        logging.debug("данные успешно загруженны")


class LigastavokLive(LigastavokBase):
    processed_data: List[LigastavokEventData]
    bet_matches: List[LigastavokEventData]

    def __init__(self, web_driver: webdriver, url: str):
        super(LigastavokLive, self).__init__(web_driver=web_driver, url=url)
        self.bet_matches = []
        self.bet_matches_url = set()
        self.processed_data = []

    def process(self):
        logging.debug(f"Загружаем контент в BeautifulSoup")
        self.driver.switch_to.window(self.tab_name)
        # b_s = BeautifulSoup(self.get_content(), "lxml")
        b_s = BeautifulSoup(self.get_content(), "html.parser")
        hash_content = hashlib.md5(str(b_s).encode()).hexdigest()
        logging.info(f"Хеш контента:{hash_content}")
        if self.hash_content == hash_content:
            self.processed_data = []
            return
        all_events = b_s.find_all('div', class_=re.compile('bui-event-row'),
                                  itemtype="http://schema.org/Event")
        self.processed_data = [LigastavokEventData(event) for event in
                               all_events]
        self.hash_content = hash_content

    def check_changes(self):
        super(LigastavokLive, self).check_changes()
        new_events = [event for event in self.processed_data if
                      event.href not in self.bet_matches_url]
        logging.debug(f"Обнаружено новых событий: {len(new_events)}")
        for event in new_events:
            self.bet_matches_url.add(event.href)
            self.bet_matches.append(event)
            print(event)

    def prepare(self):
        super(LigastavokLive, self).prepare()

    def get_content(self) -> str:
        return self.driver.find_element_by_id("content").get_attribute(
            'innerHTML')
