import datetime
import re
from dataclasses import dataclass, field
from typing import List

from bs4 import BeautifulSoup

from bets_utils import clr_txt


@dataclass
class LigastavokBetData:
    _data: BeautifulSoup = field(init=True, repr=False)
    snapshot_time: str = field(init=False, repr=True)
    status: str = field(init=False, repr=True)
    current_score: str = field(init=False, repr=True)
    total_score: str = field(init=False, repr=True)
    bets: List[List[str]] = field(init=False, repr=True)

    def __post_init__(self):
        self._snapshot_time = datetime.datetime.now()
        div_main = self._data.find('div', class_=re.compile(
            'column_main')) or BeautifulSoup()
        elem = div_main.find('div', class_=re.compile('status'))
        self.status = clr_txt(elem.get_text()) if elem else ""
        div_info = div_main.find('div',
                                 class_=re.compile('info')) or BeautifulSoup()

        elem = div_info.find('div', re.compile('current'))
        self.current_score = clr_txt(elem.get_text()) if elem else ''

        elem = div_info.find('div', re.compile('total'))
        self.total_score = clr_txt(elem.get_text()) if elem else ''
        div_outcomes = self._data.find('div', re.compile('column_outcome'))
        bets = []
        if div_outcomes:
            for outcome in div_outcomes.find_all('div', re.compile(
                    'bui-group-outcome__wrapper')):
                bets.append(
                    [clr_txt(element.string)
                     for element in outcome.div.contents
                     if element.name == 'div'])
        self.bets = bets

    @property
    def snapshot_time(self):
        return self._snapshot_time.strftime('%d-%m-%Y %H:%M:%S')

    @snapshot_time.setter
    def snapshot_time(self, value):
        pass


@dataclass
class LigastavokEventData:
    _data: BeautifulSoup = field(init=True, repr=False,
                                 default_factory=lambda: BeautifulSoup())
    league: str = field(init=False, repr=True, default="Undefine")
    href: str = field(init=False, repr=True, default="Undefine")
    member_1: str = field(init=False, repr=True, default="Undefine")
    member_2: str = field(init=False, repr=True, default="-")
    bets: List[LigastavokBetData] = field(init=False, repr=True,
                                          default_factory=lambda: [])

    def __post_init__(self):
        if isinstance(self._data, str):
            self._data = BeautifulSoup(self._data)
        div_main = self._data.find('div', class_=re.compile(
            'column_main')) or BeautifulSoup()
        elem = div_main.find('div', class_=re.compile('league'))
        self.league = clr_txt(elem.get_text()) if elem else self.league
        div_info = div_main.find('div',
                                 class_=re.compile('info')) or BeautifulSoup()
        elem = div_info.a
        self.href = elem.get('href') if elem else self.href
        members = [element.string for element in
                   elem.find_all('span')] if elem else []
        self.member_1 = '' if not members or len(members) < 1 else members[0]
        self.member_2 = '' if not members or len(members) < 2 else members[1]
        elem = div_info.find('div', re.compile('total'))
        self._total_score = clr_txt(elem.get_text()) if elem else ''
        self.bets = [LigastavokBetData(self._data)]
