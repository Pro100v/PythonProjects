import os.path

from selenium import webdriver
import logging

import settings
import bets_utils
from sites.ligastavok.bot import LigastavokLive


def main():
    bets_utils.set_logging(logging.DEBUG)
    if settings.WO_INTERNET:
        url = "file://" + bets_utils.app_path("pages", "ligastavok_live.html")
    else:
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

    logging.debug(
        f"Старт программы с параметрами driver_path:{driver_path}, url:{url}")
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
