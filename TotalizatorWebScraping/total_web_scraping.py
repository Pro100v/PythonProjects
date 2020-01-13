from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener

import time


url = 'http://www.ligastavok.ru'


# class MyListener(AbstractEventListener):
#     def after_change_value_of(self, element, driver):
#         print('==== change value =======')
#         print(element.text)
#
#     def after_execute_script(self, script, driver):
#         print("after_execute_script")
#
#     def before_execute_script(self, script, driver):
#         print("before_execute_script")
#
#     def before_quit(self, driver):
#         print("before_quit")


class Bot(object):
    def __init__(self, page):
        self.page = page
        self.driver = EventFiringWebDriver(webdriver.Chrome(), MyListener())
        self.driver.get(self.page)


    def parse(self):
        bot = self.driver
        content = bot.find_element_by_id('content')
        xpath = '//*[contains(@itemtype, "http://schema.org/Event") and contains(@class, "bui-event-row")]'
        elems = content.find_elements_by_xpath(xpath)
        for elem in elems:
            print(elem.text)

    def do(self, sec=60):
        begintime = time.time()
        while time.time() - begintime < sec:
            print('=' * 10)
            self.parse()
            time.sleep(10)
        self.driver.quit()

class MyListener(AbstractEventListener):
    def before_navigate_to(self, url, driver):
        print("Before navigating to ", url)

    def after_navigate_to(self, url, driver):
        print("After navigating to ", url)

    def before_navigate_back(self, driver):
        print("before navigating back ", driver.current_url)

    def after_navigate_back(self, driver):
        print("After navigating back ", driver.current_url)

    def before_navigate_forward(self, driver):
        print("before navigating forward ", driver.current_url)

    def after_navigate_forward(self, driver):
        print("After navigating forward ", driver.current_url)

    def before_find(self, by, value, driver):
        print(f"before find {value}")

    def after_find(self, by, value, driver):
        print(f"after_find {value}")

    def before_click(self, element, driver):
        print("before_click")

    def after_click(self, element, driver):
        print("after_click")

    def before_change_value_of(self, element, driver):
        print(f"before_change_value_of {element}")

    def after_change_value_of(self, element, driver):
        print(f"after_change_value_of {element}")

    def before_execute_script(self, script, driver):
        print("before_execute_script")

    def after_execute_script(self, script, driver):
        print("after_execute_script")

    def before_close(self, driver):
        print("tttt")

    def after_close(self, driver):
        print("before_close")

    def before_quit(self, driver):
        print("before_quit")

    def after_quit(self, driver):
        print("after_quit")

    def on_exception(self, exception, driver):
        print("on_exception")


if __name__ == '__main__':
    # driver = webdriver.Chrome()
    # edriver = EventFiringWebDriver(driver, MyListener())
    # edriver.get(url)
    # content = edriver.find_element_by_id('content')
    # xpath = '//*[contains(@itemtype, "http://schema.org/Event") and contains(@class, "bui-event-row")]'
    # elems = driver.find_elements_by_xpath(xpath)
    # for elem in elems:
    #     print(elem.text)
    # # while edriver:
    # #     pass
    # edriver.quit()
    bot = Bot(page=url)
    bot.do()
