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
        logging.debug(f"Создается экземпляр {self.__class__.__name__} с параметрами webdriver:{webdriver.name} url:{url}")
        assert webdriver and url
        self.driver = webdriver
        self.url = url
        self.errors = {}
        self.idling = 0
        self.soup = None


        #создаем вкладку в которой будет загружаться веб-страница
        self.tab_name = "test"  #ToDo: придумать генератор названия вкладки
        js = f"window.open('{self.url}', '{self.tab_name}');"
        logging.debug(f"Создаем новую вкладку скриптом js: {js}")
        self.driver.execute_script(js)

        #TODO: в класс передавать родительский объект и в него записывать себя для возможности управления из родителя

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
            self.driver.quit()


    @classmethod
    def execute(cls, webdriver: webdriver, url: str):
        instance = cls(webdriver, url)
        instance.prepare()
        while instance.idling < settings.MAX_IDLE:
            instance.process()
            instance.check_changes()
            time.sleep(settings.BET_SLEEP)




class Ligastavok(BetParser):
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


def main():
    bets_utils.set_logging(logging.DEBUG)
    url = "https://www.ligastavok.ru/bets/live"
    url = 'about:blank'
    
    driver_path = settings.PATH_CHROMEDRIVER.split('/')
    # driver_path = os.path.join(os.getcwd(), *driver_path)
    self_path = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(self_path, *driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    logging.debug(f"Старт программы с параметрами driver_path:{driver_path},  url:{url}")
    if os.path.exists(driver_path):
        # print(driver_path)

        # service = Service(driver_path)
        # service.start()
        # wd = webdriver.Remote(service.service_url)
        wd = webdriver.Chrome(
            executable_path=driver_path, 
            service_log_path=self_path,
            options=options)
        Ligastavok.execute(wd, url)
        wd.close()
    else:
        print("Is not found ", driver_path)
        logging.debug("Выход из программы")


if __name__ == "__main__":
    main()