from game.game import Game
from selenium.common.exceptions import UnexpectedAlertPresentException
import cProfile
from timeit import default_timer as timer


GAME_STATE = None

# medium-length guessing algoX game: ~96s
# GAME_STATE = 'eyJ2ZXJzaW9uIjoxLCJnYW1lVHlwZUlkIjozLCJudW1Sb3dzIjoxNiwibnVtQ29scyI6MzAsIm51bU1pbmVzIjo5OSwiZ3JpZE9iaiI6W1swLDEsMSwyLDEsMSwwLDAsMCwwLDAsMCwxLDEsMSwwLDAsMCwwLDEsMSwyLDEsMSwwLDEsMSwxLDAsMCwwLDBdLFswLDEsLTEwLDIsLTEwLDEsMCwwLDEsMiwyLDEsMSwtMTAsMSwxLDIsMiwxLDEsLTksMywtOSwxLDAsMSwtOSwzLDIsMSwwLDBdLFswLDIsMiwzLDEsMSwwLDAsMSwtOSwtOCwyLDIsMSwyLDIsLTcsLTcsMywyLDIsLTgsMiwxLDAsMSwzLC03LC04LDEsMCwwXSxbMCwxLC05LDIsMSwxLDEsMiwyLDMsNCwtOCwyLDAsMSwtOSw0LC03LC04LDEsMSwxLDEsMCwwLDAsMiwtOCwzLDEsMCwwXSxbMCwyLDQsLTcsMiwxLC0xMCwyLC0xMCwxLDIsLTksMywxLDIsMiwzLDMsMiwxLDAsMSwxLDIsMSwyLDIsMiwxLDAsMCwwXSxbMSwzLC02LC03LDIsMSwyLDMsMiwxLDEsMSwzLC05LDIsMSwtMTAsMiwyLDIsMSwxLC0xMCwzLC05LDQsLTksMiwwLDEsMSwxXSxbMSwtOCwtNiw0LDIsMCwyLC05LDIsMCwwLDAsMiwtOCwzLFsyLDEsMCwwXSxbMSwxLDAsMF0sWzMsMSwwLDBdLC04LC04LDEsMSwxLDMsLTksNSwtOCw0LDEsMiwtMTAsMV0sWzEsMiw0LC04LDIsMSw0LC03LDQsMSwxLDAsMSwyLC05LFsxLDEsMCwwXSxbMCwxLDAsMF0sWzIsMSwwLDBdLC04LDMsMSwxLDEsMywyLDUsLTgsNCwtMTAsMiwxLDFdLFswLDAsMiwtOCwzLDIsLTgsLTcsNCwtOSwxLDAsMCxbMSwxLDAsMF0sWzEsMSwwLDBdLFsxLDEsMCwwXSxbMCwxLDAsMF0sWzIsMSwwLDBdLDIsMiwxLDIsLTksMiwtMTAsMywtOSwzLDEsMSwwLDBdLFswLDAsMSwyLC05LDIsMiwzLC04LDIsMSwxLDEsWzEsMSwwLDBdLFswLDEsMCwwXSxbMCwxLDAsMF0sWzAsMSwwLDBdLFsxLDEsMCwwXSwtOSwyLDMsLTgsMywzLDIsMywxLDEsMCwwLDAsMF0sWzEsMiwzLDMsMiwxLDEsMiwyLDIsMSwyLC05LFsyLDEsMCwwXSxbMSwxLDAsMF0sWzAsMSwwLDBdLFsxLDEsMCwwXSxbMiwxLDAsMF0sMywtOCw0LC04LDIsMiwtOCwzLDEsMCwwLDEsMSwxXSxbMSwtOCwtNywtOCwxLDAsMSwtMTAsMSwxLC0xMCwzLDMsLTgsWzEsMSwwLDBdLFswLDEsMCwwXSxbMSwxLDAsMF0sLTEwLDIsMywtNywzLDIsMywtNiwtNywyLDAsMCwxLC0xMCwxXSxbMSwzLC03LDMsMSwwLDEsMiwyLDIsMiwzLC03LDMsWzMsMSwwLDBdLFsxLDEsMCwwXSxbMywxLDAsMF0sMiwyLDIsLTksMiwxLC05LDQsLTgsMiwwLDAsMSwxLDFdLFswLDEsMSwxLDAsMSwxLDMsLTksMiwxLC05LDQsLTgsMywtMTAsMiwtMTAsMSwxLDEsMSwxLDEsMywyLDIsMSwxLDEsMCwwXSxbMCwwLDAsMCwwLDEsLTEwLDMsLTksMiwxLDEsMywtOCw1LDMsMywxLDIsMSwxLDAsMCwwLDIsLTksMiwxLC0xMCwxLDAsMF0sWzAsMCwxLDEsMSwxLDEsMiwxLDIsMSwyLDIsMywtOCwtOCwzLDIsMiwtMTAsMiwyLDIsMiwzLC04LDMsMiwyLDEsMCwwXSxbMCwwLDEsLTEwLDEsMCwwLDAsMCwxLC0xMCwyLC0xMCwyLDIsMywtOCwtOSwyLDEsMiwtOSwtOSwyLC05LDIsMiwtMTAsMSwwLDAsMF0sWzAsMCwxLDEsMSwwLDAsMCwwLDEsMSwyLDEsMSwwLDEsMiwyLDEsMCwxLDIsMiwyLDEsMSwxLDEsMSwwLDAsMF1dLCJ0aW1lIjoxfQ=='


DIFFICULTIES = {
    'beginner': {
        'difficulty': 'beginner',
        'width': 9,
        'height': 9,
        'bombs': 10
    },
    'intermediate': {
        'difficulty': 'intermediate',
        'width': 16,
        'height': 16,
        'bombs': 40
    },
    'expert': {
        'difficulty': '',
        'width': 30,
        'height': 16,
        'bombs': 99
    }
}


def driver():
    game = None
    try:
        sum_tt = 0
        wins = 0
        n_games = 0
        game = Game(**DIFFICULTIES['expert'], state=GAME_STATE)
        while True:
            win = False
            tt = timer()
            game.start()
            try:
                game.attemptsolve()
            except UnexpectedAlertPresentException:
                print('Winner is you')
                wins += 1
                tt = timer() - tt
                sum_tt += tt
                win = True
            if not win: game.savescreenshot()
            n_games += 1
            print(
                'N Games:', n_games,
                'Winrate:', wins / n_games * 100,
                'Average TT:', (sum_tt / wins) if wins > 0 else None
            )
            game.restart()
    except KeyboardInterrupt:
        input('Terminate >')
    finally:
        if game:
            print('Closing game')
            game.close()

if __name__ == '__main__':
    # cProfile.run('driver()', sort='tottime')
    driver()
    # game = Game(**DIFFICULTIES['expert'], state=GAME_STATE)