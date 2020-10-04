from selenium import webdriver
from selenium.webdriver.support.events import EventFiringWebDriver

import time

from mylistener import MyListener

url = 'http://www.ligastavok.ru'


class Bot(object):
    def __init__(self, page='', driver_path='', Listener=None):
        self.page = page
        if Listener:
            self.driver = EventFiringWebDriver(
                webdriver.Chrome(),
                MyListener()
            )
        else:
            if driver_path:
                self.driver = webdriver.Chrome(driver_path)
            else:
                self.driver = webdriver.Chrome()

    def parse(self):
        # TODO подумать как запускать парсеры и добавлять их в бот
        bot = self.driver
        content = bot.find_element_by_id('content')
        xpath = '//*[contains(@itemtype, "http://schema.org/Event") ' \
                'and contains(@class, "bui-event-row")]'
        elems = content.find_elements_by_xpath(xpath)
        for elem in elems:
            print(elem.text)

    def do(self, sec=60):
        begintime = time.time()

        while time.time() - begintime < sec:
            print('=' * 50)
            self.parse()
            time.sleep(10)
        self.driver.quit()


if __name__ == '__main__':
    # driver = webdriver.Chrome()
    # edriver = EventFiringWebDriver(driver, MyListener())
    # edriver.get(url)
    # content = edriver.find_element_by_id('content')
    # xpath = '//*[contains(@itemtype, "http://schema.org/Event") ' \
    #         'and contains(@class, "bui-event-row")]'
    # elems = driver.find_elements_by_xpath(xpath)
    # for elem in elems:
    #     print(elem.text)
    # # while edriver:
    # #     pass
    # edriver.quit()
    bot = Bot(page=url)
    bot.do(sec=5)
