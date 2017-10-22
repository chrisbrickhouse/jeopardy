__version__ = '0.4.0-dev'
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
    
    def __init__(self,page_source,url):
        """Initialize important meta-data on the game."""
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
        self._set_raw_clues()
        self._set_categories()
        self._parse_clues()
        
    def _set_raw_clues(self):
        """Add all bs4 Tag objects for clues to a list, self.raw_clues"""
        self.raw_clues = self._parsed_html.body.find_all(
            'td',
            attrs={'class':'clue'}
        )
        if self.raw_clues == None or len(self.raw_clues) == 0:
            raise ValueError('This game has no clues?')
        return()
        
    def _parse_clues(self):
        """Create a Clue object for each clue in self.raw_clues"""
        if len(self.raw_clues) == 0:
            raise ValueError('This game has no clues?')
        clues = []
        for clue in self.raw_clues:
            if len(clue.contents) == 1:
                continue  # Skip clues that went unrevealed.
            clues.append(Clue(clue,self))
        j = [x for x in clues if x.round_ == 'jeopardy_round']
        dj = [x for x in clues if x.round_ == 'double_jeopardy_round']
        fj = [x for x in clues if x.round_ == 'final_jeopardy_round']
        self.clues = {
            'jeopardy_round':j,
            'double_jeopardy_round':dj,
            'final_jeopardy_round':fj
        }
            
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
    
    def __init__(self,bs4_tag,game):
        self.tag_obj = bs4_tag
        self.game = game
        self._set_round()
        try:
            self.order_num = int(
                self.tag_obj.find(
                    'td',
                    attrs={'class':'clue_order_number'}
                ).text
            )
        except AttributeError:
            if self.round_ != 'final_jeopardy_round':
                print('Unknown clue order in game %s, %s'%(self.game.title,self.round_))
                self.order_num = None
        self._set_value()
        self._set_text()
        self._set_responses()
        
    def _set_round(self):
        """Set the round the clue comes from.
        
        Sets self.round_ based upon the first tag up the tree which has an 'id'
        attribute. This may not always work but is cross checked again later in
        the method self._set_category below.
        """
        for parent in self.tag_obj.parents:
            if 'id' in parent.attrs:
                self.round_ = parent['id']
                break
                
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
        if self.round_ == 'final_jeopardy_round':
            pass  # Needs to be handled separately.
            return()  # The rest is only for non-final clues.
        quotation = re.findall(r'\((.*?)\)',annotation)
        self.responses=[]
        for match in quotation:
            speaker,speech = match.split(':')
            self.responses.append((speaker.strip(),speech.strip()))

