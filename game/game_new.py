import itertools
from typing import DefaultDict, List, Optional, Set, Tuple
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from game.exactcover import createnodematrix, exactcover
from game.grid_new import Grid
from game.square_new import Square


class Game:
    WEBDRIVER_PATH = 'E:/New folder/xtras/Minesweeper/webdriver/chromedriver.exe'
    GAMEURL = 'http://minesweeperonline.com/#'

    def __init__(
        self,
        difficulty: str,
        width: int,
        height: int,
        bombs: int,
        state: str=None
    ):
        self.width = width
        self.height = height
        self.bombs = bombs
        self.remaining_bombs = bombs
        self.game_over = False
        self._webdriver = webdriver.Chrome(executable_path=Game.WEBDRIVER_PATH + difficulty)
        self._webdriver.set_window_size(800, 600)
        self._webdriver.get(self.GAMEURL + difficulty)
        if state:
            self.loadstate(state)
        self.grid = Grid(self._webdriver, width, height)

    def loadstate(self, state: str):
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
        self.remaining_bombs = self.bombs
        self.game_over = False
        action_chain = ActionChains(self._webdriver)
        action_chain.send_keys(Keys.F2)
        action_chain.perform()
        self.grid = Grid(self._webdriver, self.width, self.height)
        for sq in self.grid:
            sq.unhighlight()

    def start(self):
        square = self.grid[self.height // 2][self.width // 2]
        self.game_over |= self.open([square])

    def close(self):
        self._webdriver.close()

    def open(self, squares: Set[Square]) -> bool:
        for square in squares:
            square.highlight('green')
            game_over = self.grid.open(square)
            square.unhighlight()
            if game_over:
                return True
        return False
    
    def reveal(self, squares: Set[Square]) -> bool:
        for square in squares:
            square.highlight('darkgreen')
            game_over = self.grid.reveal(square)
            square.unhighlight()
            if game_over:
                return True
        return False

    def flag(self, square: Square):
        self.remaining_bombs -= 1
        return self.grid.flag(square)
    
    def getfrontiers(self) -> List[Set[Square]]:
        frontiers = self.grid.getfrontiers()
        frontiers_to_process = sorted(frontiers, key=lambda f: len(f), reverse=True)
        return frontiers_to_process

    def attemptsolve(self) -> bool:
        dead_frontier = []
        frontiers = self.getfrontiers()
        guess = (None, 0)

        while not self.game_over:
            if frontiers:
                frontier = frontiers.pop()
                for sq in frontier:
                    sq.highlight('blue')

                to_open = set()
                to_reveal = self.trivial(frontier)
                if not to_reveal:
                    to_reveal, to_open, f_highest_prob = self.bruteforce(frontier)
                    guess = max(guess, f_highest_prob, key=lambda entry: entry[1])

                if to_reveal:
                    # perform reveal and update frontiers
                    if self.reveal(to_reveal):
                        return False
                    frontiers = [f for f in self.getfrontiers() if f not in dead_frontier]
                
                if to_open:
                    # perform opening and update frontiers
                    if self.open(to_open):
                        return False
                    frontiers = [f for f in self.getfrontiers() if f not in dead_frontier]
                
                if not to_reveal and not to_open:
                    dead_frontier.append(frontier)
                
                for sq in frontier:
                    sq.unhighlight()
                
            else:
                if guess[0]:
                    # flag the guess square
                    to_reveal = self.flag(guess[0])

                elif self.remaining_bombs > 0:
                    # make a random guess on a blank square
                    blanks = list(filter(lambda sq: sq.char == Square.BLANK, self.grid))
                    guess = blanks[0]
                    to_reveal = self.flag(guess)

        else:
            # open all remaining blank squares
            to_open = set(filter(lambda sq: sq.char == Square.BLANK, self.grid))
            


    def trivial(self, frontier: Set[Square]) -> Set[Square]:
        to_reveal: Set[Square] = set()
        for clue_sq in filter(lambda s: s.clue, frontier):
            blanks = list(filter(lambda s: s.char == Square.BLANK, clue_sq.adj))
            if len(blanks) == clue_sq.clue:
                for blank in blanks:
                    to_reveal.update(self.flag(blank))
        return to_reveal

    def bruteforce(self, frontier) -> Tuple[Set[Square], Set[Square], Tuple[Optional[Square], int]]:
        to_reveal: Set[Square] = set()
        to_open: Set[Square] = set()
        f_probs = self.getprobabilities(frontier)

        # flag confirmed bombs
        for confirmed_bomb in filter(lambda sq: f_probs[sq] == 1, f_probs):
            to_reveal.update(self.flag(confirmed_bomb))
        
        # open all non bombs
        f_blanks = set((adj_blank for sq in frontier for adj_blank in sq.adj if adj_blank.char == Square.BLANK))
        to_open = set(filter(lambda blank: blank not in f_probs, f_blanks))
        
        # find the highest prob square
        filtered = tuple(filter(lambda entry: entry[1] != 1, f_probs.items()))
        f_highest_prob = max(
            filtered,
            key=lambda entry: entry[1]
        ) if filtered else (None, 0)

        return to_reveal, to_open, f_highest_prob

    def creatematrix(self, frontier: Set[Square]):
        frontier_blanks: Set[Square] = set()
        for clue_sq in frontier:
            adj = filter(lambda s: s.char == Square.BLANK, clue_sq.adj)
            frontier_blanks.update(adj)

        clue_index_lookup = {}
        i = 0
        mat = []
        row_lookup = []
        col_lookup = []
        for sq in frontier_blanks:
            ranges = []
            col_header = []
            for clue_sq in filter(lambda s: s in frontier, sq.adj):
                col_header.append(clue_sq)
                if clue_sq not in clue_index_lookup:
                    clue = clue_sq.clue
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

        mat, row_lookup, _, n_rows, n_cols = self.creatematrix(frontier)
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
            probabilities[square] /= len(unique_solutions)

        return probabilities
