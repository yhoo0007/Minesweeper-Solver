# Python Minesweeper Solver
A Minesweeper solver written in Python. This solver uses Selenium to play Minesweeper on https://minesweeperonline.com/#. It can currently complete 'expert' level games in approximately 50 seconds and has a winrate of around 30-40%. Its gameplay is very close to optimal but there are still some areas that can be improved.

![example](https://github.com/yhoo0007/Minesweeper-Solver/blob/master/imgs/screenshot.png)

### Explanation
##### Frontiers
A Minesweeper game can generally be split into 'frontiers' where the clues in that frontier will only have an affect each other. This allows the solver to focus on subsections of the game and not have to compute the entire game state at every iteration. This is a massive time-saver especially when it comes to calculating probabilities.

The game can be split into frontiers by grouping the unsatisfied clues that are adjacent to each other together. Each clue can only belong to one frontier at a time. By doing this for every unsatisfied clue available, the game can be segmented into smaller sections to be processed individually.

##### Algorithm
In most stages of a Minesweeper game, progress can be made by simply checking the individual clues. I.e whenever the # of unopened squares adjacent to a clue matches the clue number, they can all be flagged as bombs. Similarly, when the number of flagged bombs adjacent to a clue matches the clue number, all remaining unopened squares can be safely* opened.

Other times the only way to proceed is to calculate the probabilities for each square. This is done by generating all possible bomb arrangements for a given frontier and then counting how many times a bomb occurs on a square / total number of arrangements.



\*it is only safe if we assume that the locations we flagged as bombs are correct which may not always be the case in situations where guessing is required.
