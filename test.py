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


class BlindfoldedChessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blindfolded Chess")
        self.game_settings = {"difficulty": 3, "time_control": "5+0", "color": "White", "takebacks": True}

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        self.container = container
        self.frames = {}

        # Create only the static startup frames here
        for F in (WelcomeView, ModeSelectView, LoginPage, OnlineSetupView, ComputerSetupView):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(WelcomeView)

    def show_frame(self, page):
        frame = self.frames.get(page)
        if frame:
            frame.tkraise()
        else:
            print(f"No frame found for: {page}")

    def start_ai_game(self, difficulty=None, time_control=None, color=None, takebacks=None):
        if difficulty is None:
            difficulty = self.game_settings["difficulty"]
        else:
            self.game_settings["difficulty"] = difficulty
        if time_control is None:
            time_control = self.game_settings["time_control"]
        else:
            self.game_settings["time_control"] = time_control
        if color is None:
            color = self.game_settings["color"]
        else:
            self.game_settings["color"] = color
        if takebacks is None:
            takebacks = self.game_settings["takebacks"]
        else:
            self.game_settings["takebacks"] = takebacks

        if isinstance(time_control, str):
            try:
                minutes, increment = map(int, time_control.split("+"))
            except Exception:
                minutes, increment = 5, 0
        elif isinstance(time_control, tuple):
            minutes, increment = time_control
        else:
            minutes, increment = 5, 0

        # Remove old GameViewComputer if exists
        old = self.frames.get(GameViewComputer)
        if old:
            try:
                old.destroy()
            except Exception:
                pass
            del self.frames[GameViewComputer]

        # create fresh GameViewComputer and register it
        game_frame = GameViewComputer(self.container, self,
                                      difficulty=difficulty,
                                      time_control=(minutes, increment),
                                      color=color,
                                      takebacks=takebacks)
        game_frame.grid(row=0, column=0, sticky="nsew")
        label = tk.Label(self, text="Vs Computer Setup")
        label.pack(pady=10)

        tk.Label(self, text="Difficulty (1-20)").pack()
        self.diff_var = tk.StringVar(value=str(self.game_settings["difficulty"]))
        tk.Entry(self, textvariable=self.diff_var).pack(pady=5)
        
        tk.Label(self, text="Time Control").pack()
        self.time_var = tk.StringVar(value=self.game_settings["time_control"])
        tk.OptionMenu(self, self.time_var, "1+0", "3+0", "3+2", "5+0", "5+3", "10+0").pack(pady=5)

        tk.Label(self, text="Play as").pack()
        self.color_var = tk.StringVar(value=self.game_settings["color"])
        tk.OptionMenu(self, self.color_var, "White", "Black").pack(pady=5)

        tk.Label(self, text="Takebacks Allowed?").pack()
        self.takebacks_var = tk.StringVar(value="Yes" if self.game_settings["takebacks"] else "No")
        tk.OptionMenu(self, self.takebacks_var, "Yes", "No").pack(pady=5)

        def on_start():
            # update controller's stored settings and start game
            diff = int(self.diff_var.get())
            tc = self.time_var.get()
            color = self.color_var.get()
            takebacks = (self.takebacks_var.get() == "Yes")

            # Update stored settings
            self.game_settings = {"difficulty": diff, "time_control": tc, "color": color, "takebacks": takebacks}
            self.start_ai_game(difficulty=diff, time_control=tc, color=color, takebacks=takebacks)
        btn_start = tk.Button(self, text="Start Game", command=on_start)
        btn_start.pack(pady=5)
        btn_back = tk.Button(self, text="Back", command=lambda: self.show_frame(ModeSelectView))
        btn_back.pack(pady=5)

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
        label = tk.Label(self, text="Vs Computer Setup")
        label.pack(pady=10)

        tk.Label(self, text="Difficulty (1-8)").pack()
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
        BlindfoldedChessApp.game_settings = {"difficulty": int(self.diff_var.get()), "time_control": self.time_var.get(), 
                                             "color": self.color_var.get(), "takebacks": self.takebacks_var.get() == "Yes"}

# Game Screen (Online placeholder)
class GameViewOnline(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Blindfolded Chess Game (Online)")
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

        # If arguments are None, use stored controller settings
        if difficulty is None:
            difficulty = controller.game_settings["difficulty"]
        if time_control is None:
            # controller stores time_control as string like "5+0"
            tc = controller.game_settings["time_control"]
            if isinstance(tc, str):
                try:
                   minutes, increment = map(int, tc.split("+"))
                   time_control = (minutes, increment)
                except:
                    time_control = (5, 0)
            elif isinstance(tc, tuple):
                time_control = tc
            else:
                time_control = (5, 0)

        if color is None:
            color = controller.game_settings["color"]

        if takebacks is None:
            takebacks = controller.game_settings["takebacks"]

        self.difficulty = difficulty
        self.time_control = time_control  # (minutes, increment)
        self.color = color
        self.takebacks = takebacks
        self.board = chess.Board()

        # Make sure the path matches and backslashes are escaped or use raw string
        sf_path = "C:\stockfish\stockfish-windows-x86-64-avx2.exe"

        try:
            self.stockfish = Stockfish(path=sf_path, depth=15)
            self.stockfish.set_skill_level(self.difficulty)
        except Exception as e:
            print("Warning: could not start Stockfish:", e)
            self.stockfish = None

        self.move_history = []

        # UI Elements
        self.label = tk.Label(self, text="AI Chess Game")
        self.label.pack()

        self.board_label = tk.Label(self)
        self.board_label.pack()

        self.moves_box = tk.Text(self, height=10, width=40)
        self.moves_box.pack()
        self.move_var = tk.StringVar()

        tk.Entry(self, textvariable=self.move_var).pack()
        tk.Button(self, text="Submit Move", command=self.submit_move).pack()

        self.timer_white = tk.Label(self, text=f"White: {self.time_control[0]:02}:00")
        self.timer_white.pack(side="left", padx=5)
        self.timer_black = tk.Label(self, text=f"Black: {self.time_control[0]:02}:00")
        self.timer_black.pack(side="left", padx=5)
        self.takeback_btn = tk.Button(self, text="Takeback", command=self.takeback_move)
        self.takeback_btn.pack(side="left", padx=5)
        self.resign_btn = tk.Button(self, text="Resign", command=lambda: self.game_over("You Resigned"))
        self.resign_btn.pack(side="left", padx=5)
        self.update_board()

        # Timers
        self.white_time = self.time_control[0] * 60
        self.black_time = self.time_control[0] * 60
        self.timer_running = True
        threading.Thread(target=self.run_timers, daemon=True).start()

    def game_over(self, result_text):
        self.timer_running = False  # Stop timers

        def export_pgn():
            try:
                game = pgn.Game()
                node = game
                board = chess.Board()

                for mv in self.move_history:
                    try:
                        # mv might be in SAN or UCI; we try SAN first
                        board.push_san(mv)
                        node = node.add_variation(board.peek())
                    except:
                        try:
                            board.push_uci(mv)
                            node = node.add_variation(board.peek())
                        except:
                            break

                pgn_text = str(game)
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".pgn",
                    filetypes=[("PGN files", "*.pgn")],
                    title="Save Game as PGN"
                )

                if file_path:
                    with open(file_path, "w") as f:
                        f.write(pgn_text)
            except Exception as e:
                print("Could not export PGN:", e)

        popup = tk.Toplevel(self)
        popup.title("Game Over")
        tk.Label(popup, text=result_text, font=("Helvetica", 16)).pack(pady=10)

        def play_again_flow():
            popup.destroy()
            change_popup = tk.Toplevel(self)
            change_popup.title("Change Settings?")
            tk.Label(change_popup, text="Do you want to change settings?").pack(pady=10)

            def yes():
                change_popup.destroy()
                # show setup view so user can modify settings
                self.controller.show_frame(ComputerSetupView)

            def no():
                change_popup.destroy()
                # restart with stored settings
                self.controller.start_ai_game()  # uses controller.game_settings
            tk.Button(change_popup, text="Yes", command=yes).pack(pady=5)
            tk.Button(change_popup, text="No", command=no).pack(pady=5)

        tk.Button(popup, text="Play Again", command=play_again_flow).pack(pady=5)
        tk.Button(popup, text="Export PGN", command=export_pgn).pack(pady=5)
        tk.Button(popup, text="Home", command=lambda: [popup.destroy(), self.controller.show_frame(WelcomeView)]).pack(pady=5)

    def update_board(self):
        try:
            svg = chess.svg.board(board=self.board)
            png = io.BytesIO()
            svg2png(bytestring=svg, write_to=png)
            img = Image.open(png)
            tk_img = ImageTk.PhotoImage(img)
            self.board_label.config(image=tk_img)
            self.board_label.image = tk_img

        except Exception as e:
            # fallback: show ASCII in moves box
            self.moves_box.insert("end", f"Could not render board image: {e}\n")

    def submit_move(self):
        move = self.move_var.get().strip()
        if not move:
            return
        try:
            chess_move = self.board.parse_san(move)
            if chess_move in self.board.legal_moves:
                self.board.push(chess_move)
                self.move_history.append(move)
                if self.stockfish:
                    self.stockfish.set_fen_position(self.board.fen())
                self.moves_box.insert("end", f"{move}\n")
                self.move_var.set("")
                self.update_board()

                # check for terminal
                if self.board.is_game_over():
                    self.game_over("Game over: " + self.result_text())
                    return

                # ask engine to move
                self.stockfish_move()
            else:
                self.moves_box.insert("end", "Illegal move\n")
        except Exception:
            self.moves_box.insert("end", "Invalid move format\n")

    def stockfish_move(self):
        if not self.stockfish:
            return
        sf_move = self.stockfish.get_best_move()

        if sf_move:
            self.board.push_uci(sf_move)
            self.move_history.append(sf_move)
            self.moves_box.insert("end", f"{sf_move}\n")
            self.update_board()
            if self.board.is_game_over():
                self.game_over("Game over: " + self.result_text())

    def result_text(self):
        if self.board.is_checkmate():
            return "Checkmate!"
        if self.board.is_stalemate():
            return "Stalemate!"
        if self.board.is_insufficient_material():
            return "Draw: insufficient material"
        if self.board.can_claim_fifty_moves():
            return "Draw: 50-move"
        if self.board.can_claim_threefold_repetition():
            return "Draw: threefold repetition"
        return "Game over"

    def takeback_move(self):
        if self.takebacks and len(self.move_history) >= 2:
            try:
                self.board.pop()
                self.board.pop()
                self.move_history = self.move_history[:-2]
                self.update_board()
            except Exception as e:
                print("Takeback failed:", e)

    def run_timers(self):
        while self.timer_running:
            try:
                if self.board.turn == chess.WHITE:
                    self.white_time -= 1
                    mins, secs = divmod(self.white_time, 60)
                    self.timer_white.config(text=f"White: {mins:02}:{secs:02}")
                else:
                    self.black_time -= 1
                    mins, secs = divmod(self.black_time, 60)
                    self.timer_black.config(text=f"Black: {mins:02}:{secs:02}")
            except Exception:
                pass
            time.sleep(1)

if __name__ == "__main__":
    app = BlindfoldedChessApp()
    app.mainloop()