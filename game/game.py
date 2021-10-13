import itertools
import os
from typing import DefaultDict, Set
from game.exactcover import createnodematrix, exactcover
from game.grid import Grid
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from game.square import Square


class Game:
    WEBDRIVER_PATH = 'chromedriver.exe'
    GAMEURL = 'http://minesweeperonline.com/#'
    SCREENSHOT_PATH = './screenshots'

    def __init__(
        self,
        difficulty: str,
        width: int,
        height: int,
        bombs: int,
        state: str=None
    ) -> None:
        self.width = width
        self.height = height
        self.bombs = bombs
        self.remaining_bombs = bombs
        self.game_over = False
        self._webdriver = webdriver.Chrome(executable_path=Game.WEBDRIVER_PATH)
        self._webdriver.set_window_size(800, 600)
        self._webdriver.get(self.GAMEURL + difficulty)
        if state:
            self.loadstate(state)
        self.grid = Grid(self._webdriver, width, height)

    def loadstate(self, state: str) -> None:
        action_chain = ActionChains(self._webdriver)
        import_btn = self._webdriver.find_element_by_id('import-link')
        action_chain.click(import_btn)
        action_chain.send_keys(state)
        action_chain.perform()
        load_btn = self._webdriver.find_element_by_css_selector('input[value="Load Game"]')
        action_chain = ActionChains(self._webdriver)
        action_chain.send_keys_to_element(load_btn, Keys.ENTER)
        action_chain.perform()

    def restart(self):
        for flag in filter(lambda sq: sq.char == Square.CHAR_FLAG, self.grid):
            flag.unhighlight()
        self.remaining_bombs = self.bombs
        self.game_over = False
        action_chain = ActionChains(self._webdriver)
        action_chain.send_keys(Keys.F2)
        action_chain.perform()
        self.grid = Grid(self._webdriver, self.width, self.height)
        for sq in self.grid:
            sq.unhighlight()

    def start(self) -> None:
        square = self.grid[self.height // 2][self.width // 2]
        self.game_over |= self.grid.open(square)

    def close(self) -> None:
        self._webdriver.close()
    
    def savescreenshot(self) -> None:
        i = 1
        while os.path.exists(os.path.join(Game.SCREENSHOT_PATH, f'screenshot{i}.png')):
            i += 1
        fp = os.path.join(Game.SCREENSHOT_PATH, f'screenshot{i}.png')
        self._webdriver.save_screenshot(fp)

    def flag(self, square: Square) -> Set[Square]:
        '''
        Flags a square on the grid and returns a list of squares that are safe to open as a result.
        '''
        safe: Set[Square] = set()
        sat_clues = self.grid.flag(square)
        self.remaining_bombs -= 1
        for sat_clue in sat_clues:
            adj_safe = self.grid.getadj(sat_clue, lambda sq: sq.char == Square.CHAR_BLANK)
            safe.update(adj_safe)
        return safe

    def open_multiple(self, to_open):
        ret = False
        for sq in to_open:
            sq.highlight('green')
        for sq in to_open:
            ret |= self.grid.open(sq)
            sq.unhighlight()
        return ret

    def attemptsolve(self) -> bool:
        while not self.game_over:
            trivial_progress = False
            frontier_cache = []
            frontiers = self.grid.getfrontiers()
            frontiers_to_process = sorted([f for f in frontiers if f not in frontier_cache], key=lambda f: len(f))

            for frontier in frontiers_to_process:
                trivial_progress |= self.trivial(frontier)
            
            if not trivial_progress and not self.game_over:
                to_open: Set[Square] = set()
                combined_prob = {}
                for frontier in frontiers_to_process:
                    # highlight current frontier
                    for sq in frontier:
                        sq.highlight('blue')

                    probabilities = self.getprobabilities(frontier)
                    # combined_prob.update(probabilities)
                    for sq, prob in probabilities.items():
                        if sq not in combined_prob:
                            combined_prob[sq] = (0, 0)
                        combined_prob[sq] = (combined_prob[sq][0] + prob[0], combined_prob[sq][1] + prob[1])

                    # flag confirmed bombs
                    for sq in (square for square, prob in probabilities.items() if prob[0] / prob[1] == 1):
                        to_open.update(self.flag(sq))
                    
                    # open all non bombs
                    for sq in frontier:
                        for adj_blank in self.grid.getadj(sq, lambda sq: sq.char == Square.CHAR_BLANK):
                            if adj_blank not in probabilities:
                                to_open.add(adj_blank)

                    # unhighlight the frontier
                    for sq in frontier:
                        sq.unhighlight()
                    
                    if to_open:
                        break

                if not to_open:
                    if combined_prob:
                        # take a guess by flagging the square with the highest probability
                        guess = max(
                            filter(lambda sq: combined_prob[sq][0] / combined_prob[sq][1] != 1, combined_prob),
                            key=lambda sq: combined_prob[sq][0] / combined_prob[sq][1]
                        )
                        to_open.update(self.flag(guess))
                        for k, v in combined_prob.items():
                            print(k.__repr__(), v, v[0] / v[1])
                        print('Guessing', guess.__repr__(), combined_prob[guess], combined_prob[guess][0] / combined_prob[guess][1])
                    elif self.remaining_bombs != 0:
                        # this clause will be reached if there is some unreachable region of the 
                        # grid and there are still bombs remaining. In this case, the only option
                        # is to randomly pick a square in that region.
                        print('Unreachable region detected')
                        blanks = list(filter(lambda sq: sq.char == Square.CHAR_BLANK, self.grid))
                        guess = blanks[0]
                        to_open.update(self.flag(guess))
                    else:
                        # unreachable region is completely safe
                        to_open.update(filter(lambda sq: sq.char == Square.CHAR_BLANK, self.grid))

                self.game_over |= self.open_multiple(to_open)
            
            # update frontier cache
            frontier_cache = frontiers

    def trivial(self, frontier: Set[Square]) -> bool:
        to_open: Set[Square] = set()
        for clue_sq in frontier:
            if clue_sq.getclue():
                adj_blanks = self.grid.getadj(clue_sq, lambda sq: sq.char == Square.CHAR_BLANK)
                if len(adj_blanks) == clue_sq.getclue():  # and clue != 0 ?
                    # flag all adjacent blanks
                    for adj_blank in adj_blanks:
                        to_open.update(self.flag(adj_blank))
        if to_open:
            self.game_over |= self.open_multiple(to_open)
            return True
        return False
    
    def creatematrix(self, frontier: Set[Square]):
        frontier_blanks = set()
        for clue_sq in frontier:
            adj = self.grid.getadj(clue_sq, lambda sq: sq.char == Square.CHAR_BLANK)
            frontier_blanks.update(adj)

        clue_index_lookup = {}
        i = 0
        mat = []
        row_lookup = []
        col_lookup = []
        for sq in frontier_blanks:
            ranges = []
            col_header = []
            for clue_sq in self.grid.getadj(sq, lambda s: s in frontier):
                col_header.append(clue_sq)
                if clue_sq not in clue_index_lookup:
                    clue = clue_sq.getclue()
                    clue_index_lookup[clue_sq] = (i, i + clue)
                    i = i + clue
                ranges.append(range(*clue_index_lookup[clue_sq]))
            col_lookup.append(col_header)
            
            # generate all possible combinations, each combination is a row
            for index_set in itertools.product(*ranges):
                mat.append(index_set)
                row_lookup.append(sq)
        return mat, row_lookup, col_lookup, len(row_lookup), i

    def getprobabilities(self, frontier):
        probabilities = DefaultDict(lambda: 0)

        mat, row_lookup, col_lookup, n_rows, n_cols = self.creatematrix(frontier)
        node_matrix = createnodematrix(mat, n_rows, n_cols)
        ret = []
        exactcover(node_matrix, all_solutions=ret)

        # get only unique solutions
        unique_solutions = set([
            frozenset(row_lookup[node.row] for node in solution)
            for solution in ret
        ])

        for solution in unique_solutions:
            for square in solution:
                probabilities[square] += 1
        for square in probabilities:
            probabilities[square] = (probabilities[square], len(unique_solutions))

        return probabilities

