# Jeopardy! Archive Parser

A program to compile a database of Jeopardy questions and incorporate tools for linguistics analysis of those data. This program scrapes [J!-Archive](http://www.j-archive.com) and stores teh data listed there in a custom data structure for easy manipulation and retrieval. Using the [Natural Language Toolkit](https://github.com/nltk/nltk) 
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

This will start the server on port 9000. The Jeopardy! Archive Parser looks for this application on port 9000 by default, so if you change the port here, it will also need to be changed in the source files.

### Installation

The Jeopardy! Archive Parser can be downloaded by cloning the repository:

```
git clone https://github.com/chrisbrickhouse/jeopardy.git
```

## Authors

* **Christian Brickhouse** - *Initial development* - [GitHub](https://github.com/chrisbrickhouse)

## License

This project is licensed under the terms of the BSD 3-clause license - see [LICENSE.md](LICENSE.md) for details
