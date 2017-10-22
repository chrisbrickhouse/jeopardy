__version__ = '0.4.0-dev'
__author__ = 'Christian Brickhouse'

import time

from selenium import webdriver

import Game
import ResponseParsing

games=[]
browser = webdriver.PhantomJS()
request_time = 0
jparse = ResponseParsing.JeopardyParser()
for i in range(1,11):
    print(i)
    if (time.time() - request_time) < 10:
        print('Requesting too fast, waiting 10 seconds...')
        time.sleep(15) 
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
                        print(repr(sentence))
                        notQuestions+=1
