__version__ = '0.3.0-dev'
__author__ = 'Christian Brickhouse'

from nltk.corpus import wordnet
from nltk.tag.stanford import CoreNLPNERTagger
from nltk.parse.corenlp import CoreNLPDependencyParser as DepParser
from nltk.parse.corenlp import CoreNLPParser

class JeopardyParser():
    def __init__(self,url='http://localhost:9000', encoding='utf8'):
        self.NERT = CoreNLPNERTagger(url=url)
        self.Parser = CoreNLPParser(url=url,encoding=encoding)
        
    def tag(self,sentence):
        sentence = clean_sentence(sentence)
        sentence = sentence.split()
        sentence = self.NERT.tag(sentence)
        return(sentence)
        
    def lexname(self,word,index=0):
        synset = wordnet.synsets(word)
        lex = synset[index].lexname()
        return(lex)
        
    def parse(self,sentence):
        sentence = clean_sentence(sentence)
        parse, = self.Parser.raw_parse(sentence)
        return(parse)
        
    def clean_sentence(self,sentence):
        s = sentence.replace("\\'","'")
        return(s)
        

def check_syntax(tree):
    if tree[0].label() not in ['SBARQ','WHNP']:
        print('Malformed question',tree[0].label())
        return(False)
    elif tree[0].label() in ['SBARQ','WHNP']:
        return(True)
