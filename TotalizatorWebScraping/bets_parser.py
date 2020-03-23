import datetime
import os.path
import time
from typing import List, Dict

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from selenium import webdriver
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
import logging
import re

import settings
import bets_utils
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
            f"Создается экземпляр {self.__class__.__name__} с параметрами webdriver:{webdriver.name} url:{url}")
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

        # TODO: в класс передавать родительский объект и в него записывать себя для возможности управления из родителя

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
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.ID, "content")))
        except TimeoutException:
            logging.debug(f"время ожидания загрузки контента превысело {timeout} сек. ")
            self.idling = settings.MAX_IDLE
            return

        logging.debug(f"контент загружен. Загружаем контент в BeautifulSoup")
        self.soup = BeautifulSoup(self.driver.find_element_by_id("content"), "lxml")

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
        xpath = "//div[contains(@class,'bui-outcome')]"
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


class BaseBetParser(object):
    """
    парсер страничек с лайвом
    """

    def __init__(self, web_driver: webdriver, url: str):
        logging.debug(
            f"Создается экземпляр {self.__class__.__name__} с параметрами webdriver:{web_driver.name} url:{url}")
        # assert webdriver and url
        self.driver = web_driver
        self.url = url
        self.errors = {}
        self.idling = 0
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


class LigastavokBase(BaseBetParser):
    """
    базовый класс для сайта https://www.ligastavok.ru
    """

    def prepare(self):
        logging.debug(f"Переходим по url:{self.url}")
        self.driver.get(self.url)

        timeout = 30
        logging.debug(f"ждем в течении {timeout} сек. для загрузки контента")
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.ID, "content")))
        except TimeoutException:
            logging.debug(f"время ожидания загрузки контента превысело {timeout} сек. ")
            # self.errors.  todo: добавить сообщение об ошибке. Понять почему ошибки словарем сделаны
            self.idling = settings.MAX_IDLE
            return
        logging.debug("данные успешно загруженны")


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
    member_2: str = None  # название гостевой комманды, либо пусто для одиночного пври
    current_score: str = None  # счет события на момент извлечения данных
    total_score: str = None  # общий счет на момент извлечния данных
    bets: List[str] = None  # перечень ставок

    def __init__(self, raw_data=None, league=None, status=None, href=None, member_1=None,
                 member_2=None, current_score=None, total_score=None, bets=None):
        self.event_raw_data = raw_data
        self.league = league
        self.status = status
        self.href = href
        self.member_1 = member_1
        self.member_2 = member_2
        self.current_score = current_score
        self.total_score = total_score
        self.bets = bets

    def __post_init__(self):
        self.league: str = None  # Лига, турнир события
        self.status: str = None  # статус события на момент извлечения данных
        self.href: str = None  # ссылка на страницу с детальными ставками
        self.member_1: str = None  # название домашней комманды, либо одиночного парри
        self.member_2: str = None  # название гостевой комманды, либо пусто для одиночного пври
        self.current_score: str = None  # счет события на момент извлечения данных
        self.total_score: str = None  # общий счет на момент извлечния данных
        self.bets: List[str] = None  # перечень ставок

        self.updated = False
        self._div_main = None
        self._div_info = None
        self._members = None  # участники пари, может быть один или несколько
        self.errors = []

    def reset(self):
        self._league = None
        self._status = None
        self._href = None
        self._member_1 = None
        self._member_2 = None
        self._current_score = None
        self._total_score = None
        self._bets = None

        self._div_main = None
        self._div_info = None
        self._members = None

    @property
    def event_raw_data(self):
        if not self._event_raw_data:
            raise ValueError(f'{self.__class__.__name__!r}.event_raw_data cannot be empty')
        return self._event_raw_data

    @event_raw_data.setter
    def event_raw_data(self, value):
        print(f'def event_raw_data(self, value={value!r})')
        if not value:
            value = BeautifulSoup()
        if isinstance(value, str):
            value = BeautifulSoup(value)
        if not isinstance(value, (BeautifulSoup,)):
            raise ValueError(f"{self.__class__.__name__!r}.event_raw_data must be the 'BeautifulSoup' instance")
        self._event_raw_data = value
        self.reset()

    @property
    def div_main(self):
        if not self._div_main:
            self._div_main = self.event_raw_data.find('div', class_=re.compile('column_main'))
        return self._div_main or BeautifulSoup()

    @property
    def league(self):
        if not self._league:
            elem = self.div_main.find('div', class_=re.compile('league'))
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
            self._div_info = self.div_main.find('div', class_=re.compile('info'))
        return self._div_info or BeautifulSoup()

    @property
    def members(self):
        if not self._members:
            elem = self.div_info.a
            self._members = [element.string for element in elem.find_all('span')] if elem else []
        return self._members

    @property
    def member_1(self):
        return '' if not self.members or len(self.members) < 1 else self.members[0]

    @member_1.setter
    def member_1(self, value):
        self._member_1 = value

    @property
    def member_2(self):
        return '' if not self.members or len(self.members) < 2 else self.members[1]

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
            self._current_score = clr_txt(current_score.get_text()) if current_score else ''
        return self._current_score

    @current_score.setter
    def current_score(self, value):
        self._current_score = value

    @property
    def total_score(self):
        if not self._total_score:
            total_score = self.div_info.find('div', re.compile('total'))
            self._total_score = clr_txt(total_score.get_text()) if total_score else ''
        return self._total_score

    @total_score.setter
    def total_score(self, value):
        self._total_score = value

    @property
    def bets(self):
        if not self._bets:
            outcomes = self.event_raw_data.find('div', re.compile('column_outcome'))
            bets = []
            if outcomes:
                for outcome in outcomes.find_all('div', re.compile('bui-group-outcome__wrapper')):
                    bets.append([clr_txt(element.string) for element in outcome.div.contents if element.name == 'div'])
            self._bets = bets
        return self._bets

    @bets.setter
    def bets(self, value):
        self._bets = value


@dataclass
class LigastavokBetData:
    _data: BeautifulSoup = field(init=True, repr=False)
    snapshot_time: str = field(init=False, repr=True)
    status: str = field(init=False, repr=True)
    current_score: str = field(init=False, repr=True)
    total_score: str = field(init=False, repr=True)
    bets: Dict = field(init=False, repr=True)

    def __post_init__(self):
        self._snapshot_time = datetime.datetime.now()
        div_main = self._data.find('div', class_=re.compile('column_main')) or BeautifulSoup()
        elem = div_main.find('div', class_=re.compile('status'))
        self.status = clr_txt(elem.get_text()) if elem else ""
        div_info = div_main.find('div', class_=re.compile('info')) or BeautifulSoup()

        elem = div_info.find('div', re.compile('current'))
        self.current_score = clr_txt(elem.get_text()) if elem else ''

        elem = div_info.find('div', re.compile('total'))
        self.total_score = clr_txt(elem.get_text()) if elem else ''
        div_outcomes = self._data.find('div', re.compile('column_outcome'))
        bets = []
        if div_outcomes:
            for outcome in div_outcomes.find_all('div', re.compile('bui-group-outcome__wrapper')):
                bets.append([clr_txt(element.string) for element in outcome.div.contents if element.name == 'div'])
        self.bets = bets

    @property
    def snapshot_time(self):
        return self._snapshot_time.strftime('%d-%m-%Y %H:%M:%S')

    @snapshot_time.setter
    def snapshot_time(self, value):
        pass


@dataclass
class LigastavokEventData:
    _data: BeautifulSoup = field(init=True, repr=False, default_factory=lambda: BeautifulSoup())
    league: str = field(init=False, repr=True, default="Undefine")
    href: str = field(init=False, repr=True, default="Undefine")
    member_1: str = field(init=False, repr=True, default="Undefine")
    member_2: str = field(init=False, repr=True, default="-")
    bets: List[LigastavokBetData] = field(init=False, repr=True, default_factory=lambda: [])

    def __post_init__(self):
        if isinstance(self._data, str):
            self._data = BeautifulSoup(self._data)
        div_main = self._data.find('div', class_=re.compile('column_main')) or BeautifulSoup()
        elem = div_main.find('div', class_=re.compile('league'))
        self.league = clr_txt(elem.get_text()) if elem else self.league
        div_info = div_main.find('div', class_=re.compile('info')) or BeautifulSoup()
        elem = div_info.a
        self.href = elem.get('href') if elem else self.href
        members = [element.string for element in elem.find_all('span')] if elem else []
        self.member_1 = '' if not members or len(members) < 1 else members[0]
        self.member_2 = '' if not members or len(members) < 2 else members[1]
        elem = div_info.find('div', re.compile('total'))
        self._total_score = clr_txt(elem.get_text()) if elem else ''
        self.bets = [LigastavokBetData(self._data)]


class LigastavokLive(LigastavokBase):
    def __init__(self, web_driver: webdriver, url: str):
        super(LigastavokLive, self).__init__(web_driver=web_driver, url=url)
        self.bet_matches = []

    def process(self):

        logging.debug(f"Загружаем контент в BeautifulSoup")
        # b_s = BeautifulSoup(self.get_content(), "lxml")
        b_s = BeautifulSoup(self.get_content(), "html.parser")
        all_events = b_s.find_all('div', class_=re.compile('bui-event-row'), itemtype="http://schema.org/Event")
        data = [LigastavokEventData(event) for event in all_events]
        for i, item in enumerate(data):
            print(i, item)

        # for event in all_events:
        #     _main = event.find('div', class_=re.compile('column_main'))
        #     league = _main.find('div', class_=re.compile('league')).get_text()
        #     league = clr_txt(league)
        #     status = (_main.find('div', class_=re.compile('status')).get_text())
        #     status = clr_txt(status)
        #     _info = _main.find('div', class_=re.compile('info'))
        #     href = _info.a.get('href')
        #     _teams = _info.a.find_all('span')
        #     home_team = _teams[0].string
        #     guest_team = _teams[1].string if len(_teams) > 1 else ''
        #     current_score = _info.find('div', re.compile('current'))
        #     current_score = current_score.get_text() if current_score else ''
        #     total_score = _info.find('div', re.compile('total'))
        #     total_score = total_score.get_text() if total_score else ''
        #     _outcomes = event.find('div', re.compile('column_outcome'))
        #     bets = []
        #     for outcome in _outcomes.find_all('div', re.compile('bui-group-outcome__wrapper')):
        #         bets.append([clr_txt(element.string) for element in outcome.div.contents if element.name == 'div'])
        #     print(f"league:{league}; status:{status}; href:{href}; home_team:{home_team}; guest_team:{guest_team}; "
        #           f"current_score:{current_score}; total_score:{total_score}; bets:{bets}")

    def prepare(self):
        super(LigastavokLive, self).prepare()

    def get_content(self) -> str:
        # file = os.path.join(bets_utils.app_path(), "pages", "ligastavok_live.html")
        # with open(file, 'r') as f:
        #     return str(f.readlines())
        return self.driver.find_element_by_id("content").get_attribute('innerHTML')


def main():
    bets_utils.set_logging(logging.DEBUG)
    url = "https://www.ligastavok.ru/bets/live"
    # url = 'about:blank'

    driver_path = bets_utils.get_webdriver_path(browser=bets_utils.CHROME)
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920,1080")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-notifications")
    # options.add_argument("--enable-automation")
    # proxy_str = '--proxy-server=http://{0}:{1}'.format(
    #     PROXY_HOST, str(PROXY_PORT))
    # options.add_argument(proxy_str)
    # Ставим запрет на загрузку картинок
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    logging.debug(f"Старт программы с параметрами driver_path:{driver_path}, url:{url}")
    if os.path.exists(driver_path):
        wd = webdriver.Chrome(
            executable_path=driver_path,
            options=options,
        )
        # LigastavokProbe.execute(wd, url)   # парсер детальных данных
        LigastavokLive.execute(wd, url)
        if wd:
            wd.quit()
    else:
        print("Is not found ", driver_path)
        logging.debug("Выход из программы")


if __name__ == "__main__":
    main()
