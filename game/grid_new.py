from typing import List, Set, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from game.square_new import Square


class Grid:
    def __init__(self, webdriver: WebDriver, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._webdriver = webdriver
        self.squares = []
        self._getsquares()
        self.clues = set(square for square in self if square.clue)
    
    def __getitem__(self, key):
        return self.squares[key]

    def __setitem__(self, key, item):
        self.squares[key] = item
    
    def __iter__(self):
        return GridIterator(self)
    
    def __str__(self):
        return '\n'.join(' '.join(map(str, row)) for row in self.squares)

    def _getadj(self, square: Square, filter=lambda sq: True) -> Tuple[Square]:
        adj = []
        for dy in range(-1, 2):
            dsty = square.y + dy
            if dsty >= 0 and dsty < self.height:
                for dx in range(-1, 2):
                    dstx = square.x + dx
                    if (dstx >= 0 and dstx < self.width) and (dy != 0 or dx != 0):
                        if filter(self.squares[dsty][dstx]):
                            adj.append(self.squares[dsty][dstx])
        return tuple(adj)  # TODO change this to yield

    def _getsquares(self):
        square_elements = self._webdriver.find_elements_by_class_name('square')
        self.squares = [
            [
                Square(col_index, row_index, element, self._webdriver) 
                for col_index, element in enumerate(
                    square_elements[row_index * self.width:row_index * self.width + self.width]
                )
            ]
            for row_index in range(self.height)
        ]
        for square in self:
            square.adj = self._getadj(square)

    def getfrontiers(self) -> List[Set[Square]]:
        frontiers = []
        clues = self.clues.copy()
        while clues:
            clue = clues.pop()
            frontier = self.getfrontier(clue)
            frontiers.append(frontier)
            clues.difference_update(frontier)
        return frontiers
    
    def getfrontier(self, clue: Square) -> Set[Square]:
        frontier: Set[Square] = set([clue])
        to_process: List[Square] = [clue]
        while to_process:
            current = to_process.pop()
            for adj in filter(lambda sq: sq.clue and sq not in frontier, current.adj):
                frontier.add(adj)
                to_process.append(adj)
        return frontier

    def open(self, square: Square) -> bool:
        if square.char == Square.BLANK:
            square.click()
            return self.refresh(square)
        return False

    def flag(self, square: Square) -> Set[Square]:
        square.flag()
        ret: Set[Square] = set()
        for adj in square.adj:
            if adj.clue and adj.decrementclue() == 0:
                self.clues.remove(adj)
                ret.add(adj)
        return ret

    def reveal(self, square: Square) -> bool:
        square.reveal()
        for adj in filter(lambda sq: sq.char == Square.BLANK, square.adj):
            if self.refresh(adj):
                return True
        return False

    def _refresh_reveal_helper(self, square: Square, refreshed: Set[Square]):
        square.reveal()
        for adj in filter(lambda sq: sq.char == Square.BLANK, square.adj):
            if self.refresh(adj, refreshed):
                return True
        return False

    def refresh(self, start: Square, refreshed: Set[Square]=set()) -> bool:
        to_refresh = [start]
        while to_refresh:
            current = to_refresh.pop()
            if current not in refreshed and current.refresh():
                if current.char in (Square.BOMBDEATH, Square.BOMBREVEALED):
                    return True
                if current.clue:
                    adj_flags = len(list(filter(lambda sq: sq.char == Square.FLAG, current.adj)))
                    # update clue to reflect remaining value
                    if current.decrementclue(adj_flags):
                        self.clues.add(current)
                    elif self._refresh_reveal_helper(current, refreshed):
                        return True
                else:
                    to_refresh += current.adj
                    refreshed.add(current)
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

