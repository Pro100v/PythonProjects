import logging
import re
import time
from dataclasses import dataclass, field
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import settings
from bets_utils import clr_txt


class BetParser(object):
    """
        базовый класс для парсера ставок конкретного события

    """

    def __init__(self, webdriver: webdriver = None, url: str = None):
        """
        Constructor for BetsParser

        Args:

        """
        logging.debug(
            f"Создается экземпляр {self.__class__.__name__} "
            f"с параметрами webdriver:{webdriver.name} url:{url}")
        assert webdriver and url
        self.driver = webdriver
        self.url = url
        self.errors = {}
        self.idling = 0
        self.soup = None

        # создаем вкладку в которой будет загружаться веб-страница
        self.tab_name = "test"  # ToDo: придумать генератор названия вкладки
        js = f"window.open('{self.url}', '{self.tab_name}');"
        logging.debug(f"Создаем новую вкладку скриптом js: {js}")
        self.driver.execute_script(js)

        # TODO: в класс передавать родительский объект и в него записывать
        #  себя для возможности управления из родителя

    def process(self):
        raise NotImplementedError()

    def check_changes(self):
        logging.debug(f"Проверяем состояние изменеия параметра ставок")
        self.idling += 1

    def prepare(self):
        logging.debug(f"Переходим по utl:{self.url}")
        self.driver.switch_to.window(self.tab_name)
        self.driver.get(self.url)

        timeout = 30
        logging.debug(f"ждем в течении {timeout} сек. для загрузки контента")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.ID, "content")))
        except TimeoutException:
            logging.debug(
                f"время ожидания загрузки контента превысело {timeout} сек. ")
            self.idling = settings.MAX_IDLE
            return

        logging.debug(f"контент загружен. Загружаем контент в BeautifulSoup")
        self.soup = BeautifulSoup(self.driver.find_element_by_id("content"),
                                  "lxml")

    def __del__(self):
        if self.driver:
            logging.debug(f"Закрываем вкладку браузера tab:{self.tab_name}")
            self.driver.switch_to.window(self.tab_name)
            self.driver.close()

    @classmethod
    def execute(cls, webdriver: webdriver, url: str):
        instance = cls(webdriver, url)
        instance.prepare()
        while instance.idling < settings.MAX_IDLE:
            instance.process()
            instance.check_changes()
            time.sleep(settings.BET_SLEEP)


class LigastavokProbe(BetParser):
    """
    Парсер ставок Ligastavok конкретного события
    site https://www.ligastavok.ru
    """

    def process(self):
        self.driver.switch_to.window(self.tab_name)
        # print(self.html)
        # xpath = "//div[contains(@class,'bui-outcome')]"
        all_bets = self.soup.find_all('div', class_=re.compile('bui-outcome'))
        for bet in all_bets:
            parent = str(bet.parent.parent.parent.span.text)
            print(f"{parent} {bet.get('title')} : {bet.contents[-1]}")

        time.sleep(1)
        self.driver.switch_to.window(self.driver.window_handles[0])

    def prepare(self):
        with open(file="./pages/detail_bets_html.txt", mode='r') as f:
            self.html = f.readlines()
        logging.debug(f"контент загружен. Загружаем контент в BeautifulSoup")
        self.soup = BeautifulSoup(str(self.html), "lxml")


@dataclass(unsafe_hash=True)
class LigastavokLiveDataTemp:
    _league: str = field(init=False, repr=False)
    _status: str = field(init=False, repr=False)
    _href: str = field(init=False, repr=False)
    _member_1: str = field(init=False, repr=False)
    _member_2: str = field(init=False, repr=False)
    _current_score: str = field(init=False, repr=False)
    _total_score: str = field(init=False, repr=False)
    _bets: List[str] = field(init=False, repr=False)

    # служебные поля
    # хранит код
    event_raw_data: str = field(init=True, repr=False)
    _event_raw_data: str = field(init=False, repr=False)

    league: str = None  # Лига, турнир события
    status: str = None  # статус события на момент извлечения данных
    href: str = None  # ссылка на страницу с детальными ставками
    member_1: str = None  # название домашней комманды, либо одиночного парри
    member_2: str = None  # название гостевой комманды,либо пусто для 1-го пари
    current_score: str = None  # счет события на момент извлечения данных
    total_score: str = None  # общий счет на момент извлечния данных
    bets: List[str] = None  # перечень ставок

    def __init__(self, raw_data=None, league=None, status=None, href=None,
                 member_1=None,
                 member_2=None, current_score=None, total_score=None,
                 bets=None):
        self.event_raw_data = raw_data
        self.league = league
        self.status = status
        self.href = href
        self.member_1 = member_1
        self.member_2 = member_2
        self.current_score = current_score
        self.total_score = total_score
        self.bets = bets

        self._div_main = None
        self._div_info = None
        self._members = None

    def __post_init__(self):
        self.league: str = ''  # Лига, турнир события
        self.status: str = ''  # статус события на момент извлечения данных
        self.href: str = ''  # ссылка на страницу с детальными ставками
        self.member_1: str = ''  # название домашней комманды/одиночного парри
        self.member_2: str = ''  # название гостевой комманды
        self.current_score: str = ''  # счет события на момент извлечения
        self.total_score: str = ''  # общий счет на момент извлечния данных
        self.bets: List[str] = []  # перечень ставок

        self.updated = False
        self._div_main = None
        self._div_info = None
        self._members = None  # участники пари, может быть один или несколько
        self.errors = []

    def reset(self):
        self._league = ''
        self._status = ''
        self._href = ''
        self._member_1 = ''
        self._member_2 = ''
        self._current_score = ''
        self._total_score = ''
        self._bets = []

        self._div_main = None
        self._div_info = None
        self._members = None

    @property
    def event_raw_data(self):
        if not self._event_raw_data:
            raise ValueError(
                f'{self.__class__.__name__!r}.event_raw_data cannot be empty')
        return self._event_raw_data

    @event_raw_data.setter
    def event_raw_data(self, value):
        print(f'def event_raw_data(self, value={value!r})')
        if not value:
            value = BeautifulSoup()
        elif isinstance(value, str):
            value = BeautifulSoup(value)
        elif not isinstance(value, (BeautifulSoup,)):
            raise ValueError(
                f"{self.__class__.__name__!r}.event_raw_data "
                f"must be the 'BeautifulSoup' instance")
        self._event_raw_data = value
        self.reset()

    @property
    def div_main(self):
        if not self._div_main:
            self._div_main = self.event_raw_data.find('div', class_=re.compile(
                "column_main"))
        return self._div_main or BeautifulSoup()

    @property
    def league(self):
        if not self._league:
            elem = self.div_main.find('div', class_=re.compile("league"))
            self._league = clr_txt(elem.get_text()) if elem else ""
        return self._league

    @league.setter
    def league(self, value):
        self._league = value

    @property
    def status(self):
        if not self._status:
            elem = self.div_main.find('div', class_=re.compile('status'))
            self._status = clr_txt(elem.get_text()) if elem else ""
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def div_info(self):
        if not self._div_info:
            self._div_info = self.div_main.find('div',
                                                class_=re.compile('info'))
        return self._div_info or BeautifulSoup()

    @property
    def members(self):
        if not self._members:
            elem = self.div_info.a
            self._members = [element.string for element in
                             elem.find_all('span')] if elem else []
        return self._members

    @property
    def member_1(self):
        return '' if not self.members or len(self.members) < 1 else \
            self.members[0]

    @member_1.setter
    def member_1(self, value):
        self._member_1 = value

    @property
    def member_2(self):
        return '' if not self.members or len(self.members) < 2 else \
            self.members[1]

    @member_2.setter
    def member_2(self, value):
        self._member_2 = value

    @property
    def href(self):
        if not self._href:
            elem = self.div_info.a
            self._href = elem.get('href') if elem else ""
        return self._href

    @href.setter
    def href(self, value):
        self._href = value

    @property
    def current_score(self):
        if not self._current_score:
            current_score = self.div_info.find('div', re.compile('current'))
            self._current_score = clr_txt(
                current_score.get_text()) if current_score else ''
        return self._current_score

    @current_score.setter
    def current_score(self, value):
        self._current_score = value

    @property
    def total_score(self):
        if not self._total_score:
            total_score = self.div_info.find('div', re.compile('total'))
            self._total_score = clr_txt(
                total_score.get_text()) if total_score else ''
        return self._total_score

    @total_score.setter
    def total_score(self, value):
        self._total_score = value

    @property
    def bets(self):
        if not self._bets:
            outcomes = self.event_raw_data.find('div',
                                                re.compile('column_outcome'))
            bets = []
            if outcomes:
                for outcome in outcomes.find_all('div', re.compile(
                        'bui-group-outcome__wrapper')):
                    bets.append([clr_txt(element.string)
                                 for element in outcome.div.contents
                                 if element.name == 'div'])
            self._bets = bets
        return self._bets

    @bets.setter
    def bets(self, value):
        self._bets = value
