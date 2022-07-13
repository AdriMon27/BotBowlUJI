#!/usr/bin/env python3
from copy import deepcopy
from typing import List

import botbowl
from botbowl import Action, ActionType, Square, BBDieResult, Skill, Formation, ProcBot
import botbowl.core.pathfinding as pf
import time
import math
from botbowl.core.pathfinding.python_pathfinding import Path  # Only used for type checker
import random

TIME_THINKING = 10.0 #HE PUESTO 1 SEGUNDO DE PRIMERAS, LUEGO CAMBIAR CUANDO RESPONDAN EN EL SERVER

class MyScriptedBot2(ProcBot):

    def __init__(self, name):
        super().__init__(name)
        self.my_team = None
        self.opp_team = None
        self.actions = []
        self.last_turn = 0
        self.last_half = 0

        #variables para hacer el aleatorio de la estrategia
        self.orden_operaciones = []
        self.index_operacion = 0
        self.n_operaciones = 10

        self.off_formation = [
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "m", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "x", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "S"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "x"],
            ["-", "-", "-", "-", "-", "s", "-", "-", "-", "0", "-", "-", "S"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "x"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "S"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "x", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "m", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]
        ]

        self.def_formation = [
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "x", "-", "b", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "x", "-", "S", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "0"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "0"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "0"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "x", "-", "S", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "x", "-", "b", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]
        ]

        self.off_formation = Formation("Wedge offense", self.off_formation)
        self.def_formation = Formation("Zone defense", self.def_formation)
        self.setup_actions = []

    def new_game(self, game, team):
        """
        Called when a new game starts.
        """
        self.my_team = team
        self.opp_team = game.get_opp_team(team)
        self.last_turn = 0
        self.last_half = 0

    def coin_toss_flip(self, game):
        """
        Select heads/tails and/or kick/receive
        """
        return Action(ActionType.TAILS)
        # return Action(ActionType.HEADS)

    def coin_toss_kick_receive(self, game):
        """
        Select heads/tails and/or kick/receive
        """
        return Action(ActionType.RECEIVE)
        # return Action(ActionType.KICK)

    def setup(self, game):
        """
        Use either a Wedge offensive formation or zone defensive formation.
        """
        # Update teams
        self.my_team = game.get_team_by_id(self.my_team.team_id)
        self.opp_team = game.get_opp_team(self.my_team)

        if self.setup_actions:
            action = self.setup_actions.pop(0)
            return action

        # If traditional board size
        if game.arena.width == 28 and game.arena.height == 17:
            if game.get_receiving_team() == self.my_team:
                self.setup_actions = self.off_formation.actions(game, self.my_team)
                self.setup_actions.append(Action(ActionType.END_SETUP))
            else:
                self.setup_actions = self.def_formation.actions(game, self.my_team)
                self.setup_actions.append(Action(ActionType.END_SETUP))
            action = self.setup_actions.pop(0)
            return action

        # If smaller variant - use built-in setup actions

        for action_choice in game.get_available_actions():
            if action_choice.action_type != ActionType.END_SETUP and action_choice.action_type != ActionType.PLACE_PLAYER:
                self.setup_actions.append(Action(ActionType.END_SETUP))
                return Action(action_choice.action_type)

        # This should never happen
        return None

    def perfect_defense(self, game):
        return Action(ActionType.END_SETUP)

    def reroll(self, game):
        """
        Select between USE_REROLL and DONT_USE_REROLL
        """
        reroll_proc = game.get_procedure()
        context = reroll_proc.context
        if type(context) == botbowl.Dodge:
            return Action(ActionType.USE_REROLL)
        if type(context) == botbowl.Pickup:
            return Action(ActionType.USE_REROLL)
        if type(context) == botbowl.PassAttempt:
            return Action(ActionType.USE_REROLL)
        if type(context) == botbowl.Catch:
            return Action(ActionType.USE_REROLL)
        if type(context) == botbowl.GFI:
            return Action(ActionType.USE_REROLL)
        if type(context) == botbowl.BloodLust:
            return Action(ActionType.USE_REROLL)
        if type(context) == botbowl.Block:
            attacker = context.attacker
            attackers_down = 0
            for die in context.roll.dice:
                if die.get_value() == BBDieResult.ATTACKER_DOWN:
                    attackers_down += 1
                elif die.get_value() == BBDieResult.BOTH_DOWN and not attacker.has_skill(Skill.BLOCK) and not attacker.has_skill(Skill.WRESTLE):
                    attackers_down += 1
            if attackers_down > 0 and context.favor != self.my_team:
                return Action(ActionType.USE_REROLL)
            if attackers_down == len(context.roll.dice) and context.favor != self.opp_team:
                return Action(ActionType.USE_REROLL)
            return Action(ActionType.DONT_USE_REROLL)
        return Action(ActionType.DONT_USE_REROLL)

    def place_ball(self, game):
        """
        Place the ball when kicking.
        """
        side_width = game.arena.width / 2
        side_height = game.arena.height
        squares_from_left = math.ceil(side_width / 2)
        squares_from_right = math.ceil(side_width / 2)
        squares_from_top = math.floor(side_height / 2)
        left_center = Square(squares_from_left, squares_from_top)
        right_center = Square(game.arena.width - 1 - squares_from_right, squares_from_top)
        if game.is_team_side(left_center, self.opp_team):
            return Action(ActionType.PLACE_BALL, position=left_center)
        return Action(ActionType.PLACE_BALL, position=right_center)

    def high_kick(self, game):
        """
        Select player to move under the ball.
        """
        ball_pos = game.get_ball_position()
        if game.is_team_side(game.get_ball_position(), self.my_team) and \
                game.get_player_at(game.get_ball_position()) is None:
            for player in game.get_players_on_pitch(self.my_team, up=True):
                if Skill.BLOCK in player.get_skills() and game.num_tackle_zones_in(player) == 0:
                    return Action(ActionType.SELECT_PLAYER, player=player, position=ball_pos)
        return Action(ActionType.SELECT_NONE)

    def touchback(self, game):
        """
        Select player to give the ball to.
        """
        p = None
        for player in game.get_players_on_pitch(self.my_team, up=True):
            if Skill.BLOCK in player.get_skills():
                return Action(ActionType.SELECT_PLAYER, player=player)
            p = player
        return Action(ActionType.SELECT_PLAYER, player=p)

    def turn(self, game):
        """
        Start a new player action.
        """
        # Update teams
        self.my_team = game.get_team_by_id(self.my_team.team_id)
        self.opp_team = game.get_opp_team(self.my_team)

        # Reset actions if new turn
        turn = game.get_agent_team(self).state.turn
        half = game.state.half
        if half > self.last_half or turn > self.last_turn:
            self.actions.clear()
            self.last_turn = turn
            self.last_half = half
            self.actions = []
            #print(f"Half: {half}")
            #print(f"Turn: {turn}")

        # End turn if only action left
        if len(game.state.available_actions) == 1:
            if game.state.available_actions[0].action_type == ActionType.END_TURN:
                self.actions = [Action(ActionType.END_TURN)]

        # Execute planned actions if any
        while len(self.actions) > 0:
            action = self._get_next_action()
            if game._is_action_allowed(action):
                return action

        # Split logic depending on offense, defense, and loose ball - and plan actions
        ball_carrier = game.get_ball_carrier()
        #hacer el orden aleatorio de funciones, reciclar para OSLA
        #si ya existe pues reusar
        #aqui hacer  lo del FM
        #self._random_orden_operaciones()
        self._make_plan(game, ball_carrier)
        action = self._get_next_action()
        return action

    def _get_next_action(self):
        action = self.actions[0]
        self.actions = self.actions[1:]
        #print(f"Action: {action.to_json()}")
        return action

    def _make_plan(self, game: botbowl.Game, ball_carrier):
        # estrategia 1
        # self._strategy_one(game, ball_carrier)

        #mirar si ya tenemos la combinación idonea para este turno
        if (self.orden_operaciones == []):
            # trasteo random
            # self.orden_operaciones = self._random_orden_operaciones()
            self.orden_operaciones = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            # self.orden_operaciones = [7, 5, 3, 2, 0, 1, 9, 8, 4, 6]

            # estrategia OSLA
            # self.orden_operaciones = self._act_in_game_copy(game, ball_carrier, TIME_THINKING)

        #print(self.orden_operaciones)

        #añadir acciones a self.acciones
        self.index_operacion = 0
        actions = []
        actions = self._check_index_operacion_in_range(game, ball_carrier)

        while actions is None:
            self.index_operacion += 1
            actions = self._check_index_operacion_in_range(game, ball_carrier)

        self._add_actions(actions)

    def _act_in_game_copy(self, game, ball_carrier, budget):
        """
        Does an OSLA
        :Returns: The List of index of functions that must be called in that order
        """
        initial_time = time.time()
        time_difference = budget * 0.9

        combinations_evaluations_map = {}

        game_copy = deepcopy(game)
        game_copy.enable_forward_model()
        game_copy.home_agent.human = True
        game_copy.away_agent.human = True

        my_team_copy = None
        opp_team_copy = None

        home_team = game_copy.get_agent_team(game_copy.home_agent)
        away_team = game_copy.get_agent_team(game_copy.away_agent)

        if home_team == self.my_team:
            my_team_copy = home_team
            opp_team_copy = away_team
            i_am_home = True
        else:
            my_team_copy = away_team
            opp_team_copy = home_team
            i_am_home = False

        root_step = game_copy.get_step()

        best_combination = None

        first_check = True

        # bucle para el OSLA
        while time.time() - initial_time < time_difference:

            # generar nueva combinacion de acciones
            if first_check:
                nueva_combinacion_operaciones = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                first_check = False
            else:
                # nueva_combinacion_operaciones = self._random_orden_operaciones()
                nueva_combinacion_operaciones = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

            #guardar score antes de actuar
            if i_am_home:
                prev_score = game_copy.state.home_team.state.score
            else:
                prev_score = game_copy.state.away_team.state.score

            # ejecutar la combinacion en el game_copy
            for operation in nueva_combinacion_operaciones:
                # Update teams
                my_team_copy = game_copy.get_team_by_id(my_team_copy.team_id)
                opp_team_copy = game_copy.get_opp_team(my_team_copy)

                #Esto lo he puesto porque me ha salido un error que no me había salido antes de que en cierto daba error porque el tamaño de available_actions es 0
                #entonces cuando sea, será END_TURN si no entiendo mal la logica del juego, y que acabe la combinación
                # End turn if only action left
                if len(game_copy.state.available_actions) == 1:
                    if game_copy.state.available_actions[0].action_type == ActionType.END_TURN:
                        game_copy.step(Action(ActionType.END_TURN))
                        break

                #parche para evitar que salga el AsssertionError
                if game_copy.active_team == my_team_copy:
                    actual_actions = self._strategy_random(game_copy, game_copy.get_ball_carrier(), operation, my_team_copy, opp_team_copy)

                    if actual_actions is not None:
                        for action in actual_actions:
                            if game_copy._is_action_allowed(action):
                                game_copy.step(action)

                        # estas 2 lineas las he copiado tal cual, no se exactamente como funcionan
                        while not game.state.game_over and len(game.state.available_actions) == 0:
                            game_copy.step()

            # insertar la combinacion al mapa de combinacion-evaluacion
            tuplaOperaciones = tuple(nueva_combinacion_operaciones)
            combination_score = self._evaluate(game_copy, my_team_copy, opp_team_copy, prev_score, i_am_home)
            # combination_score = self.simple_heuristic_casero(game_copy, my_team_copy)
            # print(str(tuplaOperaciones) + ": " + str(combination_score))
            combinations_evaluations_map[hash(tuplaOperaciones)] = combination_score
            # Y comprobar si es mejor que la previa mejor combinacion
            if best_combination is None or combination_score > combinations_evaluations_map[hash(best_combination)]:
                best_combination = tuplaOperaciones

            # revertir los cambios
            game_copy.revert(root_step)

        print(best_combination)
        return best_combination

    def simple_heuristic_casero(self, game, my_team):
        own_team = my_team
        opp_team = game.get_opp_team(own_team)
        own_score = own_team.state.score
        opp_score = opp_team.state.score
        own_kos = len(game.get_knocked_out(own_team))
        opp_kos = len(game.get_knocked_out(opp_team))
        own_cas = len(game.get_casualties(own_team))
        opp_cas = len(game.get_casualties(opp_team))
        own_stunned = len([p for p in game.get_players_on_pitch(own_team, up=False) if p.state.stunned])
        opp_stunned = len([p for p in game.get_players_on_pitch(opp_team, up=False) if p.state.stunned])
        own_down = len([p for p in game.get_players_on_pitch(own_team, up=False) if not p.state.stunned])
        opp_down = len([p for p in game.get_players_on_pitch(opp_team, up=False) if not p.state.stunned])
        own_ejected = len(game.get_dungeon(own_team))
        opp_ejected = len(game.get_dungeon(opp_team))
        own_has_ball = False
        opp_has_ball = False
        ball_carrier = game.get_ball_carrier()
        if ball_carrier is not None:
            own_has_ball = 1 if ball_carrier.team == own_team else 0
            opp_has_ball = 1 if ball_carrier.team == opp_team else 0
        own = own_score / 10 + own_has_ball / 20 - (
                    own_cas + own_ejected) / 30 - own_kos / 50 - own_stunned / 100 - own_down / 200
        opp = opp_score / 10 + opp_has_ball / 20 - (
                    opp_cas + opp_ejected) / 30 - opp_kos / 50 - opp_stunned / 100 - opp_down / 200
        if game.state.game_over:
            if game.get_winning_team() == my_team:
                own += 0.1
            elif game.get_winner() is None:
                opp += 0.1
        return 0.5 + own - opp

    def _evaluate(self, game, my_team, opp_team, prev_score, i_am_home):
        puntos = 0

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
        if aux_ball_position is not None:   #comprobar que estamos en un estado con bola en el campo
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

        #mirar si hemos marcado gol
        marcar_gol_points = 50
        if i_am_home:
            if prev_score < game.state.home_team.state.score:
                puntos += marcar_gol_points
        else:
            if prev_score < game.state.away_team.state.score:
                puntos += marcar_gol_points

        return puntos

    def _random_orden_operaciones(self):
        """
        Funcion que devuelve una List<Int> que indica el orden aleatoria para las funciones de la estrategia
        """
        i = 0
        orden = []
        while i < self.n_operaciones:
            a_meter = random.randint(0, self.n_operaciones - 1)
            if not a_meter in orden:
                orden.append(a_meter)
                i += 1

        return orden

    def _strategy_one(self, game: botbowl.Game, ball_carrier):
        # print("1. Stand up marked players")
        actions_to_append = self._stand_up_marked_players(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("2. Move ball carrier to endzone")
        actions_to_append = self._move_ball_carrier_to_endzone(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("3. Safe blocks")
        actions_to_append = self._safe_blocks(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("4. Pickup ball")
        actions_to_append = self._pickup_ball(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("5. Move receivers into scoring distance if not already")
        actions_to_append = self._move_receivers_into_scoring_distance(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("6. Blitz with open block players")
        actions_to_append = self._blitz_with_open_block_players(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("7. Make cage around ball carrier")
        actions_to_append = self._make_cage_around_ball_player(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("8. Move non-marked players to assist")
        actions_to_append = self._scan_for_assist_positons(game, ball_carrier, self.my_team, self.opp_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("9. Move towards the ball")
        actions_to_append = self._move_towards_the_ball(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("10. Risky blocks")
        actions_to_append = self._risky_blocks(game, ball_carrier, self.my_team)
        if actions_to_append is not None:
            self._add_actions(actions_to_append)
            return

        # print("11. End turn")
        actions_to_append = []
        actions_to_append.append(self._end_turn(game, ball_carrier))
        self._add_actions(actions_to_append)

    def _strategy_random(self, game: botbowl.Game, ball_carrier, num_function, my_team, opp_team):
        """
        Pass the actions

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :param num_function: the number of the function that you want to do
        :returns: The list of actions of that function
        """
        actions = []
        #for i in self.orden_operaciones:
        if num_function == 0:
            actions = self._stand_up_marked_players(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        elif num_function == 1:
            actions = self._move_ball_carrier_to_endzone(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        elif num_function == 2:
            actions = self._safe_blocks(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        elif num_function == 3:
            actions = self._pickup_ball(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        elif num_function == 4:
            actions = self._move_receivers_into_scoring_distance(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        elif num_function == 5:
            actions = self._blitz_with_open_block_players(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        elif num_function == 6:
            actions = self._make_cage_around_ball_player(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        elif num_function == 7:
            actions = self._scan_for_assist_positons(game, ball_carrier, my_team, opp_team)
            if actions is not None:
                return actions
        elif num_function == 8:
            actions = self._move_towards_the_ball(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        elif num_function == 9:
            actions = self._risky_blocks(game, ball_carrier, my_team)
            if actions is not None:
                return actions
        else:
            actions.append(self._end_turn(game, ball_carrier))
            #print("Fuera de rango -> End_turn")
            return actions

        #self._end_turn(game, ball_carrier)

    def _check_index_operacion_in_range(self, game, ball_carrier):
        """
        Checks if self.index_operacion is inside the range of len(self.orden_operaciones)
        :return: The actions of self.strategy_random with this index
        """
        actions = []
        if self.index_operacion >= len(self.orden_operaciones):
            actions = self._strategy_random(game, ball_carrier, self.index_operacion, self.my_team, self.opp_team)   #end_turn
            self.index_operacion = 0    #reiniciar para el siguiente turno
            self.orden_operaciones = [] #reiniciar para el siguiente turno y así calcular una nueva combinacion
        else:
            actions = self._strategy_random(game, ball_carrier, self.orden_operaciones[self.index_operacion], self.my_team, self.opp_team)

        return actions

    def _add_actions(self, list_actions):
        """
        Add the actions of the list to self.actions
        """
        for action in list_actions:
            self.actions.append(action)

    #region Strategy Functions
    #He puesto que cada funcion que necesita leer de open_players lo calcule internamente en vez de pasarle el array
    #Esto para poder hacer las funciones en distinto orden sin que el array esté mal
    def _stand_up_marked_players(self, game: botbowl.Game, ball_carrier, my_team):
        """Stand up marked players

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if there is any action available, otherwise None
        """
        for player in my_team.players:
            if player.position is not None and not player.state.up and not player.state.stunned and not player.state.used:
                if game.num_tackle_zones_in(player) > 0:
                    #self.actions.append(Action(ActionType.START_MOVE, player=player))
                    #self.actions.append(Action(ActionType.STAND_UP))
                    actions = []
                    actions.append(Action(ActionType.START_MOVE, player=player))
                    actions.append(Action(ActionType.STAND_UP))
                    return actions

        return None

    def _move_ball_carrier_to_endzone(self, game: botbowl.Game, ball_carrier, my_team):
        """Try to move the ball_carrier to the endzone
        First, it checks if the ball_carrier has high probability (70%)
        If not, Hand-off action to scoring player
        Else, Move safely towards the endzone

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions is any action available, otherwise None
        """
        actions = None
        if ball_carrier is not None and ball_carrier.team == my_team and not ball_carrier.state.used:
            # print("2.1 Can ball carrier score with high probability")
            td_path = pf.get_safest_path_to_endzone(game, ball_carrier, allow_team_reroll=True)
            if td_path is not None and td_path.prob >= 0.7:
                #self.actions.append(Action(ActionType.START_MOVE, player=ball_carrier))
                #self.actions.extend(path_to_move_actions(game, ball_carrier, td_path))
                actions = []
                actions.append(Action(ActionType.START_MOVE, player=ball_carrier))
                actions.extend(path_to_move_actions(game, ball_carrier, td_path))

                return actions

            # print("2.2 Hand-off action to scoring player")
            if game.is_handoff_available():

                # Get players in scoring range
                unused_teammates = []
                for player in my_team.players:
                    if player.position is not None and player != ball_carrier and not player.state.used and player.state.up:
                        unused_teammates.append(player)

                # Find other players in scoring range
                handoff_p = None
                handoff_path = None
                for player in unused_teammates:
                    if game.get_distance_to_endzone(player) > player.num_moves_left():
                        continue
                    td_path = pf.get_safest_path_to_endzone(game, player, allow_team_reroll=True)
                    if td_path is None:
                        continue
                    handoff_path = pf.get_safest_path(game, ball_carrier, player.position, allow_team_reroll=True)
                    if handoff_path is None:
                        continue
                    p_catch = game.get_catch_prob(player, handoff=True, allow_catch_reroll=True, allow_team_reroll=True)
                    p = td_path.prob * handoff_path.prob * p_catch
                    if handoff_p is None or p > handoff_p:
                        handoff_p = p
                        handoff_path = handoff_path

                # Hand-off if high probability or last turn
                if handoff_path is not None and (handoff_p >= 0.7 or my_team.state.turn == 8):
                    #self.actions.append(Action(ActionType.START_HANDOFF, player=ball_carrier))
                    #self.actions.extend(path_to_move_actions(game, ball_carrier, handoff_path))
                    actions = []
                    actions.append(Action(ActionType.START_HANDOFF, player=ball_carrier))
                    actions.extend(path_to_move_actions(game, ball_carrier, handoff_path))

                    return actions

            # print("2.3 Move safely towards the endzone")
            if game.num_tackle_zones_in(ball_carrier) == 0:
                paths = pf.get_all_paths(game, ball_carrier)
                best_path = None
                best_distance = 100
                target_x = game.get_opp_endzone_x(my_team)
                for path in paths:
                    distance_to_endzone = abs(target_x - path.steps[-1].x)
                    if path.prob == 1 and (
                            best_path is None or distance_to_endzone < best_distance) and game.num_tackle_zones_at(
                            ball_carrier, path.get_last_step()) == 0:
                        best_path = path
                        best_distance = distance_to_endzone
                if best_path is not None:
                    #self.actions.append(Action(ActionType.START_MOVE, player=ball_carrier))
                    #self.actions.extend(path_to_move_actions(game, ball_carrier, best_path))
                    actions = []
                    actions.append(Action(ActionType.START_MOVE, player=ball_carrier))
                    actions.extend(path_to_move_actions(game, ball_carrier, best_path))

                    return actions

            return None

    def _safe_blocks(self, game: botbowl.Game, ball_carrier, my_team):
        """Check if the safest block is safe enough

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if it is safe enough, otherwise None
        """
        attacker, defender, p_self_up, p_opp_down, block_p_fumble_self, block_p_fumble_opp = self._get_safest_block(
            game, my_team)
        if attacker is not None and p_self_up > 0.94 and block_p_fumble_self == 0:
            #self.actions.append(Action(ActionType.START_BLOCK, player=attacker))
            #self.actions.append(Action(ActionType.BLOCK, position=defender.position))
            actions = []
            actions.append(Action(ActionType.START_BLOCK, player=attacker))
            actions.append(Action(ActionType.BLOCK, position=defender.position))

            return actions

        return None

    def _pickup_ball(self, game: botbowl.Game, ball_carrier, my_team):
        """Try to pick up the ball if there is no ball_carrier

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if it is possible to pick it up, otherwise None
        """
        actions = []
        if game.get_ball_carrier() is None:
            pickup_p = None
            pickup_player = None
            pickup_path = None
            for player in my_team.players:
                if player.position is not None and not player.state.used:
                    if player.position.distance(game.get_ball_position()) <= player.get_ma() + 2:
                        path = pf.get_safest_path(game, player, game.get_ball_position())
                        if path is not None:
                            p = path.prob
                            if pickup_p is None or p > pickup_p:
                                pickup_p = p
                                pickup_player = player
                                pickup_path = path
            if pickup_player is not None and pickup_p > 0.33:
                #self.actions.append(Action(ActionType.START_MOVE, player=pickup_player))
                #self.actions.extend(path_to_move_actions(game, pickup_player, pickup_path))
                actions.append(Action(ActionType.START_MOVE, player=pickup_player))
                actions.extend(path_to_move_actions(game, pickup_player, pickup_path))

                # Find safest path towards endzone
                if game.num_tackle_zones_at(pickup_player, game.get_ball_position()) == 0 and game.get_opp_endzone_x(
                        my_team) != game.get_ball_position().x:
                    paths = pf.get_all_paths(game, pickup_player, from_position=game.get_ball_position(),
                                             num_moves_used=len(pickup_path))
                    best_path = None
                    best_distance = 100
                    target_x = game.get_opp_endzone_x(my_team)
                    for path in paths:
                        distance_to_endzone = abs(target_x - path.steps[-1].x)
                        if path.prob == 1 and (
                                best_path is None or distance_to_endzone < best_distance) and game.num_tackle_zones_at(
                                pickup_player, path.get_last_step()) == 0:
                            best_path = path
                            best_distance = distance_to_endzone
                    if best_path is not None:
                        #self.actions.extend(path_to_move_actions(game, pickup_player, best_path, do_assertions=False))
                        actions.extend(path_to_move_actions(game, pickup_player, best_path, do_assertions=False))

                return actions

        return None

    def _move_receivers_into_scoring_distance(self, game: botbowl.Game, ball_carrier, my_team):
        """Check how many open_players there are and move them if they can CATCH and if it is possible

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if it is possible, otherwise None
        """
        # Scan for unused players that are not marked
        open_players = []
        for player in my_team.players:
            if player.position is not None and not player.state.used and game.num_tackle_zones_in(player) == 0:
                open_players.append(player)

        for player in open_players:
            if player.has_skill(Skill.CATCH) and player != ball_carrier:
                if game.get_distance_to_endzone(player) > player.num_moves_left():
                    continue
                paths = pf.get_all_paths(game, player)
                best_path = None
                best_distance = 100
                target_x = game.get_opp_endzone_x(my_team)
                for path in paths:
                    distance_to_endzone = abs(target_x - path.steps[-1].x)
                    if path.prob == 1 and (
                            best_path is None or distance_to_endzone < best_distance) and game.num_tackle_zones_at(
                            player, path.get_last_step()):
                        best_path = path
                        best_distance = distance_to_endzone
                if best_path is not None:
                    #self.actions.append(Action(ActionType.START_MOVE, player=player))
                    #self.actions.extend(path_to_move_actions(game, player, best_path))
                    actions = []
                    actions.append(Action(ActionType.START_MOVE, player=player))
                    actions.extend(path_to_move_actions(game, player, best_path))

                    return actions

        return None

    def _blitz_with_open_block_players(self, game: botbowl.Game, ball_carrier, my_team):
        """Try to Blitz

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if it is possible, otherwise None
        """
        # Scan for unused players that are not marked
        open_players = []
        for player in my_team.players:
            if player.position is not None and not player.state.used and game.num_tackle_zones_in(player) == 0:
                open_players.append(player)

        if game.is_blitz_available():

            best_blitz_attacker = None
            best_blitz_defender = None
            best_blitz_score = None
            best_blitz_path = None
            for blitzer in open_players:
                if blitzer.position is not None and not blitzer.state.used and blitzer.has_skill(Skill.BLOCK):
                    blitz_paths = pf.get_all_paths(game, blitzer, blitz=True)
                    for path in blitz_paths:
                        defender = game.get_player_at(path.get_last_step())
                        if defender is None:
                            continue
                        from_position = path.steps[-2] if len(path.steps) > 1 else blitzer.position
                        p_self, p_opp, p_fumble_self, p_fumble_opp = game.get_blitz_probs(blitzer, from_position,
                                                                                          defender)
                        p_self_up = path.prob * (1 - p_self)
                        p_opp = path.prob * p_opp
                        p_fumble_opp = p_fumble_opp * path.prob
                        if blitzer == game.get_ball_carrier():
                            p_fumble_self = path.prob + (1 - path.prob) * p_fumble_self
                        score = p_self_up + p_opp + p_fumble_opp - p_fumble_self
                        if best_blitz_score is None or score > best_blitz_score:
                            best_blitz_attacker = blitzer
                            best_blitz_defender = defender
                            best_blitz_score = score
                            best_blitz_path = path
            if best_blitz_attacker is not None and best_blitz_score >= 1.25:
                #self.actions.append(Action(ActionType.START_BLITZ, player=best_blitz_attacker))
                #self.actions.extend(path_to_move_actions(game, best_blitz_attacker, best_blitz_path))
                actions = []
                actions.append(Action(ActionType.START_BLITZ, player=best_blitz_attacker))
                actions.extend(path_to_move_actions(game, best_blitz_attacker, best_blitz_path))

                return actions

        return None

    def _make_cage_around_ball_player(self, game: botbowl.Game, ball_carrier, my_team):
        """Try to make a cage around the ball_carrier

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if it is possible, otherwise None
        """
        # Scan for unused players that are not marked
        open_players = []
        for player in my_team.players:
            if player.position is not None and not player.state.used and game.num_tackle_zones_in(player) == 0:
                open_players.append(player)

        aux_ball_position = game.get_ball_position()
        if aux_ball_position is not None:  # comprobar que estamos en un estado con bola en el campo
            cage_positions = [
                Square(aux_ball_position.x - 1, aux_ball_position.y - 1),
                Square(aux_ball_position.x + 1, aux_ball_position.y - 1),
                Square(aux_ball_position.x - 1, aux_ball_position.y + 1),
                Square(aux_ball_position.x + 1, aux_ball_position.y + 1)
            ]
            if ball_carrier is not None:
                for cage_position in cage_positions:
                    if game.get_player_at(cage_position) is None and not game.is_out_of_bounds(cage_position):
                        for player in open_players:
                            if player == ball_carrier or player.position in cage_positions:
                                continue
                            if player.position.distance(cage_position) > player.num_moves_left():
                                continue
                            if game.num_tackle_zones_in(player) > 0:
                                continue
                            path = pf.get_safest_path(game, player, cage_position)
                            if path is not None and path.prob > 0.94:
                                #self.actions.append(Action(ActionType.START_MOVE, player=player))
                                #self.actions.extend(path_to_move_actions(game, player, path))
                                actions = []
                                actions.append(Action(ActionType.START_MOVE, player=player))
                                actions.extend(path_to_move_actions(game, player, path))

                                return actions

        return None

    def _scan_for_assist_positons(self, game: botbowl.Game, ball_carrier, my_team, opp_team):
        """Calculate the assist_positions and try to put the open_players there

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if it is possible, otherwise None
        """
        # Scan for unused players that are not marked
        open_players = []
        for player in my_team.players:
            if player.position is not None and not player.state.used and game.num_tackle_zones_in(player) == 0:
                open_players.append(player)

        # Scan for assist positions
        assist_positions = set()
        for player in game.get_opp_team(my_team).players:
            if player.position is None or not player.state.up:
                continue
            for opponent in game.get_adjacent_opponents(player, down=False):
                att_str, def_str = game.get_block_strengths(player, opponent)
                if def_str >= att_str:
                    for open_position in game.get_adjacent_squares(player.position, occupied=False):
                        if len(game.get_adjacent_players(open_position, team=opp_team, down=False)) == 1:
                            assist_positions.add(open_position)

        for player in open_players:
            for path in pf.get_all_paths(game, player):
                if path.prob < 1.0 or path.get_last_step() not in assist_positions:
                    continue
                #self.actions.append(Action(ActionType.START_MOVE, player=player))
                #self.actions.extend(path_to_move_actions(game, player, path))
                actions = []
                actions.append(Action(ActionType.START_MOVE, player=player))
                actions.extend(path_to_move_actions(game, player, path))

                return actions

        return None

    def _move_towards_the_ball(self, game: botbowl.Game, ball_carrier, my_team):
        """Move the open_players towards the ball

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if it is possible, otherwise None
        """
        # Scan for unused players that are not marked
        open_players = []
        for player in my_team.players:
            if player.position is not None and not player.state.used and game.num_tackle_zones_in(player) == 0:
                open_players.append(player)

        for player in open_players:
            if player == ball_carrier or game.num_tackle_zones_in(player) > 0:
                continue

            shortest_distance = None
            path = None

            if ball_carrier is None:
                for p in pf.get_all_paths(game, player):
                    distance = p.get_last_step().distance(game.get_ball_position())
                    if shortest_distance is None or (p.prob == 1 and distance < shortest_distance):
                        shortest_distance = distance
                        path = p
            elif ball_carrier.team != my_team:
                for p in pf.get_all_paths(game, player):
                    distance = p.get_last_step().distance(ball_carrier.position)
                    if shortest_distance is None or (p.prob == 1 and distance < shortest_distance):
                        shortest_distance = distance
                        path = p

            if path is not None:
                #self.actions.append(Action(ActionType.START_MOVE, player=player))
                #self.actions.extend(path_to_move_actions(game, player, path))
                actions = []
                actions.append(Action(ActionType.START_MOVE, player=player))
                actions.extend(path_to_move_actions(game, player, path))

                return actions

        return None

    def _risky_blocks(self, game: botbowl.Game, ball_carrier, my_team):
        """Try to do risky blocks

        :param game: the Game itself
        :param ball_carrier: who is carrying the ball
        :returns: The list of actions if it is possible, otherwise None
        """
        attacker, defender, p_self_up, p_opp_down, block_p_fumble_self, block_p_fumble_opp = self._get_safest_block(
            game, my_team)
        if attacker is not None and (p_opp_down > (1 - p_self_up) or block_p_fumble_opp > 0):
            #self.actions.append(Action(ActionType.START_BLOCK, player=attacker))
            #self.actions.append(Action(ActionType.BLOCK, position=defender.position))
            actions = []
            actions.append(Action(ActionType.START_BLOCK, player=attacker))
            actions.append(Action(ActionType.BLOCK, position=defender.position))

            return actions

        return None

    def _end_turn(self, game: botbowl.Game, ball_carrier):
        """
        returns: Action(ActionType.END_TURN)
        """
        #self.actions.append(Action(ActionType.END_TURN))
        return Action(ActionType.END_TURN)

    #endregion

    def _get_safest_block(self, game, my_team):
        block_attacker = None
        block_defender = None
        block_p_self_up = None
        block_p_opp_down = None
        block_p_fumble_self = None
        block_p_fumble_opp = None
        for attacker in my_team.players:
            if attacker.position is not None and not attacker.state.used and attacker.state.up:
                for defender in game.get_adjacent_opponents(attacker, down=False):
                    p_self, p_opp, p_fumble_self, p_fumble_opp = game.get_block_probs(attacker, defender)
                    p_self_up = (1-p_self)
                    if block_p_self_up is None or (p_self_up > block_p_self_up and p_opp >= p_fumble_self):
                        block_p_self_up = p_self_up
                        block_p_opp_down = p_opp
                        block_attacker = attacker
                        block_defender = defender
                        block_p_fumble_self = p_fumble_self
                        block_p_fumble_opp = p_fumble_opp
        return block_attacker, block_defender, block_p_self_up, block_p_opp_down, block_p_fumble_self, block_p_fumble_opp

    def quick_snap(self, game):
        return Action(ActionType.END_TURN)

    def blitz(self, game):
        return Action(ActionType.END_TURN)

    def player_action(self, game):
        # Execute planned actions if any
        while len(self.actions) > 0:
            action = self._get_next_action()
            if game._is_action_allowed(action):
                return action

        ball_carrier = game.get_ball_carrier()
        if ball_carrier == game.get_active_player():
            td_path = pf.get_safest_path_to_endzone(game, ball_carrier)
            if td_path is not None and td_path.prob <= 0.9:
                self.actions.extend(path_to_move_actions(game, ball_carrier, td_path))
                #print(f"Scoring with {ball_carrier.role.name}, p={td_path.prob}")
                return self._get_next_action()
        return Action(ActionType.END_PLAYER_TURN)

    def block(self, game):
        """
        Select block die or reroll.
        """
        # Get attacker and defender
        attacker = game.get_procedure().attacker
        defender = game.get_procedure().defender
        is_blitz = game.get_procedure().blitz
        dice = game.num_block_dice(attacker, defender, blitz=is_blitz)

        # Loop through available dice results
        actions = set()
        for action_choice in game.state.available_actions:
            actions.add(action_choice.action_type)

        # 1. DEFENDER DOWN
        if ActionType.SELECT_DEFENDER_DOWN in actions:
            return Action(ActionType.SELECT_DEFENDER_DOWN)

        if ActionType.SELECT_DEFENDER_STUMBLES in actions and not (defender.has_skill(Skill.DODGE) and not attacker.has_skill(Skill.TACKLE)):
            return Action(ActionType.SELECT_DEFENDER_STUMBLES)

        if ActionType.SELECT_BOTH_DOWN in actions and not defender.has_skill(Skill.BLOCK) and attacker.has_skill(Skill.BLOCK):
            return Action(ActionType.SELECT_BOTH_DOWN)

        # 2. BOTH DOWN if opponent carries the ball and doesn't have block
        if ActionType.SELECT_BOTH_DOWN in actions and game.get_ball_carrier() == defender and not defender.has_skill(Skill.BLOCK):
            return Action(ActionType.SELECT_BOTH_DOWN)

        # 3. USE REROLL if defender carries the ball
        if ActionType.USE_REROLL in actions and game.get_ball_carrier() == defender:
            return Action(ActionType.USE_REROLL)

        # 4. PUSH
        if ActionType.SELECT_DEFENDER_STUMBLES in actions:
            return Action(ActionType.SELECT_DEFENDER_STUMBLES)

        if ActionType.SELECT_PUSH in actions:
            return Action(ActionType.SELECT_PUSH)

        # 5. BOTH DOWN
        if ActionType.SELECT_BOTH_DOWN in actions:
            return Action(ActionType.SELECT_BOTH_DOWN)

        # 6. USE REROLL to avoid attacker down unless a one-die block
        if ActionType.USE_REROLL in actions and dice > 1:
            return Action(ActionType.USE_REROLL)

        # 7. ATTACKER DOWN
        if ActionType.SELECT_ATTACKER_DOWN in actions:
            return Action(ActionType.SELECT_ATTACKER_DOWN)

    def push(self, game):
        """
        Select square to push to.
        """
        # Loop through available squares
        for position in game.state.available_actions[0].positions:
            return Action(ActionType.PUSH, position=position)

    def follow_up(self, game):
        """
        Follow up or not. ActionType.FOLLOW_UP must be used together with a position.
        """
        player = game.state.active_player
        for position in game.state.available_actions[0].positions:
            # Always follow up
            if player.position != position:
                return Action(ActionType.FOLLOW_UP, position=position)

    def apothecary(self, game):
        """
        Use apothecary?
        """
        return Action(ActionType.USE_APOTHECARY)
        # return Action(ActionType.DONT_USE_APOTHECARY)

    def interception(self, game):
        """
        Select interceptor.
        """
        for action in game.state.available_actions:
            if action.action_type == ActionType.SELECT_PLAYER:
                for player, rolls in zip(action.players, action.rolls):
                    return Action(ActionType.SELECT_PLAYER, player=player)
        return Action(ActionType.SELECT_NONE)

    def pass_action(self, game):
        """
        Reroll or not.
        """
        return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def catch(self, game):
        """
        Reroll or not.
        """
        return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def gfi(self, game):
        """
        Reroll or not.
        """
        return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def dodge(self, game):
        """
        Reroll or not.
        """
        return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def pickup(self, game):
        """
        Reroll or not.
        """
        return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def use_juggernaut(self, game):
        return Action(ActionType.USE_SKILL)
        # return Action(ActionType.DONT_USE_SKILL)

    def use_wrestle(self, game):
        return Action(ActionType.USE_SKILL)
        # return Action(ActionType.DONT_USE_SKILL)

    def use_stand_firm(self, game):
        return Action(ActionType.USE_SKILL)
        # return Action(ActionType.DONT_USE_SKILL)

    def use_pro(self, game):
        return Action(ActionType.USE_SKILL)
        # return Action(ActionType.DONT_USE_SKILL)

    def use_bribe(self, game):
        return Action(ActionType.USE_BRIBE)

    def blood_lust_block_or_move(self, game):
        return Action(ActionType.START_BLOCK)

    def eat_thrall(self, game):
        position = game.get_available_actions()[0].positions[0]
        return Action(ActionType.SELECT_PLAYER, position)

    def end_game(self, game):
        """
        Called when a game ends.
        """
        winner = game.get_winning_team()
        print("Casualties: ", game.num_casualties())
        if winner is None:
            print("It's a draw")
        elif winner == self.my_team:
            print("I ({}) won".format(self.name))
            print(self.my_team.state.score, "-", self.opp_team.state.score)
        else:
            print("I ({}) lost".format(self.name))
            print(self.my_team.state.score, "-", self.opp_team.state.score)


def path_to_move_actions(game: botbowl.Game, player: botbowl.Player, path: Path, do_assertions=True) -> List[Action]:
    """
    This function converts a path into a list of actions corresponding to that path.
    If you provide a handoff, foul or blitz path, then you have to manally set action type.
    :param game:
    :param player: player to move
    :param path: a path as returned by the pathfinding algorithms
    :param do_assertions: if False, it turns off the validation, can be helpful when the GameState will change before
                          this path is executed.
    :returns: List of actions corresponding to 'path'.
    """

    if path.block_dice is not None:
        action_type = ActionType.BLOCK
    elif path.handoff_roll is not None:
        action_type = ActionType.HANDOFF
    elif path.foul_roll is not None:
        action_type = ActionType.FOUL
    else:
        action_type = ActionType.MOVE

    active_team = game.state.available_actions[0].team
    player_at_target = game.get_player_at(path.get_last_step())

    if do_assertions:
        if action_type is ActionType.MOVE:
            assert player_at_target is None or player_at_target is game.get_active_player()
        elif action_type is ActionType.BLOCK:
            try:
                a = game.get_opp_team(active_team)
                assert a is player_at_target.team
            except:
                raise Exception("ojfowj")
            assert player_at_target.state.up
        elif action_type is ActionType.FOUL:
            assert game.get_opp_team(active_team) is player_at_target.team
            assert not player_at_target.state.up
        elif action_type is ActionType.HANDOFF:
            assert active_team is player_at_target.team
            assert player_at_target.state.up
        else:
            raise Exception(f"Unregonized action type {action_type}")

    final_action = Action(action_type, position=path.get_last_step())

    if game._is_action_allowed(final_action):
        return [final_action]
    else:
        actions = []
        if not player.state.up and path.steps[0] == player.position:
            actions.append(Action(ActionType.STAND_UP, player=player))
            actions.extend(Action(ActionType.MOVE, position=sq) for sq in path.steps[1:-1])
        else:
            actions.extend(Action(ActionType.MOVE, position=sq) for sq in path.steps[:-1])
        actions.append(final_action)
        return actions


# Register MyScriptedBot
botbowl.register_bot('first', MyScriptedBot2)


def main():
    # Load configurations, rules, arena and teams
    config = botbowl.load_config("bot-bowl")
    config.competition_mode = False
    config.pathfinding_enabled = True
    # config = get_config("gym-7.json")
    # config = get_config("gym-5.json")
    # config = get_config("gym-3.json")
    ruleset = botbowl.load_rule_set(config.ruleset, all_rules=False)  # We don't need all the rules
    arena = botbowl.load_arena(config.arena)
    home = botbowl.load_team_by_filename("human", ruleset)
    away = botbowl.load_team_by_filename("human", ruleset)

    num_games = 10
    wins = 0
    tds = 0
    # Play 10 games
    for i in range(num_games):
        home_agent = botbowl.make_bot('scripted')
        home_agent.name = "Scripted Bot"
        away_agent = botbowl.make_bot('random')
        away_agent.name = "Random Bot"
        config.debug_mode = False
        game = botbowl.Game(i, home, away, home_agent, away_agent, config, arena=arena, ruleset=ruleset)
        game.config.fast_mode = True

        print("Starting game", (i+1))
        start = time.time()
        game.init()
        end = time.time()
        print(end - start)

        wins += 1 if game.get_winning_team() is game.state.home_team else 0
        tds += game.state.home_team.state.score
    print(f"won {wins}/{num_games}")
    print(f"Own TDs per game={tds/num_games}")


if __name__ == "__main__":
    main()