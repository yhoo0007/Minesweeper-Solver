from typing import Tuple
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver, WebElement


class Square:
    TYPE_BLANK = 'blank'
    TYPE_BOMBDEATH = 'bombdeath'
    TYPE_BOMBREVEALED = 'bombrevealed'
    TYPE_FLAG = 'bombflagged'

    BLANK = '*'
    BOMBDEATH = 'x'
    BOMBREVEALED = 'b'
    FLAG = 'f'

    TYPE_TO_CHAR = {
        'blank': BLANK,
        'bombdeath': BOMBDEATH,
        'bombrevealed': BOMBREVEALED,
        'bombflagged': FLAG
    }

    def __init__(self, x: int, y: int, element: WebElement, webdriver: WebDriver) -> None:
        self.x = x
        self.y = y
        self._element = element
        self._webdriver = webdriver
        self.is_revealed = False
        self.char = None
        self.clue = None
        self.adj: Tuple[Square] = ()
        self.refresh()

    def __repr__(self) -> str:
        return f'{self.x} {self.y} {self.char}'
    
    def __str__(self) -> str:
        return self.char
    
    def refresh(self) -> bool:
        square_type = self._element.get_attribute('class').split(' ')[1]
        if square_type in Square.TYPE_TO_CHAR:
            new_char = Square.TYPE_TO_CHAR[square_type]
        else:
            new_char = square_type[4:]  # this extracts the clue number
            self.clue = int(new_char)
        ret = self.char != new_char
        self.char = new_char
        return ret

    def click(self):
        action_chain = ActionChains(self._webdriver)
        action_chain.click(self._element)
        action_chain.perform()
    
    def flag(self):
        self.char = Square.FLAG
        # self.highlight('red')
        action_chain = ActionChains(self._webdriver)
        action_chain.move_to_element(self._element)
        action_chain.send_keys(' ')
        action_chain.perform()
    
    def reveal(self):
        if not self.is_revealed:
            self.is_revealed = True
            if len(list(filter(lambda sq: sq.char == Square.BLANK, self.adj))):
                action_chain = ActionChains(self._webdriver)
                action_chain.move_to_element(self._element)
                action_chain.send_keys(' ')
                action_chain.perform()
    
    def decrementclue(self, val=1) -> int:
        if self.clue is not None:
            self.clue = self.clue - val if self.clue >= val else 0
            self.char = str(self.clue)
            return self.clue
        else:
            raise Exception('Decrementing a non clue square!')

    def highlight(self, color: str):
        self._webdriver.execute_script(f"document.getElementById('{self.y + 1}_{self.x + 1}').style.backgroundBlendMode = 'screen';")
        self._webdriver.execute_script(f"document.getElementById('{self.y + 1}_{self.x + 1}').style.backgroundColor = '{color}';")
    
    def unhighlight(self):
        self._webdriver.execute_script(f"document.getElementById('{self.y + 1}_{self.x + 1}').style.backgroundBlendMode = '';")
        self._webdriver.execute_script(f"document.getElementById('{self.y + 1}_{self.x + 1}').style.backgroundColor = '';")

