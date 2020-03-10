import os.path
import sys
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import pandas as pd
from lxml import html

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import logging
import re

import settings
import bets_utils


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
        with open(file="detail_bets_html.txt", mode='r') as f:
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


class LigastavokLive(LigastavokBase):
    def __init__(self, web_driver: webdriver, url: str):
        super(LigastavokLive, self).__init__(web_driver=web_driver, url=url)
        self.bet_matches = []

    def process(self):
        def clr_txt(s: str) -> str:
            return s.replace('\\n', '').replace('\\t', '').replace("', '", '').strip()
        logging.debug(f"Загружаем контент в BeautifulSoup")
        # b_s = BeautifulSoup(self.get_content(), "lxml")
        b_s = BeautifulSoup(self.get_content(), "html.parser")
        all_events = b_s.find_all('div', class_=re.compile('bui-event-row'), itemtype="http://schema.org/Event")
        for event in all_events:
            main = event.find('div', class_=re.compile('column_main'))
            league = main.find('div', class_=re.compile('league')).get_text()
            league = clr_txt(league)
            status = (main.find('div', class_=re.compile('status')).get_text())
            status = clr_txt(status)
            info = main.find('div', class_=re.compile('info'))
            href = info.a.get('href')
            teams = info.a.find_all('span')
            home_team = teams[0].string
            guest_team = teams[1].string
            current_score = info.find('div', re.compile('current'))
            current_score = current_score.get_text() if current_score else ''
            total_score = info.find('div', re.compile('total'))
            total_score = total_score.get_text() if total_score else ''
            outcomes = event.find('div', re.compile('column_outcome'))
            bets = []
            for outcome in outcomes.find_all('div', re.compile('bui-group-outcome__wrapper')):
                bets.append([clr_txt(element.string) for element in outcome.div.contents if element.name == 'div'])
            print(f"league:{league}; status:{status}; href:{href}; home_team:{home_team}; guest_team:{guest_team}; "
                  f"current_score:{current_score}; total_score:{total_score}; bets:{bets}")

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
