import random

import pygame as pg

from EventManager import *
import Const

from math import sqrt
from copy import copy

class StateMachine(object):
    '''
    Manages a stack based state machine.
    peek(), pop() and push() perform as traditionally expected.
    peeking and popping an empty stack returns None.

    TL;DR. Just for game state recording.
    '''
    def __init__(self):
        self.statestack = []

    def peek(self):
        '''
        Returns the current state without altering the stack.
        Returns None if the stack is empty.
        '''
        try:
            return self.statestack[-1]
        except IndexError:
            # empty stack
            return None

    def pop(self):
        '''
        Returns the current state and remove it from the stack.
        Returns None if the stack is empty.
        '''
        try:
            return self.statestack.pop()
        except IndexError:
            # empty stack
            return None

    def push(self, state):
        '''
        Push a new state onto the stack.
        Returns the pushed value.
        '''
        self.statestack.append(state)
        return state

    def clear(self):
        '''
        Clear the stack.
        '''
        self.statestack = []


class GameEngine:
    '''
    The main game engine. The main loop of the game is in GameEngine.run()
    '''

    def __init__(self, ev_manager: EventManager):
        '''
        This function is called when the GameEngine is created.
        For more specific objects related to a game instance
            , they should be initialized in GameEngine.initialize()
        '''
        self.ev_manager = ev_manager
        ev_manager.register_listener(self)

        self.state_machine = StateMachine()

    def initialize(self):
        '''
        This method is called when a new game is instantiated.
        '''
        self.clock = pg.time.Clock()
        self.state_machine.push(Const.STATE_MENU)
        self.roll = [0, 1]
        self.players = [Player(self.roll[0]), Player(self.roll[1])]

    def notify(self, event: BaseEvent):
        '''
        Called by EventManager when a event occurs.
        '''
        if isinstance(event, EventInitialize):
            self.initialize()

        elif isinstance(event, EventEveryTick):
            # Peek the state of the game and do corresponding work
            cur_state = self.state_machine.peek()
            if cur_state == Const.STATE_MENU:
                self.update_menu()
            elif cur_state == Const.STATE_PLAY:
                self.update_objects()

                self.timer -= 1
                if self.timer == 0:
                    self.ev_manager.post(EventChangePosition())
            elif cur_state == Const.STATE_PLAY:
                pass
            elif cur_state == Const.STATE_ENDGAME:
                self.update_endgame()

        elif isinstance(event, EventStateChange):
            if event.state == Const.STATE_POP:
                if self.state_machine.pop() is None:
                    self.ev_manager.post(EventQuit())
            else:
                self.state_machine.push(event.state)

        elif isinstance(event, EventQuit):
            self.running = False

        elif isinstance(event, EventPlayerMove):
            self.players[event.player_id].move_direction(event.direction)
            self.check_collision()

        elif isinstance(event, EventTimesUp):
            self.state_machine.push(Const.STATE_ENDGAME)
        
        elif isinstance(event, EventPause):
            self.state_machine.push(Const.STATE_STOP)

        elif isinstance(event, EventContinue):
            self.state_machine.pop()

        elif isinstance(event, EventChangePosition):
            self.change_position()
    
    def change_position(self):
        self.roll[0], self.roll[1] = self.roll[1], self.roll[0]
        self.players = [Player(self.roll[0]), Player(self.roll[1])]
        self.timer = Const.GAME_LENGTH
    
    def distance(self, player1, player2):
        '''
        Calculate the distance between players
        '''
        return sqrt((player1.position.x - player2.position.x)**2 +
            (player1.position.y - player2.position.y)**2)

    def check_collision(self):
        '''
        If collision happens, quit the game
        '''
        if self.distance(self.players[0], self.players[1]) < 2 * Const.PLAYER_RADIUS:
            self.ev_manager.post(EventQuit()) 

    def update_menu(self):
        '''
        Update the objects in welcome scene.
        For example: game title, hint text
        '''
        pass

    def update_objects(self):
        '''
        Update the objects not controlled by user.
        For example: obstacles, items, special effects
        '''
        pass

    def update_endgame(self):
        '''
        Update the objects in endgame scene.
        For example: scoreboard
        '''
        pass

    def run(self):
        '''
        The main loop of the game is in this function.
        This function activates the GameEngine.
        '''
        self.running = True
        # Tell every one to start
        self.ev_manager.post(EventInitialize())
        self.timer = Const.GAME_LENGTH
        while self.running:
            self.ev_manager.post(EventEveryTick())
            self.clock.tick(Const.FPS)


class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.position = copy(Const.PLAYER_INIT_POSITION[player_id]) # is a pg.Vector2
        self.speed = Const.SPEED_ATTACK if player_id == 1 else Const.SPEED_DEFENSE

    def move_direction(self, direction: str):
        '''
        Move the player along the direction by its speed.
        Will automatically clip the position so no need to worry out-of-bound moving.
        '''
        # Modify position of player
        self.position += self.speed / Const.FPS * Const.DIRECTION_TO_VEC2[direction]

        # clipping
        self.position.x = max(0, min(Const.ARENA_SIZE[0], self.position.x))
        self.position.y = max(0, min(Const.ARENA_SIZE[1], self.position.y))
