import re
from selenium import webdriver
from bs4 import BeautifulSoup as soup

class Game:
    title_regex = re.compile(r'#(\d+).*?([a-zA-Z]+), ([a-zA-Z]+) (\d+), (\d+)')
    rounds = ['jeopardy_round','double_jeopardy_round','final_jeopardy_round']
    def __init__(self,url,browser):
        browser.get(url)
        self.id_ = url.split('=')[-1]
        self._page_source = browser.page_source
        self._parsed_html = soup(page_source,"html.parser")
        self.title = self._parsed_html.body.find(
            'div',
            attrs={'id':'game_title'}
        ).text
        num,dow,mon,day,year = re.search(title_regex,game_title).groups()
        self.game_number = num
        self.weekday = dow
        self.month = mon
        self.day = day
        self.date = ' '.join([day,mon,year])
        self.year = year
        self._set_raw_clues()
        self._set_categories()
        
    def _set_raw_clues(self):
        self.raw_clues = parsed_html.body.find_all('td',attrs={'class':'clue'})
        if self.raw_clues = None or len(self.raw_clues) == 0:
            raise ValueError('This game has no clues?')
        return()
        
    def _parse_clues(self):
        if len(self.raw_clues) == 0:
            raise ValueError('This game has no clues?')
        for clue in self.raw_clues:
            Clue(clue,self)
            
    def _set_categories(self):
        catsByRound = {
            'jeopardy_round':[],
            'double_jeopardy_round':[],
            'final_jeopardy_round':[]
        }
        for round_ in rounds:
            gen = self._parsed_html.body.find_all(
                'td',
                attrs={'class':'category_name'}
                )
            for category in gen:
                catsByRound[round_].append(category.lower())
        self.categories = catsByRound
        
class Clue:
    response_regex = re.compile(r"stuck', '(.*)<em")
    wasCorrect_regex = re.compile(r'<td class="(right|wrong)">(.*?)<\/td>')
    target_regex = re.compile(r"correct_response.+?>(.*)</em>")
    def __init__(self,bs4_tag,game):
        self.game = game
        self.tag_obj = bs4_tag
        self._set_round() 
        self.order_num = int(
            self.tag_obj.find(
                'td',
                attrs={'class':'clue_order_number'}
            ).text
        )
        self._set_value()
        self._set_text()
        self.annotation = 
        self.target = 
        self.correct = 
        
    def _set_round(self):
        for parent in self.tag_obj.parents:
            if 'id' in parent.attrs:
                self.round_ = parent['id']
                break
                
    def _set_value(self):
        val = self.tag_obj.find(
            'td',
            attrs={'class':'clue_value'}
        )
        if val == None:
            val = self.tag_obj.find(
                'td',
                attrs={'class':'clue_value'}
            )
            if val == None:
                raise ValueError('Clue has no value?')
            else:
                self.daily_double = True
                val = val[4:]  # remove the 'DD: ' that precedes DD clue values
        else:
            self.daily_double = False
        self.value = int(val.strip().strip('$'))
        
    def _set_text(self):
        clue_tag = self.tag_obj.find('td',attrs={'class':'clue_text'})
        self.text = clue_tag.text
        self._set_category(clue_tag['id'])
        
    def _set_category(self,id_str):
        if id_str is 'clue_FJ':
            rnd = 'FJ'
        else:
            rnd,col,row = id_str.split('_')[1:]
        if (
                (rnd = 'J' and self.round_ is not 'jeopardy_round') or 
                (rnd = 'DJ' and self.round_ is not 'double_jeopardy_round') or
                (rnd = 'FJ' and self.round_ is not 'final_jeopardy_round')
        ):
            print('Rounds do not match for %s,\n\
            defaulting to round used in coordinates.' % id_str)
            if rnd == 'J':
                self.round_ = 'jeopardy_round'
            elif rnd = 'DJ':
                self.round_ = 'double_jeopardy_round'
            elif rnd = 'FJ':
                self.round_ = 'final_jeopardy_round'
        self.row = int(row)
        self.column = int(column)
        cats = self.game.categories[self.round_]
        self.category = cats[self.column-1]
    
    def _set_responses(self):
        annotation = None
        for div in self.tag_obj.find_all('div'):
            if div.has_attr('onmouseover'):
                annotation = div['onmouseover']
                break
        if annotation == None:
            raise ValueError('Clue has no response?')
        try:
            self.target = re.search(target_regex,annotation).group(1)
        except AttributeError:
            raise AttributeError('Clue has no correct response?')
        self.annotation = re.search(response_regex,annotation).group(1)
        responses = re.findall(wasCorrect_regex,annotation)
        if responses == []:
            print('Unknown whether response was correct or not.\n\
            Continuing regardless, here\'s diagnostic info:\n\tGame id: %s\n\
            \tDate: %s\n\tRound: %s\n\tClue coords (row,col): %s, %s' % (
                self.game.id_,
                self.game.date,
                self.round_
                self.row,
                self.col
            )
            self.correct = None
            continue
        for response in responses:
            player = response[1]
            if response[0] == 'right':
                self.correct = True
            elif response[0] == 'wrong' and self.correct is not True:
                self.correct = False:
            else:
                self.correct = None



url = 'http://www.j-archive.com/showgame.php?game_id=1'
browser = webdriver.PhantomJS()
