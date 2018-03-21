__version__ = '0.6.0-dev'
__author__ = 'Christian Brickhouse'

import time
import json
from random import randint  # For testing purposes.

from selenium import webdriver

import Game
import ResponseParsing


class Scraper():
    """A wraper for gathering J!-archive data and calling parsers on it.

    This object contains methods for automatically collecting, storing, and
      analyzing data from the Jeopardy! Archive. It scrapes the various pages,
      creates Game and Clue objects to store their data, and allows access to
      those data in a convenient way. The data can be exported and imported
      using JSON, and analyzed using the JeopardyParser.

    Attributes:
        games          A list of Game instances from scraping runs.
        browser        A selenium instance used to request webpages.
        jparse         An instance of ResponseParsing.JeopardyParser() for easy
                           parsing of data within the module.
        default_wait   Time (in seconds) that the scraper will wait between
                           requests so as not to overload the server.
    """
    def __init__(
            self,
            default_wait = 2,
            url = 'http://localhost:9000',
            conll = False,
        ):
        """Initialize the webscraper with a default wait (in seconds).

        The method creates a browser object used to access the various web
          pages, a list to store game objects in, a wrapper for the parsers,
          and a default wait time between requests. Default wait time is
          2 seconds and as a courtesy to the website must be at least 1 second.
          This value can be overridden for a specific scrape call, see
          Scrape.scrape() for documentation.

        Raises:
            ValueError if default wait is less than 1 second.
        """
        self.games = []
        self.browser = webdriver.PhantomJS()
        if default_wait < 1:
            raise ValueError('Wait must be at least 1 second as a courtesy.')
        else:
            self.default_wait = default_wait
        self.jparse = ResponseParsing.JeopardyParser(url)
        self.conll = conll
        if conll:
            # conll defaults to False so if someone is using this argument
            # they likely know what they're doing, but if not, try to protect
            # the user from themselves.
            print('INFO: Argument \'conll\' is set to True.')
            print('      The scraper will attempt to parse every sentence in')
            print('      the corpus which will increase times and cpu usage.')

    def scrape(
            self,
            start,
            stop = None,
            step = 1,
            wait = None,
            random = False,
        ):
        """Scrape pages of given game ids and create Game and Clue instances.

        This method takes game ids as its input and requests the page(s),
          passing the html on to Game.__init__ and storing the associated
          instance in Scraper.games.
        Arguments start and stop are an inclusive range, such that
          start <= i <= stop.

        Arguments:
            start   An int representing the game id for the scraper to start its
                      run at. If it is the only argument provided, the scraper
                      only scrapes that page and no others.
            stop    An int representing the game id for the scraper to stop at,
                      unless it is beyond the length of the jeopardy archive in
                      which case the scraper runs until it reaches the end of
                      the archive.
            step    An int representing the increment for getting from start to
                      stop. See the documentation for range() in the Python base
                      library for more details as it is passed directly to
                      range().
            wait    An int to override the default_wait time for this run. It is
                      incredibly rude to not throttle your requests and may be
                      seen as malicious activity, so while this may be set to
                      zero, be responsible and do not do so for long runs or
                      without a good reason.
            random  A boolean. If True, a random page id is chosen from within
                      the bounds of the step increment (thus it is useless if
                      step == 1). As an example:
                        scraper(start=1,stop=100,step=10,random=True)
                      would choose a random page such that 1 <= page_id <= 10,
                      then a random page 10 < page_id <= 20, then one between
                      21 and 30, 31 and 40, and so on. It is useful for sampling
                      purposes (though page ids do not map onto dates
                      particullarly well).

        Raises:
            ValueError if stop value is less than start.
        """
        request_time = 0
        conll = self.conll
        if type(wait) is not int:
            wait = self.default_wait
        if stop == None:
            stop = start + 1
        elif stop < start:
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
                #print('Continuing')
            self.browser.get(url)
            request_time = time.time()
            html = self.browser.page_source
            if i > 5500:
                if self._checkEnd(html,i):
                    break
            game = Game.Game(html,url)
            if conll:
                game.conll(self.jparse.dep_parser)
            self.games.append(game)

    def save(self,fname='JeopardyData.json',sub_files=False):
        """Output the data to a JSON file.

        Saves all public attributes of Game, Clue, and FinalJeopardyClue
          instances. As they are private attributes, page source and bs4 tag
          objects are not saved (page source for size reduction and bs4 tag due
          to JSON limitations).
        """
        serial = []
        for game in self.games:
            serial.append(game.__dict__())
        if sub_files:
            years_dict = self._games_by_year(serial)
            for y in years_dict:
                out = json.dumps(years_dict[y])
                fname = 'JeopardyGames_'+y+'.json'
                with open(fname,'w') as f:
                    f.write(out)
            return()
        json_output = json.dumps(serial)
        with open(fname,'w') as f:
            f.write(json_output)

    def load(self,fname='JeopardyData.json',append=False):
        """Read data in from a JSON file."""
        with open(fname,'r') as f:
            json_input = json.load(f)
        if not append:
            self.games = []
        for game in json_input:
            self.games.append(Game.Game(load=True,**game))

    def _games_by_year(self,l):
        d = {}
        for game in l:
            y = game['year']
            if y not in d:
                d[y] = []
            d[y].append(game)
        return(d)

    def _checkEnd(self, source, id_):
        """Check to see if the requested page throws an error."""
        error_string = 'ERROR: No game %s in database.'%str(id_)
        if error_string in source:
            return(True)
        else:
            return(False)

    def __len__(self):
        """Return the number of games it has scraped."""
        l = len(self.games)
        return(l)

    def __str__(self):
        """Return a newline seperated string of game titles it has scraped."""
        text = []
        for game in self.games:
            text.append(game.title)
        text = '\n'.join(text)
        return(text)
