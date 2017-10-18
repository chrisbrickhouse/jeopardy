import re
from selenium import webdriver
from bs4 import BeautifulSoup


url = 'http://www.j-archive.com/showgame.php?game_id=1'
browser = webdriver.PhantomJS()
browser.get(url)
page = browser.page_source
parsed_html = BeautifulSoup(page,"html.parser")
game_title = parsed_html.body.find('div',attrs={'id':'game_title'}).text
title_regex = re.compile(r'#(\d+).*?([a-zA-Z]+), ([a-zA-Z]+) (\d+), (\d+)')
response_regex = re.compile(r'stuck', '(.*/em>)')
num,dow,mon,day,year = re.search(title_regex,game_title).groups()
for clue in parsed_html.body.find_all('td',attrs={'class':'clue'}):
	for child in clue.descendants:
		try:
			print child['onmouseover']
		except:
			continue
