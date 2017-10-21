import Game

url = 'http://www.j-archive.com/showgame.php?game_id=1'
browser = webdriver.PhantomJS()
browser.get(url)
html = browser.page_source
game_one = Game.Game(html,url)
