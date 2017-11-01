__version__ = '0.6.0-dev'
__author__ = 'Christian Brickhouse'

import re

from bs4 import BeautifulSoup as soup


class Game:
    """An object that represents a Jeopardy game and structures related data.
    
    The Game class creates an object that structures and contains data on a 
    given Jeopardy game from the j-archive. It contains data related to the 
    game as a whole and contains all of the clues (represented as Clue objects)
    within it.
    
    Attributes:
        id_         The game id used in the j-archive url.
        title       The title of the game, including the game number and date.
        game_number The number of the game in sequence from the first, different
                      from the id_. Game ID is j-archive specific, but 
                      game_number is numbered from the start of Jeopardy.
        date        The date the game aired in the format '(D)D Mon YYYY'.
        day         The day of the month on which the game aired.
        month       The month in which the game aired.
        year        The year in which the game aired.
        raw_clues   The bs4 tag elements for each of the clues.
        categories  A dictionary, with round names as keys, containing lists of
                      category names.
        clues       A dictionary, with round names as keys, containing lists of
                      all the Clue objects for that round.
                      
        TO ADD:
            *       Various objects related to score statistics and team 
                      batting avgerage.
    
    Methods:
        __init__    Initializes the game object.
    """
    
    title_regex = re.compile(r'#(\d+).*?([a-zA-Z]+), ([a-zA-Z]+) (\d+), (\d+)')
    rounds = ['jeopardy_round','double_jeopardy_round','final_jeopardy_round']
    
    def __init__(self,page_source=None,url=None,load=False,**kwargs):
        """Initialize important meta-data on the game."""
        if load:
            self.loaded = True
            self.load(**kwargs)
            return(None)
        else:
            self.loaded = False
        self.id_ = url.split('=')[-1]
        self._page_source = page_source
        self._parsed_html = soup(self._page_source,"html.parser")
        self.title = self._parsed_html.body.find(
            'div',
            attrs={'id':'game_title'}
        ).text
        num,dow,mon,day,year = re.search(self.title_regex,self.title).groups()
        self.game_number = num
        self.weekday = dow
        self.month = mon
        self.day = day
        self.date = ' '.join([day,mon,year])
        self.year = year
        notEmpty = self._set_raw_clues()
        if notEmpty:
            self._set_categories()
            self._parse_clues()
        else:
            self.clues={}
            for round_ in self.rounds:
                self.clues[round_] = []
            self.categories = {
                'jeopardy_round':[],
                'double_jeopardy_round':[],
                'final_jeopardy_round':[]
            }
    
    def load(self,**kwargs):
        self.id_ = kwargs['id_']
        self.title = kwargs['title']
        self.game_number = kwargs['game_number']
        self.weekday = kwargs['weekday']
        self.month = kwargs['month']
        self.day = kwargs['day']
        self.date = kwargs['date']
        self.year = kwargs['year']
        self.categories = kwargs['categories']
        self.clues = {
            'jeopardy_round':[],
            'double_jeopardy_round':[],
            'final_jeopardy_round':[]
        }
        for clue in kwargs['clues']:
            round_ = clue['round_']
            self.clues[round_].append(Clue(game=self,load=True,**clue))
            
        
    def _set_raw_clues(self):
        """Add all bs4 Tag objects for clues to a list, self.raw_clues"""
        self.raw_clues = self._parsed_html.body.find_all(
            'td',
            attrs={'class':'clue'}
        )
        if self.raw_clues == None or len(self.raw_clues) == 0:
            print('Game has no clues, moving on...')
            self.raw_clues = []
            return(False)
        return(True)
        
    def _parse_clues(self):
        """Create a Clue object for each clue in self.raw_clues"""
        if len(self.raw_clues) == 0:
            raise ValueError('Game has no clues yet _parse_clues was called?')
        self.clues = {
            'jeopardy_round':[],
            'double_jeopardy_round':[],
            'final_jeopardy_round':[]
        }
        for clue in self.raw_clues:
            if len(clue.contents) == 1:
                continue  # Skip clues that went unrevealed.
            for parent in clue.parents:
                if 'id' in parent.attrs:
                    round_ = parent['id']
                    break
            if round_ == 'final_jeopardy_round':
                self.clues[round_].append(FinalJeopardyClue(clue,self))
            elif round_ in ['jeopardy_round','double_jeopardy_round']:
                self.clues[round_].append(Clue(clue,self,round_))
            else:
                raise ValueError(f"Unknown round: {round_}")
            
    def _set_categories(self):
        """Create data structure of categories used in the game. 
        
        A list of categories used in each round is stored in a dictionary whose
        keys are the various round names. This structure is stored as 
        self.categories.
        """
        catsByRound = {
            'jeopardy_round':[],
            'double_jeopardy_round':[],
            'final_jeopardy_round':[]
        }
        for round_ in self.rounds:
            round_tag = self._parsed_html.body.find('div',attrs={'id':round_})
            gen = round_tag.find_all(
                'td',
                attrs={'class':'category_name'}
                ) # needs better name than 'gen'
            for category in gen:
                catsByRound[round_].append(category.text.lower())
        self.categories = catsByRound
        
    def __dict__(self):
        clues = []
        for round_ in self.clues.keys():
            for clue in self.clues[round_]:
                clues.append(clue.__dict__())
        dictionary = {
            'id_':self.id_,
            'title':self.title,
            'game_number':self.game_number,
            'weekday':self.weekday,
            'month':self.month,
            'day':self.day,
            'date':self.date,
            'year':self.year,
            'categories':self.categories,
            'clues':clues,
        }
        return(dictionary)

        
class Clue:
    """An object representing and containing data on a particular Jeopardy clue.
    
    This class and its associated methods compile and structure data on a 
    Jeopardy clue ib relation to the game object it is associated with. It is 
    called by Game._parse_clues but can be constructed individually if given a 
    proper bs4 tag object and a game object.
    
    Attributes:
        tag_obj       The bs4 tag object from parsing the j-archive data which
                        contains the associated data for the clue.
        game          The Game object this clue is associated with.
        round_        The round this clue is from.
        category      The name of the category for the clue.
        value         How much is won (or lost) given an (in)correct response.
                        This is usually the facial value of the clue but for
                        Daily Doubles (ie, daily_double == True), it is the 
                        amount the contestant wagered.
        row           The row the clue is found on, indexed from 1, not 0.
        column        The column the clue is found on, indexed from 1.
        daily_double  A boolean stating whether the clue was a Daily Double.
        text          The text of the clue.
        annotation    Any associated commentary with the clue other than the
                        correct response.
        target        The correct response.
        correct       Whether any participant answered the clue correctly.
        
    Methods:
        __init__      Initializes the Clue object and calls the various 
                        functions to set the attributes.
        
    """
    
    response_regex = re.compile(r"stuck', '(.*)<em")
    wasCorrect_regex = re.compile(r'<td class="(right|wrong)">(.*?)<\/td>')
    target_regex = re.compile(r"correct_response.+?>(.*)</em>")
    
    def __init__(
                self,
                bs4_tag=None,
                game=None,
                round_=None,
                load=False,
                **kwargs
                ):
        if game and load:
            self.loaded = True
            self.load(game,**kwargs)
            return(None)
        self.loaded = False
        self.tag_obj = bs4_tag
        self.game = game
        self.round_ = round_
        self._set_text()
        self._set_responses()
        if round_ != 'final_jeopardy_round':
            self._set_value()
            try:
                self.order_num = int(
                    self.tag_obj.find(
                        'td',
                        attrs={'class':'clue_order_number'}
                    ).text
                )
            except AttributeError:
                print('Unknown clue order in game {self.game.title}, {round_}')
                self.order_num = None
        
    def load(self,game,**kwargs):
        self.game = game
        self.round_ = kwargs['round_']
        self.text = kwargs['text']
        self.category = kwargs['category']
        self.row = kwargs['row']
        self.column = kwargs['column']
        self.target = kwargs['target']
        self.annotation = kwargs['annotation']
        if self.round_ != 'final_jeopardy_round':
            self.order_num = kwargs['order_num']
            self.daily_double = kwargs['daily_double']
            self.value = kwargs['value']
            self.correct = kwargs['correct']
            self.responses = kwargs['responses']
                
    def _set_value(self):
        """Set the dollar amount the clue was worth.
        
        Value is stored as an int in self.value and represents the dollar amount
        won or lost by a correct or incorrect response. It determines whether
        the clue is a daily double and sets self.daily_double as a boolean.
        """
        if self.round_ == 'final_jeopardy_round':
            return()
        val = self.tag_obj.find(
            'td',
            attrs={'class':'clue_value'}
        )
        if val == None:
            val = self.tag_obj.find(
                'td',
                attrs={'class':'clue_value_daily_double'}
            )
            if val == None:
                raise ValueError('Clue has no value?')
            else:
                self.daily_double = True
                self.value = val.text[5:]  # remove the 'DD: $' that precedes DD clue values.
        else:
            self.daily_double = False
            self.value = int(val.text.strip().strip('$'))
        
    def _set_text(self):
        """Set the text of the clue."""
        clue_tag = self.tag_obj.find('td',attrs={'class':'clue_text'})
        self.text = clue_tag.text
        self._set_category(clue_tag['id'])
        
    def _set_category(self,id_str):
        """Set the category of the clue and its coordinates on the board."""
        if id_str == 'clue_FJ':
            rnd = 'FJ'
        else:
            rnd,col,row = id_str.split('_')[1:]
        if (
                (rnd == 'J' and self.round_ != 'jeopardy_round') or 
                (rnd == 'DJ' and self.round_ != 'double_jeopardy_round') or
                (rnd == 'FJ' and self.round_ != 'final_jeopardy_round')
        ):
            print('Rounds do not match for %s,\n\
            defaulting to round used in coordinates.' % id_str)
            if rnd == 'J':
                self.round_ = 'jeopardy_round'
            elif rnd == 'DJ':
                self.round_ = 'double_jeopardy_round'
            elif rnd == 'FJ':
                self.round_ = 'final_jeopardy_round'
        cats = self.game.categories[self.round_]
        if rnd == 'FJ':
            self.row = None
            self.column = None
            self.category = cats[0]
            return()
        self.row = int(row)
        self.column = int(col)
        self.category = cats[self.column-1]
    
    def _set_responses(self):
        """Parse the response text and set various response variables."""
        annotation = None
        tag = self.tag_obj
        if self.round_ == 'final_jeopardy_round':
            for parent in self.tag_obj.parents:
                if parent.has_attr('id'):
                    if parent['id'] == 'final_jeopardy_round':
                        tag = parent
        for div in tag.find_all('div'):
            if div.has_attr('onmouseover'):
                annotation = div['onmouseover']
                break
        if annotation == None:
            raise ValueError('Clue has no response?')
        try:
            self.target = re.search(self.target_regex,annotation).group(1)
        except AttributeError:
            raise ValueError('Clue has no correct response?')
        self.annotation = re.search(self.response_regex,annotation).group(1)
        responses = re.findall(self.wasCorrect_regex,annotation)
        if responses == []:
            print('Unknown whether response was correct or not.\n' +
            'Here\'s diagnostic info:\n\tGame id: %s\n' +
            '\tDate: %s\n\tRound: %s\n\tClue coords (row,col): %s, %s' % (
                self.game.id_,
                self.game.date,
                self.round_,
                self.row,
                self.col
            ))
            self.correct = None
            return()
        if self.round_ == 'final_jeopardy_round':
            return()
        self.correct = None
        for response in responses:
            player = response[1]
            if response[0] == 'right':
                self.correct = True
            elif response[0] == 'wrong' and self.correct != True:
                self.correct = False
            else:
                self.correct = None
        self._clean_annotations()

    def _clean_annotations(self):
        annotation = self.annotation
        quotation = re.findall(r'\((.*?)\)',annotation)
        self.responses=[]
        for match in quotation:
            msplit = match.split(':')
            speaker = msplit[0]
            speech = ':'.join(msplit[1:])
            self.responses.append((speaker.strip(),speech.strip()))
    
    def __dict__(self):
        if self.round_ == 'final_jeopardy_round':
            dictionary = {
                'round_':self.round_,
                'text':self.text,
                'category':self.category,
                'row':self.row,
                'column':self.column,
                'target':self.target,
                'annotation':self.annotation,
            }
            return(dictionary)
        dictionary = {
            'round_':self.round_,
            'order_num':self.order_num,
            'daily_double':self.daily_double,
            'value':self.value,
            'text':self.text,
            'row':self.row,
            'column':self.column,
            'category':self.category,
            'target':self.target,
            'annotation':self.annotation,
            'correct':self.correct,
            'responses':self.responses,
        }
        return(dictionary)
        
class FinalJeopardyClue(Clue):
    
    fj_regex = re.compile(r'<td(?: class=\"(.*?)\"|.*?)>(.*?)</td>')
    
    def __init__(self,bs4_tag=None,game=None,load=False,**kwargs):
        super().__init__(bs4_tag,game,'final_jeopardy_round')
        matches = re.findall(self.fj_regex,self.annotation)
        count = 0
        fj_data = []
        response = []
        print(self.annotation)
        for match in matches:
            response.append(match)
            count+=1
            if count == 3:
                count = 0
                fj_data.append(response)
                response=[]
        self.contestants = [x[0][1] for x in fj_data]
        self.responses = [x[1][1] for x in fj_data]
        self.wagers = [x[2][1] for x in fj_data]
        correct = [x[0][0] for x in fj_data]
        self._correct_=[]
        for value in correct:
            if value == 'wrong':
                self._correct_.append(False)
            elif value == 'right':
                self._correct_.append(True)
            else:
                raise ValueError('Response neither right nor wrong?')
                
    def correct(self,contestant=None):
        c_type = type(contestant)
        if contestant == None:
            if True in self._correct_:
                return(True)
            else:
                return(False)
        elif c_type is int:
            return(self._correct_[contestant])
        elif c_type is str:
            i = self.contestants.index(contestant)
            return(self._correct_[i])
        elif c_type in [list,tuple]:
            out = []
            for item in contestant:
                out.append(self.correct(item))
            return(out)
        else:
            raise TypeError(f'Type {c_type.__name__} not supported')
            
    def load(self,**kwargs):
        super().load(kwargs)
        self.wagers = kwargs['wagers']
        self.responses = kwargs['responses']
        self.contestants = kwargs['contestants']
        self._correct_ = kwargs['correct']
        
    def __dict__(self):
        d = super().__dict__()
        d['correct'] = self._correct_
        d['wagers'] = self.wagers
        d['responses'] = self.responses
        d['contestants'] = self.contestants
        return(d)
