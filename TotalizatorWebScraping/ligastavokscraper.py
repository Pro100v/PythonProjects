from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

class LigaStavokScraper(object):
    """
        WebSrapering of site https://www.ligastavok.ru for extract bet's data
    """

    def __init__(self, driver):
        # TODO: подумать принимать driver из вне или создавать внутри собственный для каждого парсера
        if isinstance(driver, RemoteWebDriver)
            self.driver = driver
        else:
            raise WebDriverException("You may not create a scraper with driver that is not is instance of WebDriver")
        self.sport_kind = []
        self.home_team = []
        self.guest_team = []
        self.match_day = []
        self.match_location = []
        self.bet_1 = []
        self.bet_X = []
        self.bet_2 = []

    def parse_live_events(self):
        url = 'https://www.ligastavok.ru/bets/live'
        xpath_content = '//div[@id = "content"]//*[contains(@class, "live__events-block")]'
        xpath_items = './/*[@itemtype = "http://schema.org/Event" and contains(@class, "bui-event-row")]'

        try:
            content = self.driver.find_element_by_xpath(xpath_content)
        except NoSuchElementException as err:
            # TODO: сделать обработку в цикле для перебора списка строк xpath через отдельный метод
            msg = f'Error in parse_live_events() with define a content container\nMessage: {err}'
            print(msg)
            raise

        try:
            events_elements = content.find_element_by_xpath(xpath_items)
        except NoSuchElementException as err:
            # TODO: сделать обработку в цикле для перебора списка строк xpath
            msg = f'Error in parse_live_events() with define elements of events\nMessage: {err}'
            print(msg)
            raise

        for event in events_elements:
            sport_kind = self.get_sport_kind(event)
            home_team = self.get_home_team(event)
            guest_team = self.get_guest_team(event)
            match_day = self.get_match_day(event)
            match_location = self.get_match_location(event)
            bet_1 = self.get_bet_1(event)
            bet_X = self.get_bet_X(event)
            bet_2 = self.get_bet_2(event)

            self.sport_kind.append(sport_kind)
            self.home_team.append(home_team)
            self.guest_team.append(guest_team)
            self.match_day.append(match_day)
            self.match_location.append(match_location)
            self.bet_1.append(bet_1)
            self.bet_X.append(bet_X)
            self.bet_2.append(bet_2)

    def get_sport_kind(self, element):
        try:
            xpath = './/*[contains(@class, "game-icon")]'
            elem = element.find_element_by_xpath(xpath)
            return elem.get_attribute('data-icon')
        except Exception as e:
            print(f"Ошибка! get_sport_kind {e}: {e.args}")
            return ''

    def get_home_team(self, element):
        try:
            xpath = './/*[@itemprop="name"]'
            elem = element.find_elements_by_xpath(xpath)
            return elem[0].text
        except Exception as e:
            print(f"Ошибка! get_home_team {e}: {e.args}")
            return ''

    def get_guest_team(self, element):
        try:
            xpath = './/*[@itemprop="name"]'
            elem = element.find_elements_by_xpath(xpath)
            return elem[1].text
        except Exception as e:
            print(f"Ошибка! get_guest_team {e}: {e.args}")
            return ''

    def get_match_day(self, element):
        pass
        return ''

    def get_match_location(self, element):
        try:
            xpath = './/*[@itemprop="location"]'
            elem = element.find_element_by_xpath(xpath)
            return elem.text
        except Exception as e:
            print(f"Ошибка! get_match_location {e}: {e.args}")
            return ''

    def get_bet_1(self, element):
        try:
            xpath = './/*[@itemprop="offers"]'
            elem = element.find_elements_by_xpath(xpath)
            return elem[0].text if len(elem) > 0 else ''
        except Exception as e:
            print(f"Ошибка! get_bet_1 {e}: {e.args}")
            return ''

    def get_bet_2(self, element):
        try:
            xpath = './/*[@itemprop="offers"]'
            elem = element.find_elements_by_xpath(xpath)
            if len(elem) == 0:
                return ''
            return elem[2].text if len(elem) >= 3 else elem[1].text
        except Exception as e:
            print(f"Ошибка! get_bet_2 {e}: {e.args}")
            return ''

    def get_bet_X(self, element):
        try:
            xpath = './/*[@itemprop="offers"]'
            elem = element.find_elements_by_xpath(xpath)
            return elem[1].text if len(elem) >= 3 else ''
        except Exception as e:
            print(f"Ошибка! get_bet_X {e}: {e.args}")
            return ''


