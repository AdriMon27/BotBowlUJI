from botbowl import Square

import botbowl
from botbowl.core import Action, Agent
import numpy as np
from copy import deepcopy
import random
import time
from random_bot_example import *


class Node:
    def __init__(self, action=None, parent=None):
        self.parent = parent
        self.children = []
        self.action = action
        self.evaluations = []

    def num_visits(self):
        return len(self.evaluations)

    def visit(self, score):
        self.evaluations.append(score)

    def score(self):
        return np.average(self.evaluations)


class SearchBot(botbowl.Agent):

    def __init__(self, name, seed=None):
        super().__init__(name)
        self.my_team = None
        self.rnd = np.random.RandomState(seed)

    def new_game(self, game, team):
        self.my_team = team

    def act(self, game):
        game_copy = deepcopy(game)
        game_copy.enable_forward_model()
        game_copy.home_agent.human = True
        game_copy.away_agent.human = True

        root_step = game_copy.get_step()
        root_node = Node()
        l = game_copy.get_available_actions()
        for action_choice in game_copy.get_available_actions():
            if action_choice.action_type == botbowl.ActionType.PLACE_PLAYER:
                continue
            for player in action_choice.players:
                root_node.children.append(Node(Action(action_choice.action_type, player=player), parent=root_node))
            for position in action_choice.positions:
                root_node.children.append(Node(Action(action_choice.action_type, position=position), parent=root_node))
            if len(action_choice.players) == len(action_choice.positions) == 0:
                root_node.children.append(Node(Action(action_choice.action_type), parent=root_node))

        best_node = None
        # print(f"Evaluating {len(root_node.children)} nodes")
        t = time.time()
        for node in root_node.children:
            game_copy.step(node.action)
            while not game.state.game_over and len(game.state.available_actions) == 0:
                game_copy.step()
            score = self._evaluate(game)
            node.visit(score)
            # print(f"{node.action.action_type}: {node.score()}")
            if best_node is None or node.score() > best_node.score():
                best_node = node

            game_copy.revert(root_step)

        # print(f"{best_node.action.action_type} selected in {time.time() - t} seconds")

        return best_node.action

    def _evaluate(self, game):
        puntos = 0

        my_team = game.get_agent_team(game.home_agent)
        opp_team = game.get_agent_team(game.away_agent)

        # mirar los jugadores
        for player in my_team.players:
            # Que tenemos de pie y no estuneados
            if player.position is not None and player.state.up and not player.state.stunned:
                puntos += 1

            # Que no han sido usados
            if not player.state.used:
                puntos -= 1

        # mirar si el jugador con bola está protegido
        aux_ball_position = game.get_ball_position()
        if aux_ball_position is not None:  # comprobar que estamos en un estado con bola en el campo
            cage_positions = [
                Square(aux_ball_position.x - 1, aux_ball_position.y - 1),
                Square(aux_ball_position.x + 1, aux_ball_position.y - 1),
                Square(aux_ball_position.x - 1, aux_ball_position.y + 1),
                Square(aux_ball_position.x + 1, aux_ball_position.y + 1)
            ]
            for cage_position in cage_positions:
                if game.get_player_at(cage_position) is not None:
                    puntos += 1

        # mirar los jugadores rivales tumbados o estuneados
        for rival_player in opp_team.players:
            if rival_player is not None and (not rival_player.state.up or rival_player.state.stunned):
                puntos += 1

        return puntos + random.random()/10

    def end_game(self, game):
        pass

# Register the bot to the framework
botbowl.register_bot('search-bot', SearchBot)

if __name__ == '__main__':
    # Load configurations, rules, arena and teams
    config = botbowl.load_config("bot-bowl")
    ruleset = botbowl.load_rule_set(config.ruleset)
    arena = botbowl.load_arena(config.arena)
    home = botbowl.load_team_by_filename("human", ruleset)
    away = botbowl.load_team_by_filename("human", ruleset)
    config.competition_mode = False
    config.debug_mode = False
    config.fast_mode = True
    config.pathfinding_enabled = False

    # Play a game
    bot_a = botbowl.make_bot("search-bot")
    bot_b = botbowl.make_bot("my-random-bot")
    game = botbowl.Game(1, home, away, bot_a, bot_b, config, arena=arena, ruleset=ruleset)
    print("Starting game")
    game.init()
    print("Game is over")
    print(game.get_winning_team())