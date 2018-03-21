# Jeopardy! Archive Parser

A program to compile a database of Jeopardy questions and incorporate tools for linguistics analysis of those data. This program scrapes [J!-Archive](http://www.j-archive.com) and stores the data listed there in a custom data structure for easy manipulation and retrieval. Using the [Natural Language Toolkit](https://github.com/nltk/nltk)
it incorporates calls to Stanford's [CoreNLP](https://github.com/stanfordnlp/CoreNLP) and Princeton's [WordNet](https://wordnet.princeton.edu/) for syntactic and semantic analysis of the data. The Jeopardy! Archive Parser is distributed under the terms of the BSD 3-clause license.

## Getting Started

### Required software

This program is written in Python 3 and may run on Python 2.x but is not tested on it so it's best to use Python 3. It requires a number of Python modules, you can install them using pip:

```
pip install bs4 selenium nltk
```

It also relies upon [PhantomJS](https://github.com/ariya/phantomjs/) which can be downloaded [here](http://phantomjs.org/) or installed via your package manager.

For linguistic analysis using the ResponseParsing module, Stanford's CoreNLP and Princeton's WordNet programs are both required. CoreNLP can be downloaded from [here](https://stanfordnlp.github.io/CoreNLP/download.html) and WordNet can be downloaded from [here](https://wordnet.princeton.edu/wordnet/download/current-version/) or from your package manager.

To use CoreNLP parsing, the program must be running as a server application (full documentation is [here](https://stanfordnlp.github.io/CoreNLP/corenlp-server.html). To do so, navigate to the directory where the CoreNLP .jar file is located and run:

```java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000```

This will start the server on port 9000. The Jeopardy! Archive Parser looks for this application on port 9000 by default, so if you change the port here (or use an instance running on a remote server), you will need to supply the url to JCorpus.Scraper.&#95;&#95;init&#95;&#95;() which defaults to "http://<span></span>localhost:9000".

### Installation

The Jeopardy! Archive Parser can be downloaded by cloning the repository:

```
git clone https://github.com/chrisbrickhouse/jeopardy.git
```

### Examples

To use the program, start a python shell and import the JCorpus module and initialize it:

```python
import JCorpus
scraper = JCorpus.Scraper()
```

To scrape pages, use the ```scrape``` method to indicate the page id (or range of ids) on the jeopardy archive:

```python
scraper.scrape(5)  # Scrapes the J!-archive page whose pageid is 5

scraper.scrape(5,10)  # Scrape pageids 5 through 10 (inclusive)

scraper.scrape(1,10,2)  # Scrape odd numbered page ids from 1 to 10
```

To load data from a JSON file, use the Scraper.load() method:
```python
# The fname keyword argument in save() and load() defaults to JeopardyData.json
scraper.load(fname='JeopardyData.json')

# The method overwrites scraper.games by default. To keep the data already
#   scraped or loaded, set the append keyword argument to True
scraper.load(fname='JeopardyData.json',append=True)
```

Game objects are stored in the list ```scraper.games``` and game and clue info can be accessed from there:

```python
# Print the values for all clues
for game in scraper.games:
    for round_ in game.clues:
        for clue in game.clues[round_]:
            print(clue.value)

# Print only clues from games in October
for game in scraper.games:
    if game.month == 'October':
        for round_ in game.clues:
            for clue in game.clues[round_]:
                print(clue.text)
```

Parsing is not yet fully implemented (as of v0.5.0).

## Scraping
Code dealing with the scraping of data from the jeopardy archive website is located in the file [```JCorpus.py```](JCorpus.py). It has one class [```JCorpus```](https://github.com/chrisbrickhouse/jeopardy/blob/dev/JCorpus.py#L14-L167) which contains all attributes and methods of the web scraper.

<h3 id="JCorpus-Scraper-init" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/JCorpus.py#L31-L50">JCorpus.Scraper._&#95;init&#95;_(*self, default_wait = 2, url = 'http://localhost:9000', conll = False*)</a></h3>
This object contains methods for automatically collecting, storing, and analyzing data from the Jeopardy! Archive.

It optionally takes a wait time in seconds to override the default of 2 seconds. Out of courtesy for the Jeopardy! Archive's servers, users cannot provide a wait time of less than one second; if a default_wait of less than 1 second is provided, it raises a ValueError. Two seconds is fine for interactive use and small jobs, but if used in a script or on long ranges of pages, it is recommended that a wait of at least 5 seconds be used to minimize traffic and any potential effects on service.

```python
scraper = JCorpus.Scraper()
scraper = JCorpus.Scraper(5) # Will wait 5 seconds between website requests
scraper = JCorpus.Scraper(0.6) # Raises ValueError
```

It optionally takes a url to point to the CoreNLP server, and defaults to the local machine on port 9000. If CoreNLP is run on the local machine but a different port, the full url must still be supplied. If it is run on a remote server, the url must be supplied in full.

```python
scraper = JCorpus.Scraper()  # Defaults to port 9000
scraper = JCorpus.Scraper(url = 'http://localhost:22')  # Use port 22 instead
scraper = JCorpus.Scraper(url = 'http://www.example.com/nlp')  # Remote server
```

It optionally takes a boolean keyword argument, conll, which defaults to False. If set to True, once each game is loaded, the clue text and response text are dependency parsed and the output is saved as clue attributes Clue.text_conll and Clue.responses_conll which can be printed to view the CoNLL output. Setting this value to True will likely increase the time it takes to finish scraping a range of pages, with each game taking about 5 seconds to fully parse. It will print a warning to the console reminding users of this. There is currently no way to get conll outputs for clues once scraped except by manually inputting them to CoreNLP.

```python
scraper = JCorpus.Scraper()  # Will not produce CoNLL output by default
scraper = JCorpus.Scraper(conll = True)  # Will dependency parse clues as scraped
```

The length of an instance is equal to the number of games it has scraped:
```Python
len(scraper) == len(scraper.games)
```

The instance as a string is a string of the game number and date for all the games it has scraped separated by newlines. This is useful for getting an overview of the games in the archive, especially in a print statement:
```Python
str(scraper)  # Newline separated string of game titles in scraper.games
print(str(scraper))  # More readable
```

<h3 id="JCorpus-Scraper-scrape" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/JCorpus.py#L52-L123">JCorpus.Scraper.scrape(*self, start, stop = None, step = 1, wait = None, random = False*)</a></h3>
The most basic use of this method follows the syntax of the python built-in function ```range()```:

```python
scraper.scrape(1) # Scrapes the archive page with page-id 1
scraper.scrape(5,10) # Scrapes from 5 <= page id <= 10
scraper.scrape(2,5,2) # Has a step of 2 and so scrapes every second page:
                      #   [2,4] not [2,3,4,5]
```

The step parameter is passed directly to ```range``` so the peculiarities of its method also apply here:

```python
list(range(2,5,2))    # == [2,4]
scraper.scrape(2,5,2) # scrapes page ids 2 and 4
list(range(2,6,2))    # == [2,4]
scraper.scrape(2,6,2) # scrapes page ids 2 and 4
list(range(2,4,2))    # == [2] != [2,4]
scraper.scrape(2,4,2) # ONLY scrapes page id 2
```

It optionally takes a wait time to override the initialized default. The main use case is for requests of a different type than you planned on using: a one-off short run among a lot of long ones, or a long run in interactive mode when using mostly short calls for example.

```python
scraper.scrape(1,3,wait = 4) # Will wait 4 seconds between each request.
```

It optionally takes a parameter, ```random```, which, if set to ```True```, will select a random page for each interval in the list of boundaries ```range(start, stop, step)``` and so has no effect if ```step=1```.

```python
import random
list(range(1,40,10)) == [1,11,21,31]

# Choose a random page id in the intervals bounded by range(1,40,10)
scraper.scrape(1,40,10,random=True)

# This is equivalent to:
#   Scrape random page id between 1 and 10 inclusive
i = random.randint(1,10)
scraper.scrape(i)
#   Scrape random page id between 11 and 20 inclusive
i = random.randint(11,20)
scraper.scrape(i)
#   Scrape random page id between 21 and 30 inclusive
i = random.randint(21,30)
scraper.scrape(i)
#   It will not select a page in [31,40] because of how range() works, see above
```

<h4> On sampling</h4>
Page ids are not chronological for episodes of jeopardy but are a chronological numbering of when the game was added to the archive. That is, page id 1 is the first game added to the archive, and page id 4763 is the 4763rd game added to the archive. The first game added to the archive is the first game of the 21st season. All episodes in the archive from prior to season 21 break up the chronological page ids of those afterwards. <!--(**To Do:** see how the random argument affects sampling distribution)-->

<h3 id="JCorpus-Scraper-save" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/JCorpus.py#L125-L138">JCorpus.Scraper.save(*self, fname = 'JeopardyData.json', sub_files = False*)</a></h3>
This function outputs a JSON file with all public attributes of the Game, Clue, and FinalJeopardyClue instances in ```self.games```.

It optionally takes the path with file name (or just filename as is the default) as an argument to tell the function where to save the file.

It optionally takes a boolean keyword argument, sub_files, which defaults to false. When false, it outputs all data into one file named ```fname```. When true it creates a JSON file for each year, named 'JeopardyGames_YEAR.json'. If a given year does not have a game scraped, no file is created.

```Python
scraper.save()  # Writes data to JeopardyData.json
scraper.save(fname='JData.json')  # Writes data to JData.json
scraper.save(sub_files = True)  # Creates a file for each year with >1 game.
```

**Note, this method may not up to date in the most recent development versions. An update to this may be a breaking change.**

<h3 id="JCorpus-Scraper-load" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/JCorpus.py#L140-L146">JCorpus.Scraper.load(*self, fname = 'JeopardyData.json', append = False*)</a></h3>
Loads the data from a save file into memory so it can be manipulated with the API.

It takes an optional argument ```fname``` which is the path and filename of the file to load.

It optionally takes a boolean keyword argument, append, which defaults to false. When false it empties scraper.games and replaces it with the data from the file. When true it keeps the games in scraper.games and adds the data in the file to it. Games which were loaded can be distinguished from those scraped by the game.loaded attribute.

```python
scraper.load()  # Reads ./JeopardyData.json
scraper.load('JData.json')  # Reads ./JData.json
scraper.load(append=True)  # Reads ./JeopardyData.json and adds it to scraper.games
```

## Accessing and manipulating data
The maximal unit of data is a game represented by a [```Game.Game()```](https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L9-L260) instance. It contains attributes relating to information on the game itself, as well as serving as a container for data on each clue that appeared in the game which are stored as ```Game.Clue()``` objects and ```Game.FinalJeopardyClue()``` objects in a dictionary of lists, ```Game.clues```, with round names as keys.

### Game.Game() Public Attributes
* ```id_``` The id number used by j-archive to index the game.
* ```title``` The title of the game, including game number and date.
* ```game_number``` The number of the game in sequence of Jeopardy! games.
* ```date``` The air date in (D)D Mon YYYY format.
* ```day``` The day of the month the game aired.
* ```month``` The month the game aired.
* ```year``` The year the game aired.
* ```categories``` A dictionary of lists, with round names as keys and a list of category names in that round as the values.
* ```clues``` A dictionary of lists, with round names as keys and a list of clues in that round as values.
* ```loaded``` Boolean where True means the game was read from file.
* ```raw_clues``` (Only available if loaded == False) The bs4 tags for the clues.


<h3 id="Game-Game-init" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L45-L86">Game.Game._\_init\__(*self, page_source=None, url=None, load=False,* \*\**kwargs*)</a></h3>
A game object is typically initialized by a scraper object and so usage of the init function is rarely useful for users. If you have the source html of a j! archivepage, or would like to create an instance using your own custom scraper, the html source should be the first argument:

```python
url = 'http://www.j-archive.com/showgame.php?game_id=1'
try:
  # Python 3
  import urllib.request
  with urllib.request.urlopen(url) as response:
    html = response.read()
except ImportError:
  # Python 2
  import urllib2
  response = urllib2.urlopen(url)
  html = response.read()

game = Game.Game.__init__(html,url) # Game instance.
```

The ```load``` keyword argument is used by ```Scraper.load()``` to indicate that the game was read from file rather than scraped. This is important because certain attributes and methods are only defined when ```Game.loaded``` is False.

<h3 id="Game-Game-score" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L45-L86">Game.Game.score_graph(*self, plt=None*)</a></h3>
If called with a matplotlib or pyplot instance as an argument, it will plot a graph of the score by clue number:
```Python
import matplotlib.pyplot as plt

game.score_graph(plt)
```

If called without argument it returns the score data as a dictionary with contestant names as keys and a list of scores over time for that contestant as the value. It can be used to create your own plots:
```Python
score_data = game.score_graph()
for contestant in score_data:
  score = score_data[contestant]
  plt.plot(list(range(len(score))), score)
plt.show()
```

### Game.Clue() Public Attributes
* ```game``` The Game.Game() instance associated with this clue.
* ```round_``` The round this clue is from: ```['jeopardy_round','double_jeopardy_round','final_jeopardy_round']```
* ```category``` The category the clue is from.
* ```daily_double``` Boolean, True if the clue was a daily double, else False.
* ```value``` How much the clue was worth, how much was wagered if ```daily_double``` is True.
* ```text``` The text of the clue.
* ```responses``` A list of tuples of speaker and speech pairs. If none were in the archive, it is an empty list.
* ```target``` The correct response.
* ```order_num``` Integer representing the place in the order of selected clues.
* ```row``` and ```column``` The coordinates of the clue on the board.
* ```text_conll``` The CoNLL string for the clue text. None if not parsed yet.
* ```responses_conll``` The CoNLL strings for responses. None if not parsed yet.
* ```loaded``` Boolean, True if loaded from data, else False.
* ```tag_obj``` (Only available if loaded is False) The bs4 tag object for the clue.

#### Game.FinalJeopardyClue() extension
* ```contestants``` A list of the first names of each contestant in Final Jeopardy (in some games, not all contestants participated because of scores and rules). The index of a contestant here is the index for their data in ```wagers```.
* ```wagers``` A list of the amount each contestant wagered.

<h3 id="Game-Clue-init" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L45-L86">Game.Clue.__init__(*self, bs4_tag=None, game=None, load=False,*\*\**kwargs*)</a></h3>
Clue instances are rarely if ever user generated. Rather they are [created automatically](https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L225) for all clues in a game [when a ```Game.Game()``` instance is created](https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L77). For more information [see the code](https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L305-L334).

<h3 id="Game-Clue-correct" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L45-L86">Game.Clue.correct(*self, method = 'any'*)</a></h3>
This method returns information regarding whether the clue was answered correctly or not. It can be called with or without an optional parameter which determines how the function determines what to return.
```Python
game = scraper.games[0]
clue = game.clues['jeopardy_round'][0]

# The following return True if any response to the clue was correct.
clue.correct()             # This is the default operation.
clue.correct('any')        # Full name.
clue.correct('a')          # Abbreviation.
clue.correct(method='any') # Keyword explicit.
# The following return True if no response to the clue was correct.
clue.correct('any-false')
clue.correct('af')

#The following return True only if all responses were incorrect.
clue.correct('no-correct')
clue.correct('nc')

# The following return how many people buzzed in to give an answer.
clue.correct('length')
clue.correct('l')

# The following does not return a boolean, rather a list of tuples with
#   contestant names as the first item and boolean value of the response as
#   the second item.
clue.correct('all')
```

<h3 id="Game-FJClue" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L620-L741">Game.FinalJeopardyClue.&#95;&#95;init&#95;&#95;(*self,bs4_tag=None,game=None,load=False,kwargs*)</a></h3>
This is an extension of the Game.Clue() class for the specifics of Final Jeopardy! clues, and as such has similar specifics. It is rarely, if ever, useful to call, being called automatically during scraping. It has one public method.

<h3 id="Game-FJClue-correct" style="%font-family: monospace;"><a href="https://github.com/chrisbrickhouse/jeopardy/blob/dev/Game.py#L620-L741">Game.FinalJeopardyClue.correct(*self,method='any', contestant=None*)</a></h3>
By default, it functions the same as Game.Clue.correct() and extends the functionality by allowing the user to specify a contestant to check if their response was correct or not.

## Authors

* **Christian Brickhouse** - *Initial development* - [GitHub](https://github.com/chrisbrickhouse)

## License

This project is licensed under the terms of the BSD 3-clause license - see [LICENSE](LICENSE) for details
