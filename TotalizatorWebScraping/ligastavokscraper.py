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


class BaseBetScraper(object):
    """
        Description for BaseScraper
        Class for base metods of web scraping
    """

    def __init__(self, driver_path=None):
        """
        Constructor for BaseScraper

        Args:

        """

        if isinstance(driver_path, str):
            if os.path.exists(driver_path):
                self.driver = webdriver.Chrome(driver_path)
        else:
            driver_path = 'chromedriver'
            if sys.platform.startswith('win'):
                driver_path += '.exe'
            self.driver = webdriver.Chrome(driver_path)

        self.content = None
        self.start()

    def start(self, ):
        """

        Args:


        Returns:
            None
        """
        pass

    def stop(self, ):
        """

        Args:


        Returns:
            None
        """
        self.driver.close()
        pass

    def get_element_by_xpath(self, xpath=None, parent_element=None, single=True, pos=None):
        """ищет элемент по одному пути или списку

        Args:
            xpath - selector to target element
            parent_element - object of webelement in which start looking for target element
            single - looking for one element or list
            pos - if 'single' is False, when None = return all list , else return item by 'pos' position
        Returns:
            webelement object
        """
        if not xpath:
            raise ValueError('ERROR: parameter xpath cannot be empty')
        if isinstance(xpath, str):
            xpath = [xpath]
        if not isinstance(xpath, list):
            raise ValueError('ERROR: param xpath must be a list or a string')

        for path in xpath:
            try:
                if parent_element:
                    res = parent_element.find_element_by_xpath(path) if single else \
                        parent_element.find_elements_by_xpath(path)
                elif self.content:
                    res = self.content.find_element_by_xpath(path) if single else \
                        self.content.find_elements_by_xpath(path)
                else:
                    res = self.driver.find_element_by_xpath(path) if single else \
                        self.driver.find_elements_by_xpath(path)
                if res:
                    if single or pos is None:  # if we get one element or list of elements without concrete position
                        return res
                    else:
                        if not isinstance(pos, (int, slice)):
                            raise TypeError('ERROR: BaseBetScraper.get_element_by_xpath. param "pos" must be int or '
                                            'slice')
                        return res[pos] if isinstance(pos, int) else res[pos][0]
            except NoSuchElementException as err:
                # TODO: write error event to log
                caller = sys._getframe(1).f_code.co_name
                print(f'Error in find element by xpath: {path}, called by: {caller}', err)
        # raise NoSuchElementException(f'Error in find element by xpath: {xpath}')
        return ''


class LigaStavokScraper(BaseBetScraper):
    """
        WebSrapering of site https://www.ligastavok.ru for extract bet's data
    """

    def __init__(self, url='', driver_path=None, sec_execute=60):

        # TODO: создать класс с данными и туда передавать результаты парсинга
        self.sec_execute = sec_execute

        self.sport_kind = []
        self.home_team = []
        self.guest_team = []
        self.match_day = []
        self.match_location = []
        self.bet_1 = []
        self.bet_X = []
        self.bet_2 = []
        self.df = None

        self.url = url if url else 'https://www.ligastavok.ru/'
        super(LigaStavokScraper, self).__init__(driver_path=driver_path)

    def start(self):
        url = 'https://www.ligastavok.ru/bets/live'
        self.driver.get(url)
        timeout = 30
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.ID, "content")))
        except TimeoutException:
            self.stop()

        start_time = time.time()
        iteration = 1
        while time.time() - start_time <= self.sec_execute:
            print(f'{" Current iteration %s " % str(iteration):=^60}')
            # try:
            #     self.parse_live_events()
            #     time.sleep(5)
            #     iteration += 1
            # except Exception as err:
            #     print('ERROR: LigaStavokScraper.start(). Message:', err, err.args, sys._getframe(1).f_code.co_name)
            #     time.sleep(1)
            #     self.stop()
            self.parse_live_events()
            time.sleep(5)
            iteration += 1
        time.sleep(1)
        self.stop()
        self.df = pd.DataFrame.from_dict(
            {
                'sport_kind': self.sport_kind,
                'home_team': self.home_team,
                'guest_team': self.guest_team,
                'match_day': self.match_day,
                'match_location': self.match_location,
                '1': self.bet_1,
                'X': self.bet_X,
                '2': self.bet_2,
            }
        )
        self.df.to_csv('web_data.csv')

    def parse_live_events(self):
        # url = 'https://www.ligastavok.ru/bets/live'
        # self.driver.get(url)
        # timeout = 30
        # try:
        #     WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.ID, "content")))
        # except TimeoutException:
        #     self.stop()

        xpath_content = ['//div[@id = "content"]//*[contains(@class, "live__events-block")]', '//div[@id = "content"]']
        xpath_items = './/*[@itemtype = "http://schema.org/Event" and contains(@class, "bui-event-row")]'

        # try:
        #     self.content = self.driver.find_element_by_xpath(xpath_content)
        # except NoSuchElementException as err:
        #     # TODO: сделать обработку в цикле для перебора списка строк xpath через отдельный метод
        #     msg = f'Error in parse_live_events() with define a content container. Message: {err}'
        #     print(msg)
        #     raise
        self.content = self.get_element_by_xpath(xpath=xpath_content)
        self.tree = html.fromstring(self.content.get_attribute('innerHTML'))

        # try:
        #     events_elements = content.find_element_by_xpath(xpath_items)
        # except NoSuchElementException as err:
        #     # TODO: сделать обработку в цикле для перебора списка строк xpath
        #     msg = f'Error in parse_live_events() with define elements of events\nMessage: {err}'
        #     print(msg)
        #     raise

        # lxml
        # events_elements = self.get_element_by_xpath(xpath=xpath_items, single=False)
        events_elements = self.tree.xpath(xpath_items)
        print('Found %s events' % str(len(events_elements)))

        for i, event in enumerate(events_elements):
            start_time = time.time()
            strtime = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
            print(f'{strtime} Start parsing #{i+1} event', end='')
            # Todo: skip find element - continue
            # xpath = './/div[contains(@class, "bui-event-row-outcome__lock")]'
            sport_kind = self.get_sport_kind(event)
            home_team = self.get_home_team(event)
            guest_team = self.get_guest_team(event)
            match_day = self.get_match_day(event)
            match_location = self.get_match_location(event)
            bet_1 = self.get_bet_1(event)
            bet_x = self.get_bet_x(event)
            bet_2 = self.get_bet_2(event)

            self.sport_kind.append(sport_kind)
            self.home_team.append(home_team)
            self.guest_team.append(guest_team)
            self.match_day.append(match_day)
            self.match_location.append(match_location)
            self.bet_1.append(bet_1)
            self.bet_X.append(bet_x)
            self.bet_2.append(bet_2)

            strtime = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
            print(f'\t{home_team} - {guest_team}. \t Finish parsing. Duration: {time.time() - start_time:0.2f}')



    def get_sport_kind(self, element):
        xpath = './/*[contains(@class, "game-icon")]'
        attribute = 'data-icon'
        # try:
        #     elem = element.find_element_by_xpath(xpath)
        #     return elem.get_attribute('data-icon')
        # except Exception as e:
        #     print(f"Ошибка! get_sport_kind {e}: {e.args}")
        #     return ''

        # lxml
        # target_elem = self.get_element_by_xpath(xpath=xpath, parent_element=element)
        # return target_elem.get_attribute(name=attribute)
        target_elem = element.xpath(xpath)[0]
        return target_elem.attrib.get(attribute, 'none')

    def get_home_team(self, element):
        xpath = './/*[@itemprop="name"]'
        pos = 0  # 0 - home team
        # try:
        #     elem = element.find_elements_by_xpath(xpath)
        #     return elem[0].text
        # except Exception as e:
        #     print(f"Ошибка! get_home_team {e}: {e.args}")
        #     return ''

        # lxml
        # target_elem = self.get_element_by_xpath(xpath=xpath, parent_element=element, single=False, pos=pos)
        # return target_elem.text if target_elem else ''

        target_elem = element.xpath(xpath)
        return target_elem[pos].text if target_elem else 'None'

    def get_guest_team(self, element):
        xpath = './/*[@itemprop="name"]'
        pos = 1  # 1 - home team
        # try:
        #     xpath = './/*[@itemprop="name"]'
        #     elem = element.find_elements_by_xpath(xpath)
        #     return elem[1].text
        # except Exception as e:
        #     print(f"Ошибка! get_guest_team {e}: {e.args}")
        #     return ''

        # lxml
        # target_elem = self.get_element_by_xpath(xpath=xpath, parent_element=element, single=False, pos=pos)
        # return target_elem.text if target_elem else ''

        target_elem = element.xpath(xpath)
        return target_elem[pos].text if target_elem else 'None'

    def get_match_day(self, element):
        pass
        return ''

    def get_match_location(self, element):
        xpath = './/*[@itemprop="location"]'
        # try:
        #     elem = element.find_element_by_xpath(xpath)
        #     return elem.text
        # except Exception as e:
        #     print(f"Ошибка! get_match_location {e}: {e.args}")
        #     return ''

        # lxml
        # target_elem = self.get_element_by_xpath(xpath=xpath, parent_element=element)
        # return target_elem.text if target_elem else ''
        target_elem = element.xpath(xpath)
        return target_elem[0].text if target_elem else ''

    def get_bet_1(self, element):
        xpath = './/*[@itemprop="offers"]'
        pos = slice(0, 1)  # first score
        # try:
        #     elem = element.find_elements_by_xpath(xpath)
        #     return elem[0].text if len(elem) > 0 else ''
        # except Exception as e:
        #     print(f"Ошибка! get_bet_1 {e}: {e.args}")
        #     return ''

        # xlml
        # target_elem = self.get_element_by_xpath(xpath=xpath, parent_element=element, single=False, pos=pos)
        # return target_elem.text if target_elem else 'None'

        target_elem = element.xpath(xpath)[:3]
        return target_elem[pos][0].text if target_elem else 'None'

    def get_bet_2(self, element):
        xpath = './/*[@itemprop="offers"]'
        pos = slice(-1, None)  # last score
        # pos = 2

        # try:
        #     elem = element.find_elements_by_xpath(xpath)
        #     if len(elem) == 0:
        #         return ''
        #     return elem[2].text if len(elem) >= 3 else elem[1].text
        # except Exception as e:
        #     print(f"Ошибка! get_bet_2 {e}: {e.args}")
        #     return ''

        # xlml
        # target_elem = self.get_element_by_xpath(xpath=xpath, parent_element=element, single=False, pos=pos)
        # return target_elem.text if target_elem else ''
        target_elem = element.xpath(xpath)[:3]
        return target_elem[pos][0].text if target_elem else 'None'


    def get_bet_x(self, element):
        xpath = './/*[@itemprop="offers"]'
        pos = slice(1, -1)
        # try:
        #     elem = element.find_elements_by_xpath(xpath)
        #     return elem[1].text if len(elem) >= 3 else ''
        # except Exception as e:
        #     print(f"Ошибка! get_bet_X {e}: {e.args}")
        #     return ''

        # xlml
        # target_elem = self.get_element_by_xpath(xpath=xpath, parent_element=element, single=False, pos=pos)
        # return target_elem.text if target_elem else ''

        target_elem = element.xpath(xpath)[:3]
        return target_elem[pos][0].text if target_elem else 'None'


class ParseData(object):
    """
        Description for ParseData
        Класс для хранения инормации из парсера
    """

    def __init__(self, ):
        """
        Constructor for ParseData

        Args:

        """


if __name__ == '__main__':
    bot = LigaStavokScraper(url='https://www.ligastavok.ru/bets/live', sec_execute=50)
    print(bot.df.__repr__())
