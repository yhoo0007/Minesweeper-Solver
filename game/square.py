from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver, WebElement


class Square:
    TYPE_BLANK = 'blank'
    TYPE_BOMBDEATH = 'bombdeath'
    TYPE_BOMBREVEALED = 'bombrevealed'
    TYPE_FLAG = 'bombflagged'

    CHAR_BLANK = '*'
    CHAR_BOMBDEATH = 'x'
    CHAR_BOMBREVEALED = 'b'
    CHAR_FLAG = 'f'
    
    TYPE_TO_CHAR = {
        'blank': CHAR_BLANK,
        'bombdeath': CHAR_BOMBDEATH,
        'bombrevealed': CHAR_BOMBREVEALED,
        'bombflagged': CHAR_FLAG
    }
    
    def __init__(self, x: int, y: int, element: WebElement, webdriver: WebDriver) -> None:
        self.x = x
        self.y = y
        self._element = element
        self._webdriver = webdriver
        self.char = None
        self.refresh()
    
    def __repr__(self) -> str:
        return f'{self.x} {self.y} {self.char}'
    
    def __str__(self) -> str:
        return self.char
    
    def refresh(self) -> bool:
        '''
        Refreshes the square and returns whether the state has changed
        '''
        square_type = self._element.get_attribute('class').split(' ')[1]
        if square_type in Square.TYPE_TO_CHAR:
            new_char = Square.TYPE_TO_CHAR[square_type]
        else:
            new_char = square_type[4:]  # this extracts the clue number
        ret = self.char != new_char
        self.char = new_char
        return ret

    def getclue(self):
        try:
            return int(self.char)
        except ValueError:
            return None

    def click(self):
        action_chain = ActionChains(self._webdriver)
        action_chain.click(self._element)
        action_chain.perform()
    
    def flag(self):
        self.char = Square.CHAR_FLAG
        self.highlight('red')
    
    def decrementclue(self, val=1) -> int:
        if (clue := self.getclue()) is not None:
            clue = clue - val if clue >= val else 0
            self.char = str(clue)
            return clue
        else:
            raise Exception('Decrementing a non clue square!')

    def highlight(self, color: str):
        self._webdriver.execute_script(f"document.getElementById('{self.y + 1}_{self.x + 1}').style.backgroundBlendMode = 'screen';")
        self._webdriver.execute_script(f"document.getElementById('{self.y + 1}_{self.x + 1}').style.backgroundColor = '{color}';")
    
    def unhighlight(self):
        self._webdriver.execute_script(f"document.getElementById('{self.y + 1}_{self.x + 1}').style.backgroundBlendMode = '';")
        self._webdriver.execute_script(f"document.getElementById('{self.y + 1}_{self.x + 1}').style.backgroundColor = '';")
