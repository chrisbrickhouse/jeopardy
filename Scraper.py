__version__ = '0.5.0-dev'
__author__ = 'Christian Brickhouse'

import time
from random import randint  # For testing purposes.

from selenium import webdriver

import Game
import ResponseParsing

wait = 2
games=[]
browser = webdriver.PhantomJS()
request_time = 0
jparse = ResponseParsing.JeopardyParser()
for i in range(1,6000,100):
    i = i+randint(0,99)  # Random offset so pages picked are semi-random.
    if (time.time() - request_time) < wait:
        print('Requesting too fast, waiting %s seconds...'%wait)
        time.sleep(wait) 
        print('Continuing')
    url = 'http://www.j-archive.com/showgame.php?game_id='+str(i)
    browser.get(url)
    request_time = time.time() 
    html = browser.page_source
    game = Game.Game(html,url)
    games.append(game)

total = 0
notQuestions = 0
for game in games:
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
