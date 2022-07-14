#!/usr/bin/env python3
from scripted_bot_example import *
from scripted_bot_example_original import *
from random_bot_example import *
from search_example import *
from mcts_example import *

import botbowl as botbowl
import time as time

if __name__ == '__main__':
    config = botbowl.load_config("bot-bowl")
    config.competition_mode = False
    config.pathfinding_enabled = True
    config.debug_mode = False
    ruleset = botbowl.load_rule_set(config.ruleset, all_rules=False)  # We don't need all the rules
    arena = botbowl.load_arena(config.arena)
    home = botbowl.load_team_by_filename("human", ruleset)
    away = botbowl.load_team_by_filename("human", ruleset)

    wins_home = 0
    wins_away = 0
    ties = 0
    # Play x games
    for i in range(100):
        # home_agent = botbowl.make_bot('first')
        # home_agent = botbowl.make_bot('my-random-bot')
        home_agent = botbowl.make_bot('scripted')
        # home_agent = botbowl.make_bot('search-bot')
        home_agent.name = "Bot UJI"
        away_agent = botbowl.make_bot('first')
        # away_agent = botbowl.make_bot('my-random-bot')
        # away_agent = botbowl.make_bot('scripted')
        # away_agent = botbowl.make_bot("search-bot")
        # away_agent = botbowl.make_bot("mcts")
        away_agent.name = "Bot 2"
        game = botbowl.Game(i, home, away, home_agent, away_agent, config, arena=arena, ruleset=ruleset)
        game.config.fast_mode = True

        print("Starting game", (i+1))
        start = time.time()
        game.init()
        end = time.time()
        print(end - start)

        if game.get_winning_team() is game.state.home_team:
            wins_home += 1
        elif game.get_winning_team() is game.state.away_team:
            wins_away += 1
        else:
            ties += 1

    print("wins_home: " + str(wins_home))
    print("wins_away: " + str(wins_away))
    print("ties: " + str(ties))