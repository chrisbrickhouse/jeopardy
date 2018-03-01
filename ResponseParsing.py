__version__ = '0.6.0-dev'
__author__ = 'Christian Brickhouse'

from nltk.corpus import wordnet
from nltk.tag.stanford import CoreNLPNERTagger
from nltk.parse.corenlp import CoreNLPDependencyParser as DepParser
from nltk.parse.corenlp import CoreNLPParser

class JeopardyParser():
    def __init__(self,url='http://localhost:9000', encoding='utf8'):
        """Start the parsers to make sure they're running before calling.
        
        CoreNLP runs by default on port 9000, but if an external server is used
          or a different port is selected when started, the url will need to be
          explicitly passed.
        """
        self.NERT = CoreNLPNERTagger(url=url)
        self.Parser = CoreNLPParser(url=url,encoding=encoding)
        
    def tag(self,sentence):
        """Return the sentence after tagging named entities."""
        sentence = self.clean_sentence(sentence)
        sentence = sentence.split()
        sentence = self.NERT.tag(sentence)
        return(sentence)
        
    def lexname(self,word,index=0):
        """Return the lexname entry for a word in WordNet."""
        synset = wordnet.synsets(word)
        lex = synset[index].lexname()
        return(lex)
        
    def parse(self,sentence):
        """Return the syntactic Tree object for a sentence."""
        sentence = self.clean_sentence(sentence)
        parse, = self.Parser.raw_parse(sentence)
        return(parse)
        
    def clean_sentence(self,sentence):
        """Remove backslash apostrophes from the data."""
        s = sentence.replace("\\'","'")
        return(s)
        

    def check_syntax(self,tree,labels=['SBARQ','WHNP']):
        """Return True if sentence type is not on provided in labels."""
        if tree[0].label() not in labels:
            print('Malformed question',tree[0].label())
            return(False)
        elif tree[0].label() in labels:
            return(True)
