__version__ = '0.6.0-dev'
__author__ = 'Christian Brickhouse'

import time
import json
from random import randint  # For testing purposes.

from selenium import webdriver

import Game
import ResponseParsing


class Scraper():
    def __init__(self,default_wait=2):
        self.games = []
        self.browser = webdriver.PhantomJS()
        if default_wait < 1:
            raise ValueError('Wait must be at least 1 second as a courtesy.')
        else:
            self.default_wait = default_wait
        self.jparse = ResponseParsing.JeopardyParser()
        
    def scrape(self,start,stop=None,step=1,wait=None,random=True):
        request_time = 0
        if type(wait) is not int:
            wait = self.default_wait
        if stop == None:
            stop = start + 1
        elif stop <= start:
            raise ValueError('Stop must be greater than start value.')
        else:
            stop += 1  # So range gives an i such that start <= i <= stop
        for i in range(start,stop,step):
            if random:
                i = i+randint(0,step-1)  # Offset to pick semi-random pages.
            print(i)
            url = 'http://www.j-archive.com/showgame.php?game_id='+str(i)
            if (time.time() - request_time) < wait:
                print('Requesting too fast, waiting %s seconds...'%wait)
                time.sleep(wait) 
                print('Continuing')
            self.browser.get(url)
            request_time = time.time() 
            html = self.browser.page_source
            if i > 5500:
                if self._checkEnd(html,i):
                    break
            game = Game.Game(html,url)
            self.games.append(game)
            
    def parse_all(self):
        total = 0
        notQuestions = 0
        for game in self.games:
            for round_ in game.clues:
                if round_ == 'final_jeopardy_round':
                    continue
                for clue in game.clues[round_]:
                    if clue.annotation:
                        for response in clue.responses:
                            sentence = response[1]
                            tree = jparse.parse(sentence)[0]
                            total += 1
                            if not ResponseParsing.check_syntax(tree):
                                print(sentence)
                                notQuestions+=1
            
    def save(self,fname='JeopardyData.json'):
        serial = []
        for game in self.games:
            serial.append(game.__dict__())
        json_output = json.dumps(serial)
        with open(fname,'w') as f:
            f.write(json_output)
    
    def load(self,fname='JeopardyData.json'):
        with open(fname,'r') as f:
            json_input = json.load(f)
        self.games = []
        for game in json_input:
            self.games.append(Game.Game(load=True,**game))

    def _checkEnd(self, source, id_):
        error_string = 'ERROR: No game %s in database.'%str(id_)
        if error_string in source:
            return(True)
        else:
            return(False)
            
    def __len__(self):
        l = len(self.games)
        return(l)
        
    def __str__(self):
        text = []
        for game in self.games:
            text.append(game.title)
        text = '\n'.join(text)
        return(text)
