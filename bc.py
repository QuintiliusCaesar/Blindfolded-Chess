import tkinter as tk
from tkinter import filedialog
from stockfish import Stockfish
import chess
import chess.svg
from PIL import Image, ImageTk
import io
from cairosvg import svg2png
import threading
import time
from chess import pgn
from voice import listen_for_move, parse_move

class BlindfoldedChessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blindfolded Chess")
        self.game_settings = {"difficulty": 3, "time_control": "5+0", "color": "White", "takebacks": True, "minutes": 0, "increment": 0}

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (WelcomeView, ModeSelectView, LoginPage, OnlineSetupView, ComputerSetupView, GameViewOnline, GameViewComputer):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(WelcomeView)

    def show_frame(self, page):
        frame = self.frames[page]
        frame.tkraise()

    def start_ai_game(self, difficulty=None, time_control=None, color=None, takebacks=None):
        
        if isinstance(time_control, str):
            try:
                minutes, increment = map(int, time_control.split("+"))
                self.game_settings['minutes'] = minutes
                self.game_settings['increment'] = increment
            except Exception:
                minutes, increment = 5, 0
        elif isinstance(time_control, tuple):
            minutes, increment = time_control
        else:
            minutes, increment = 5, 0

        
        if difficulty is None:
            difficulty = self.game_settings['difficulty']
        else:
            self.game_settings['difficulty'] = difficulty
        if time_control is None:
            time_control = self.game_settings['time_control']
        else:
            self.game_settings['time_control'] = time_control
        if color is None:
            color = self.game_settings['color']
        else:
            self.game_settings['color'] = color
        if takebacks is None:
            takebacks = self.game_settings['takebacks']
        else:
            self.game_settings['takebacks'] = takebacks

        

        time_control = (minutes, increment)
        game_frame = GameViewComputer(self.frames[GameViewComputer].master, self, self.game_settings['difficulty'],
                                      self.game_settings['time_control'], 
                                      self.game_settings['color'], 
                                      self.game_settings['takebacks'])
        self.frames[GameViewComputer] = game_frame
        game_frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(GameViewComputer)

# Welcome
class WelcomeView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Welcome to Blindfolded Chess")
        label.pack(pady=10)
        btn = tk.Button(self, text="Choose Mode", command=lambda: controller.show_frame(ModeSelectView))
        btn.pack()

# Mode Select
class ModeSelectView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Choose Game Mode")
        label.pack(pady=10)
        btn1 = tk.Button(self, text="Play Online", command=lambda: controller.show_frame(LoginPage))
        btn1.pack(pady=5)
        btn2 = tk.Button(self, text="Vs Computer", command=lambda: controller.show_frame(ComputerSetupView))
        btn2.pack(pady=5)
        btn_back = tk.Button(self, text="Back", command=lambda: controller.show_frame(WelcomeView))
        btn_back.pack()

# Login Page
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Login Page", font=("Helvetica", 16))
        label.pack(pady=10, padx=10)

        self.username_entry = tk.Entry(self)
        self.username_entry.pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        back_button = tk.Button(self, text="Back",
                                command=lambda: controller.show_frame(ModeSelectView))
        back_button.pack()

        login_button = tk.Button(self, text="Submit",
                                 command=lambda: controller.show_frame(OnlineSetupView))
        login_button.pack()

# Online Setup
class OnlineSetupView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Select Time Control (Online)")
        label.pack(pady=10)
        self.time_var = tk.StringVar(value="3+2")
        dropdown = tk.OptionMenu(self, self.time_var, "1+0", "3+0", "3+2", "5+3", "10+0")
        dropdown.pack(pady=5)
        btn_start = tk.Button(self, text="Start Online Game", command=lambda: controller.show_frame(GameViewOnline))
        btn_start.pack(pady=5)
        btn_back = tk.Button(self, text="Back", command=lambda: controller.show_frame(ModeSelectView))
        btn_back.pack()



# Computer Setup
class ComputerSetupView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Game Settings")
        label.pack(pady=10)

        tk.Label(self, text="Difficulty (1-15)").pack()
        self.diff_var = tk.StringVar(value="3")
        tk.Entry(self, textvariable=self.diff_var).pack(pady=5)

        tk.Label(self, text="Time Control").pack()
        self.time_var = tk.StringVar(value="5+3")
        tk.OptionMenu(self, self.time_var, "1+0", "3+0", "5+3", "10+0").pack(pady=5)

        tk.Label(self, text="Play as").pack()
        self.color_var = tk.StringVar(value="White")
        tk.OptionMenu(self, self.color_var, "White", "Black").pack(pady=5)

        tk.Label(self, text="Takebacks Allowed?").pack()
        self.takebacks_var = tk.StringVar(value="Yes")
        tk.OptionMenu(self, self.takebacks_var, "Yes", "No").pack(pady=5)

        btn_start = tk.Button(self, text="Start Game", command=lambda: controller.start_ai_game(
            int(self.diff_var.get()),
            time_control=self.time_var.get(),
            color=self.color_var.get(),
            takebacks=self.takebacks_var.get() == "Yes"))
        btn_start.pack(pady=5)
        btn_back = tk.Button(self, text="Back", command=lambda: controller.show_frame(ModeSelectView))
        btn_back.pack()

# Game Screen
class GameViewOnline(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Blindfolded Chess Game")
        label.pack(pady=10)

        self.moves_box = tk.Text(self, height=10, width=40)
        self.moves_box.insert("end", "Moves will appear here...\n")
        self.moves_box.pack(pady=5)

        tk.Label(self, text="Your Move (say or type):").pack()
        self.input_var = tk.StringVar()
        tk.Entry(self, textvariable=self.input_var).pack(pady=5)

        btn_resign = tk.Button(self, text="Resign", command=lambda: controller.show_frame(WelcomeView))
        btn_resign.pack(side="left", padx=10)
        btn_draw = tk.Button(self, text="Offer Draw", command=lambda: print("Draw offered"))
        btn_draw.pack(side="left", padx=10)

class GameViewComputer(tk.Frame):
    def __init__(self, parent, controller, difficulty=None, time_control=None, color=None, takebacks=None):
        super().__init__(parent)
        self.controller = controller
        if difficulty is None:
            self.difficulty = controller.game_settings['difficulty']
        else:
            self.difficulty = difficulty
        if time_control is None:
            self.time_control = controller.game_settings['time_control']
        else:
            self.time_control = time_control
        if color is None:
            self.color = controller.game_settings['color']
        else:
            self.color = color
        if takebacks is None:
            self.takebacks = controller.game_settings['takebacks']
        else:
            self.takebacks = takebacks

        self.board = chess.Board()

        self.stockfish = Stockfish(path="C:\stockfish\stockfish-windows-x86-64-avx2.exe", depth=15)
        self.stockfish.set_skill_level(self.difficulty)

        self.move_history = []

        # UI Elements
        self.label = tk.Label(self, text="Playing vs Stockfish")
        self.label.pack()

        self.board_label = tk.Label(self)
        self.board_label.pack()

        self.moves_box = tk.Text(self, height=10, width=40)
        self.moves_box.pack()

        self.move_var = tk.StringVar()
        tk.Entry(self, textvariable=self.move_var).pack()
        tk.Button(self, text="Submit Move", command=self.submit_move).pack()

        self.timer_white = tk.Label(self, text=f"White: {controller.game_settings['minutes']}:00")
        self.timer_white.pack(side="left", padx=5)
        self.timer_black = tk.Label(self, text=f"Black: {controller.game_settings['minutes']}:00")
        self.timer_black.pack(side="left", padx=5)

        self.takeback_btn = tk.Button(self, text="Takeback", command=self.takeback_move)
        self.takeback_btn.pack(side="left", padx=5)

        self.resign_btn = tk.Button(self, text="Resign", command=lambda: self.game_over("You Resigned"))
        self.resign_btn.pack(side="left", padx=5)

        # Timers
        self.white_time = controller.game_settings['minutes'] * 60
        self.black_time = controller.game_settings['minutes'] * 60

        self.update_board()
        self.playing_as_black()
        self.timer_running = False
        self.start_timers()

    def start_timers(self):
        if len(self.move_history) > 0:
            self.timer_running = True
            threading.Thread(target=self.run_timers, daemon=True).start()

    def game_over(self, result_text):
        self.timer_running = False  # Stop timers

        def export_pgn():
            pgn = chess.pgn.Game()
            board = chess.Board()
            node = pgn
            for move in self.move_history:
                try:
                    board.push_san(move)
                    node = node.add_variation(board.peek())
                except:
                    break
            pgn_text = str(pgn)

            file_path = filedialog.asksaveasfilename(
            defaultextension=".pgn",
            filetypes=[("PGN files", "*.pgn")],
            title="Save Game as PGN"
        )
            if file_path:
                with open(file_path, "w") as f:
                    f.write(pgn_text)
            

        popup = tk.Toplevel(self)
        popup.title("Game Over")

        def play_again(self):
            popup.destroy()
            change_popup = tk.Toplevel(self)
            change_popup.title("Change Settings")
            tk.Label(change_popup, text="Change Settings?").pack(pady=10)
            tk.Button(change_popup, text="Yes", command=lambda: [change_popup.destroy(), self.controller.show_frame(ComputerSetupView)]).pack(pady=5)
            tk.Button(change_popup, text="No", command=lambda: [change_popup.destroy(), self.controller.start_ai_game()]).pack(pady=5)

        tk.Label(popup, text=result_text, font=("Helvetica", 16)).pack(pady=10)

        tk.Button(popup, text="Play Again", command=lambda: play_again(self)).pack(pady=5)
        tk.Button(popup, text="Export PGN", command=export_pgn).pack(pady=5)
        tk.Button(popup, text="Home", command=lambda: [popup.destroy(), self.controller.show_frame(WelcomeView)]).pack(pady=5)

    def start_voice_mode(self):
        self.voice_thread = threading.Thread(target=self.listen_and_play, daemon=True)
        self.voice_thread.start()

    def listen_and_play(self):
        while not self.board.is_game_over():
            move_text = listen_for_move()
            move = parse_move(move_text, self.board)
            if move and move in self.board.legal_moves:
                self.board.push(move)
                self.move_history.append(self.board.san(move))
                self.update_board()
            else:
                print("Invalid move — try again.")
            self.stockfish_move()
        

    def update_board(self):
        svg = chess.svg.board(board=self.board, orientation=chess.BLACK if self.color == "Black" else chess.WHITE).encode("utf-8")
        png = io.BytesIO()
        svg2png(bytestring=svg, write_to=png)
        img = Image.open(png)
        tk_img = ImageTk.PhotoImage(img)
        self.board_label.config(image=tk_img)
        self.board_label.image = tk_img

    def update_timers(self):
        mins, secs = divmod(self.white_time, 60)
        self.timer_white.config(text=f"White: {mins:02}:{secs:02}")
        mins, secs = divmod(self.black_time, 60)
        self.timer_black.config(text=f"Black: {mins:02}:{secs:02}")

    def playing_as_black(self):
        if self.color == "Black" and len(self.move_history) == 0:
            
            self.stockfish_move()
        self.update_board()

    def submit_move(self):
        move = self.move_var.get()
        try:
            chess_move = self.board.parse_san(move)
            if chess_move in self.board.legal_moves:
                self.board.push(chess_move)
                self.move_history.append(move)
                self.stockfish.set_fen_position(self.board.fen())
                self.moves_box.insert("end", f"{move}\n")
                self.move_var.set("")
                self.update_board()       
                t = threading.Thread(target=self.stockfish_move)
                t.daemon = True
                t.start()
                
                if self.color == "White":
                    self.white_time += self.controller.game_settings['increment']
                else:
                    self.black_time += self.controller.game_settings['increment']
                self.update_timers()

            else:
                self.moves_box.insert("end", "Illegal move\n")
        except:
            self.moves_box.insert("end", "Invalid move format\n")
      
 

        #start timers after first move
        if not self.timer_running:
            self.start_timers()

         # Check for game over conditions
        if self.board.is_checkmate():
            self.game_over("Checkmate! You Won!")
        elif self.board.is_stalemate():
            self.game_over("Stalemate! Draw!")
        elif self.board.is_insufficient_material():
            self.game_over("Draw due to insufficient material!")
        elif self.board.can_claim_fifty_moves():
            self.game_over("Draw by fifty-move rule!")
        elif self.board.can_claim_threefold_repetition():
            self.game_over("Draw by threefold repetition!")    


    def stockfish_move(self):  
        if len(self.move_history) == 0:
            sf_move = self.stockfish.get_best_move()
        else:
            # Time for Stockfish to think
            sf_move = self.stockfish.get_best_move_time(20000)  
        if sf_move:
            move = chess.Move.from_uci(sf_move)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.move_history.append(move.uci())
                self.moves_box.insert("end", f"{move}\n")
                
                if self.color == "White":
                    self.black_time += self.controller.game_settings['increment']
                else:
                    self.white_time += self.controller.game_settings['increment']
                
                self.update_timers()
        self.after(1, self.update_board())

        if not self.board.is_game_over():
            self.start_voice_mode()
        
        # Check for game over conditions
        if self.board.is_checkmate():
                self.game_over("Checkmate! You Lost.")
        elif self.board.is_stalemate():
            self.game_over("Stalemate! Draw!")
        elif self.board.is_insufficient_material():
            self.game_over("Draw due to insufficient material!")
        elif self.board.can_claim_fifty_moves():
            self.game_over("Draw by fifty-move rule!")
        elif self.board.can_claim_threefold_repetition():
            self.game_over("Draw by threefold repetition!")

    def takeback_move(self):
        if self.takebacks and len(self.move_history) >= 2:
            self.board.pop()
            self.board.pop()
            self.move_history = self.move_history[:-2]
            self.update_board()

    def run_timers(self):
        while self.timer_running:
            if self.board.turn == chess.WHITE:
                self.white_time -= 1
                mins, secs = divmod(self.white_time, 60)
                self.timer_white.config(text=f"White: {mins:02}:{secs:02}")
            else:
                self.black_time -= 1
                mins, secs = divmod(self.black_time, 60)
                self.timer_black.config(text=f"Black: {mins:02}:{secs:02}")
            time.sleep(1)

    def time_result(self):
        if (self.color == "White" and self.white_time < 0) or (self.color == "Black" and self.black_time < 0):
            self.game_over("You Lost on time!")
        elif (self.color == "White" and self.black_time < 0) or (self.color == "Black" and self.white_time < 0):
            self.game_over("You won on time!")
    


if __name__ == "__main__":
    app = BlindfoldedChessApp()
    app.mainloop()
