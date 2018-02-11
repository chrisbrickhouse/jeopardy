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
        score_graph If given a matplotlib instance, will plot each player's
                      score by clue, otherwise returns a the data as dictionary
                      where keys are contestant names and values are lists of
                      the data used to plot.
    """

    title_regex = re.compile(r'#(\d+).*?([a-zA-Z]+), ([a-zA-Z]+) (\d+), (\d+)')
    rounds = ['jeopardy_round','double_jeopardy_round','final_jeopardy_round']

    def __init__(self,
            page_source = None,
            url = None,
            load = False,
            **kwargs
        ):
        """Initialize important meta-data on the game."""
        if load:
            self.loaded = True
            self._load(**kwargs)
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
        self._set_contestants()
        self.score_data = None
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

    def score_graph(self, plt=None):
        if self.score_data == None:
            self.score_data = self._make_score_data()
        if plt == None:
            return(self.score_data)
        else:
            for cont in self.contestants:
                plt.plot(cont.score_series)
            plt.show()
            return()

    def _make_score_data(self):
        max_i = 0
        for clue in self.clues['jeopardy_round']:
            if clue.order_num == None:
                continue
            i = clue.order_num
            resp = clue.correct('all')
            for contestant in self.contestants:
                contestant._update_series(clue, resp, i)
            if i > max_i:
                max_i = i
        offset = max_i
        for clue in self.clues['double_jeopardy_round']:
            if clue.order_num == None:
                continue
            i = clue.order_num + offset
            resp = clue.correct('all')
            for contestant in self.contestants:
                contestant._update_series(clue, resp, i)
            if i > max_i:
                max_i = i
        for clue in self.clues['final_jeopardy_round']:
            i = max_i + 1
            resp = clue.correct('all')
            for contestant in self.contestants:
                contestant._update_series(clue, resp, i, fj=True)
                contestant.score_series = contestant.score_series[:max_i+2]
        for cont in self.contestants:
            cont._make_series()
        ret_dict = {}
        for cont in self.contestants:
            series = cont.score_series
            ret_dict[cont.name] = series
        return(ret_dict)

    def _load(self,**kwargs):
        """Set attributes based on given data.

        Called by Scraper.load() via Game.__init__(), it takes in JSON formatted
          data and sets the public attributes. Private attributes (page source
          and bs4 trees notably) are not loaded as they are not saved.
        """
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
            if round_ == 'final_jeopardy_round':
                self.clues[round_].append(FinalJeopardyClue(
                                                            game=self,
                                                            load=True,
                                                            **clue
                                                            ))
            else:
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

    def _set_contestants(self):
        """Return a list of Contestant objects."""
        self.contestants = []
        raw_contestants = self._parsed_html.body.find_all(
            'p',
            attrs={'class':'contestants'}
        )
        for cont in raw_contestants:
            flavor = cont.text
            name = cont.a.text
            link = cont.a['href']
            self.contestants.append(Contestant(name,link,flavor))

    def __dict__(self):
        """Return a dictionary of public attributes"""
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
        loaded        Boolean that is True if instance was loaded from JSON and
                        False otherwise.
        order_num     An integer representing the clue number, that is, 1 is the
                        first revealed clue, 10 is the tenth revealed clue, etc.
                        Numbers are only for the current round.
        *correct     (Made method in 0.6.0)

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
            self._load(game,**kwargs)
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
                print(f'Unknown clue order in game {self.game.title}, {round_}')
                self.order_num = None

    def correct(self,method='any'):
        """Return, among other options, whether the clue was answered correctly.

        By default, returns True if any response to the clue was correct.
          Specifying a different method argument changes that functionality and
          can provide whether there were any wrong responses, the truth value of
          all given responses, and the number of responses among others, see
          list of options.

        Arguments:
            method      How the function should determine what value to return,
                          take one of the following:

                        a   any             Return True if any response was
                                              correct.
                        af  any-false       Return True if any response was not
                                              correct. Opposite of 'any'.
                        nc  no-correct      Return True iff no responses were
                                              correct.
                        fr  first-response  Return True if the first response
                                              was correct, False if incorrect
                                              or not answered.
                            all             Return a list of tuples with
                                              contestant names as the first
                                              tuple value and the truth values
                                              for the response as the second.
                                              True is a correct response and
                                              False is not a correct response.
                        l   length          Return the number of responses.
        """
        truth_list = [x[1] for x in self._correct_]
        if method == 'any' or method == 'a':
            if True in truth_list:
                return(True)
            else:
                return(False)
        elif method == 'any-false' or method == 'af':
            if False in truth_list:
                return(True)
            else:
                return(False)
        elif method == 'no-correct' or method == 'nc':
            if True not in truth_list:
                return(True)
            else:
                return(False)
        elif method == 'first-response' or method == 'fr':
            return(self._correct_[0][1])
        elif method == 'all':
            return(self._correct_)
        elif method == 'length' or method == 'l':
            return(len(self._correct_))
        else:
            raise ValueError(f"Unknown method argument {method}")

    def _load(self,game,**kwargs):
        """Set public attributes from JSON input"""
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
            self._correct_ = kwargs['correct']
            self.responses = kwargs['responses']

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
        if self.round_ == 'final_jeopardy_round':
            return()
        self._correct_ = []
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
            return()
        for response in responses:
            player = response[1]
            if response[0] == 'right':
                self._correct_.append((player,True))
            elif response[0] == 'wrong':
                self._correct_.append((player,False))
        quotation = re.findall(r'\((.*?)\)',annotation)
        self.responses=[]
        for match in quotation:
            msplit = match.split(':')
            speaker = msplit[0]
            speech = ':'.join(msplit[1:])
            self.responses.append((speaker.strip(),speech.strip()))

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
                # remove the 'DD: $' that precedes DD values and any commas.
                self.value = int(val.text[5:].replace(',',''))
        else:
            self.daily_double = False
            self.value = int(val.text.strip().strip('$'))

    def __str__(self):
        """Return the clue text."""
        return(self.text)

    def __dict__(self):
        """Return a dictionary of public attributes."""
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
            'correct':self._correct_,
            'responses':self.responses,
        }
        return(dictionary)

class FinalJeopardyClue(Clue):
    """An extension of the Clue class to handle Final Jeopardy data.

    Attributes:
      Defined here:
        wagers      A list of the amount each contestant wagered.
        contestants A list of the first names of each contestant who
                      participated in Final Jeopardy.
        responses   A list of the responses each contestant gave.

      Inhereted from Clue (see documentation there):
        category
        text
        annotation
        target
        round_
        row
        column
    """

    fj_regex = re.compile(r'<td(?: class=\"(.*?)\"|.*?)>(.*?)</td>')

    def __init__(self,bs4_tag=None,game=None,load=False,**kwargs):
        if game and load:
            self.loaded = True
            self._load(game,kwargs)
            return(None)
        self.loaded = False
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
        print(self.contestants)
        print(self.responses)
        print(self.wagers)
        print(correct)
        correctval = []
        for value in correct:
            if value == 'wrong':
                correctval.append(False)
            elif value == 'right':
                correctval.append(True)
            else:
                raise ValueError('Response neither right nor wrong?')
        print(correctval)
        print(repr(fj_data))
        self._correct_ = []
        for i in range(len(self.contestants)):
            cont = self.contestants[i]
            val = self.wagers[i]
            tv = correctval[i]
            self._correct_.append(
                (
                    cont,
                    tv,
                    val
                )
            )
        print(self._correct_)

    def correct(self,method='any',contestant=None):
        """Extends Clue.correct() to retrieve particular contestant responses.

        By default, the function returns whether any contestant responded
            correctly. If no contestant is specified, the method parameter is
            passed to Clue.correct() and that value returned, if a contestant
            is specified, method is meaningless and disregarded.
        If contestant is an integer, it is treated as an index and the boolean
            at that location in FJC._correct_ is returned. If it is a string
            it is treated as a contestant's name and the boolean for that
            contestant's response is returned. If it is a list or tuple, each
            element is passed individually to FJC.clue to be evaluated
            recursively and a list of the returns is returned.
        """
        c_type = type(contestant)
        if contestant == None:
            if method == 'all':
                return(self._correct_)
            return(super().correct(method))
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

    def _load(self,game,**kwargs):
        """Set public attributes from JSON input."""
        super()._load(game,kwargs)
        self.wagers = kwargs['wagers']
        self.responses = kwargs['responses']
        self.contestants = kwargs['contestants']
        self._correct_ = kwargs['correct']

    def __dict__(self):
        """Return dictionary of public attributes."""
        d = super().__dict__()
        d['correct'] = self._correct_
        d['wagers'] = self.wagers
        d['responses'] = self.responses
        d['contestants'] = self.contestants
        return(d)

class Contestant():
    def __init__(self, name, link, flavor=''):
        self.name = name
        self.first_name = name.split(" ")[0]
        self.link = link
        self.flavor = flavor
        self.score_series = [0]*70

    def _update_series(self, clue, resp, i, fj = False):
        guessers = [x[0] for x in resp]
        if fj == True:
            print(resp)
            print(guessers)
        if self.first_name in guessers:
            tv = [x[1] for x in resp if x[0] == self.first_name][0]
            if fj == True:
                val = [x[2] for x in resp if x[0] == self.first_name][0]
                val = int(val.strip()[1:].replace(',',''))
            else:
                val = clue.value
            if tv == False:
                val = -1 * val
            try:
                self.score_series[i] = val
            except:
                print(i)
                exit()

    def _make_series(self):
        for i in range(len(self.score_series)):
            if i == 0:
                continue
            self.score_series[i] = self.score_series[i-1] + \
                self.score_series[i]
