from game.square import Square
from typing import List, Set
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By


class Grid:
    def __init__(self, webdriver: WebDriver, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._webdriver = webdriver
        square_elements = self._webdriver.find_elements(By.CLASS_NAME, 'square')
        self.squares = [
            [
                Square(col_index, row_index, element, self._webdriver) 
                for col_index, element in enumerate(
                    square_elements[row_index * self.width:row_index * self.width + self.width]
                )
            ]
            for row_index in range(self.height)
        ]
        self.clues = set(square for square in self if square.getclue())

    def __getitem__(self, key) -> List[Square]:
        return self.squares[key]

    def __setitem__(self, key, item):
        self.squares[key] = item
    
    def __iter__(self):
        return GridIterator(self)
    
    def __str__(self):
        return '\n'.join(' '.join(map(str, row)) for row in self.squares)
    
    def getadj(self, square: Square, filter=lambda sq: True) -> List[Square]:
        '''
        Returns the squares adjacent to the given one.
        '''
        adj = []
        for dy in range(-1, 2):
            dsty = square.y + dy
            if dsty >= 0 and dsty < self.height:
                for dx in range(-1, 2):
                    dstx = square.x + dx
                    if (dstx >= 0 and dstx < self.width) and (dy != 0 or dx != 0):
                        if filter(self.squares[dsty][dstx]):
                            adj.append(self.squares[dsty][dstx])
        return adj  # TODO change this to yield

    def getfrontiers(self) -> List[Set[Square]]:
        '''
        Returns a list of frontiers.
        '''
        frontiers = []
        clues = self.clues.copy()
        while clues:
            clue = clues.pop()
            frontier = self.getfrontier(clue)
            frontiers.append(frontier)
            clues.difference_update(frontier)
        return frontiers
    
    def getfrontier(self, clue: Square) -> Set[Square]:
        '''
        Finds the frontier which includes the given clue square.
        '''
        frontier: Set[Square] = set([clue])
        to_process: List[Square] = [clue]
        while to_process:
            current = to_process.pop()
            for adj in filter(
                lambda sq: sq.getclue() and sq not in frontier,
                self.getadj(current)
            ):  # TODO try passing filter into getadj
                frontier.add(adj)
                to_process.append(adj)
        return frontier
    
    def open(self, square: Square) -> bool:
        '''
        Clicks the given square and updates the grid state.
        '''
        if square.char == Square.CHAR_BLANK:
            square.click()
            return self.refresh(start=square)
        return False
    
    def flag(self, square: Square) -> List[Square]:
        '''
        Flags the given square and returns a list of adjacent squares that have been satisfied.
        '''
        square.flag()
        sat = []
        for adj_sq in self.getadj(square, lambda sq: sq.getclue()):
            updated_clue = adj_sq.decrementclue()
            if updated_clue == 0:
                sat.append(adj_sq)
                self.clues.remove(adj_sq)
        return sat
    
    def refresh(self, start: Square, refreshed: Set[Square]=set()) -> bool:
        '''
        From the given square, refresh adjacent squares as long as they have changed. Returns a
        bool representing whether the game is over.
        '''
        to_refresh = [start]
        while to_refresh:
            current = to_refresh.pop()
            if current.refresh():
                refreshed.add(current)
                if current.char in (Square.CHAR_BOMBDEATH, Square.CHAR_BOMBREVEALED):
                    return True
                if current.getclue() == 0:
                    for adj in self.getadj(current, lambda sq: sq not in refreshed):
                        to_refresh.append(adj)
                else:
                    # update clue to reflect remaining value
                    adj_flags = self.getadj(current, lambda sq: sq.char == Square.CHAR_FLAG)
                    updated_clue = current.decrementclue(len(adj_flags))
                    if updated_clue:
                        self.clues.add(current)
                    else:
                        # free open
                        for safe_sq in self.getadj(current, lambda sq: sq.char == Square.CHAR_BLANK):
                            if self.open(safe_sq):
                                return True
                            # return safe_sq.click() and self.refresh(safe_sq, refreshed)
        return False

class GridIterator:
    def __init__(self, grid: Grid):
        self.grid = grid
        self.row_index = 0
        self.col_index = 0

    def __next__(self):
        if self.row_index < self.grid.height:
            if self.col_index < self.grid.width:
                res = self.grid[self.row_index][self.col_index]
                self.col_index = (self.col_index + 1) % self.grid.width
                if self.col_index == 0:
                    self.row_index += 1
            return res
        raise StopIteration
