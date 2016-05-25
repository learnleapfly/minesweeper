from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger
from random import choice
from itertools import product
from kivy.animation import Animation


###########################################################################

TOUCH_HOLD_THRESHOLD = 0.5

GAME_SIZE = 4
NUMBER_OF_BOMBS = 2


class GridSquare(Label):
    square_label = StringProperty('Z')

    def __init__(self, **kwargs):
        super(GridSquare, self).__init__(**kwargs)
        self.is_bomb = False
        self.guess_bomb = False
        self.is_hidden = True
        self.square_label = '.'
        self.bombs_nearby = 0
        self.coords = None

    def set_label(self):
        if self.guess_bomb:
            self.square_label = 'Bomb?'
        elif self.is_hidden:
            self.square_label = '.'
        elif self.is_bomb:
            self.square_label = 'BOOM'
            self.parent.parent.mainwindow.end_game('You Lose!')
        elif self.bombs_nearby > 0:
            self.square_label = str(self.bombs_nearby)
        else:
            self.square_label = ' '

    def reveal_square(self):
        if self.is_hidden:
            self.is_hidden = False
            self.set_label()
            if self.is_bomb is False and self.bombs_nearby == 0:
                for neighbour in self.parent.get_neighbours(self.coords):
                    neighbour.reveal_square()
            if self.parent.parent is not None:
                self.parent.parent.mainwindow.check_for_win()

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if Clock.get_time() - touch.time_start > TOUCH_HOLD_THRESHOLD:
                self.toggle_guess_bomb()
            else:
                self.reveal_square()
            return True

    def toggle_guess_bomb(self):
        self.guess_bomb = not self.guess_bomb
        self.set_label()
        if self.guess_bomb:
            self.parent.parent.mainwindow.num_bombs_left -= 1
        else:
            self.parent.parent.mainwindow.num_bombs_left += 1


class GameBoard(GridLayout):

    mainwindow = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(GameBoard, self).__init__(**kwargs)
        self.board_size = GAME_SIZE
        self.cols = GAME_SIZE
        self.grid_squares = {}
        for coords in product(xrange(0, self.board_size), xrange(0, self.board_size)):
            new_square = GridSquare()
            new_square.coords = coords
            self.grid_squares[coords] = new_square
            self.add_widget(new_square)
        self.scatter_bombs(NUMBER_OF_BOMBS)
        self.compute_all_bomb_counts()

    def get_neighbours(self, (row, col)):
        for coord in product(range(row-1, row+2), range(col-1, col+2)):
            if coord in self.grid_squares.keys() and coord != (row, col):
                yield self.grid_squares[coord]

    def scatter_bombs(self, num_bombs):
        for _ in xrange(0, num_bombs):
            coords = choice([(x, y) for x in range(0, self.board_size) for y in range(0, self.board_size)])
            self.grid_squares[coords].is_bomb = True

    def compute_all_bomb_counts(self):
        for coord in product(xrange(0, self.board_size), xrange(0, self.board_size)):
            grid_square = self.grid_squares[coord]
            grid_square.bombs_nearby = self.compute_bomb_count(coord)

    def compute_bomb_count(self, target):
        bomb_count = 0
        for neighbour in self.get_neighbours(target):
            if neighbour.is_bomb:
                bomb_count += 1
        return bomb_count


class MinesweeperGame(BoxLayout):

    num_bombs_left = NumericProperty(None)
    timer = NumericProperty(None)
    best_time = NumericProperty(None)
    winner_status = StringProperty('Unknown')

    def __init__(self, **kwargs):
        super(MinesweeperGame, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self.close, self)
        self._keyboard.bind(on_key_down=self.press)
        self.num_bombs_left = NUMBER_OF_BOMBS
        self.timer = 999
        self.start_time = Clock.get_time()
        self.best_time = 9999
        self.board = GameBoard()
        self.playing_area.add_widget(self.board)
        Clock.schedule_interval(self.timer_callback, 1.0)

    def timer_callback(self, _):
        self.timer = int(Clock.get_time() - self.start_time)

    def close(self):
        self._keyboard.unbind(on_key_down=self.press)
        self._keyboard = None
        App.get_running_app().stop()

    def reset_game(self, instance=None, value=None):
        Logger.info("reset: game")
        if self.board:
            self.playing_area.remove_widget(self.board)
        self.board = GameBoard()
        self.playing_area.add_widget(self.board)
        self.start_time = Clock.get_time()

    def press(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'escape':
            self.close()
        elif keycode[1] == 'r':
            self.reset_game()
        else:
            Logger.info("Unknown key: {}".format(keycode))
        return True

    def check_for_win(self):
        for gs in self.board.grid_squares.values():
            if gs.is_hidden and gs.is_bomb is False:
                return False
        self.end_game('You Win!')

    def end_game(self, status):
        self.winner_status = status
        if 'win' in status.lower() and self.timer < self.best_time:
            self.best_time = self.timer

        label = Label(text=status)
        animation = Animation(font_size=72, d=2)
        animation += Animation(font_size=0, d=1)
        self.playing_area.add_widget(label)
        animation.bind(on_complete=self.reset_game)
        animation.start(label)

###########################################################################
###########################################################################


class MinesweeperApp(App):
    def build(self):
        game = MinesweeperGame()
        game.reset_game()
        return game


if __name__ == '__main__':
    MinesweeperApp().run()
