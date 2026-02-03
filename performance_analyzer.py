import pygame
import sys
import copy
import random
import time
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from TD_Learning_MCTS import select_move_with_td, get_valid_moves, encode_state, evaluate_board_with_position

# Constants
WINDOW_SIZE = 600
CELL_SIZE = 60
NUM_GAMES = 50
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRID_COLOR = (0, 128, 0)
BACKGROUND_COLOR = (34, 139, 34)


class TournamentAnalytics:
    def __init__(self):
        self.metrics = {
            'game_lengths': [],
            'win_history': [],  # 'B', 'W', or 'D'
            'piece_counts': [],  # List of (black_count, white_count) tuples
            'move_times': defaultdict(list),  # {'B': [], 'W': []}
            'valid_moves_count': defaultdict(list),  # {'B': [], 'W': []}
            'position_scores': defaultdict(list),  # {'B': [], 'W': []}
            'moves_per_game': []
        }

    def record_game_length(self, num_moves):
        self.metrics['game_lengths'].append(num_moves)

    def record_win(self, winner):
        self.metrics['win_history'].append(winner)

    def record_piece_count(self, black_count, white_count):
        self.metrics['piece_counts'].append((black_count, white_count))

    def record_move_time(self, player, time_taken):
        self.metrics['move_times'][player].append(time_taken)

    def record_valid_moves(self, player, num_moves):
        self.metrics['valid_moves_count'][player].append(num_moves)

    def record_position_score(self, player, score):
        self.metrics['position_scores'][player].append(score)

    def plot_all_metrics(self):
        plt.style.use('ggplot')  # Changed from 'seaborn' to 'ggplot'
        fig = plt.figure(figsize=(20, 12))

        # 1. Win Rate Analysis
        ax1 = fig.add_subplot(231)
        self._plot_win_rates(ax1)

        # 2. Game Length Distribution
        ax2 = fig.add_subplot(232)
        self._plot_game_length_distribution(ax2)

        # 3. Piece Count Progression
        ax3 = fig.add_subplot(233)
        self._plot_piece_count_progression(ax3)

        # 4. Move Time Analysis
        ax4 = fig.add_subplot(234)
        self._plot_move_times(ax4)

        # 5. Valid Moves Analysis
        ax5 = fig.add_subplot(235)
        self._plot_valid_moves(ax5)

        # 6. Position Score Trends
        ax6 = fig.add_subplot(236)
        self._plot_position_scores(ax6)

        plt.tight_layout()
        plt.savefig('tournament_analytics.png')
        plt.close()

    def _plot_win_rates(self, ax):
        wins = {'B': 0, 'W': 0, 'D': 0}
        for winner in self.metrics['win_history']:
            wins[winner] += 1

        total_games = len(self.metrics['win_history'])
        win_rates = {k: (v / total_games) * 100 for k, v in wins.items()}

        colors = ['black', 'white', 'gray']
        ax.bar(win_rates.keys(), win_rates.values(), color=colors)
        ax.set_title('Win Rates')
        ax.set_ylabel('Win Rate (%)')

        for i, v in enumerate(win_rates.values()):
            ax.text(i, v + 1, f'{v:.1f}%', ha='center')

    def _plot_game_length_distribution(self, ax):
        ax.hist(self.metrics['game_lengths'], bins=20, edgecolor='black')
        ax.set_title('Game Length Distribution')
        ax.set_xlabel('Number of Moves')
        ax.set_ylabel('Frequency')

    def _plot_piece_count_progression(self, ax):
        black_counts = [count[0] for count in self.metrics['piece_counts']]
        white_counts = [count[1] for count in self.metrics['piece_counts']]

        games = range(len(black_counts))
        ax.plot(games, black_counts, 'k-', label='Black')
        ax.plot(games, white_counts, 'r-', label='White')
        ax.set_title('Piece Count Progression')
        ax.set_xlabel('Game Number')
        ax.set_ylabel('Number of Pieces')
        ax.legend()

    def _plot_move_times(self, ax):
        black_times = self.metrics['move_times']['B']
        white_times = self.metrics['move_times']['W']

        ax.boxplot([black_times, white_times], tick_labels=['Black', 'White'])
        ax.set_title('Move Time Analysis')
        ax.set_ylabel('Time (seconds)')

    def _plot_valid_moves(self, ax):
        black_moves = self.metrics['valid_moves_count']['B']
        white_moves = self.metrics['valid_moves_count']['W']

        # Ensure both lists are the same length
        max_length = max(len(black_moves), len(white_moves))
        black_moves.extend([None] * (max_length - len(black_moves)))
        white_moves.extend([None] * (max_length - len(white_moves)))

        moves = range(max_length)
        ax.plot(moves, black_moves, 'k-', label='Black', alpha=0.7)
        ax.plot(moves, white_moves, 'r-', label='White', alpha=0.7)

        ax.set_title('Valid Moves Available')
        ax.set_xlabel('Move Number')
        ax.set_ylabel('Number of Valid Moves')
        ax.legend()

    def _plot_position_scores(self, ax):
        black_scores = self.metrics['position_scores']['B']
        white_scores = self.metrics['position_scores']['W']

        # Determine the maximum length between the two lists
        max_length = max(len(black_scores), len(white_scores))

        # Pad the shorter list with np.nan (or any placeholder value)
        if len(black_scores) < max_length:
            black_scores = black_scores + [np.nan] * (max_length - len(black_scores))
        if len(white_scores) < max_length:
            white_scores = white_scores + [np.nan] * (max_length - len(white_scores))

        moves = range(max_length)
        ax.plot(moves, black_scores, 'k-', label='Black', alpha=0.7)
        ax.plot(moves, white_scores, 'r-', label='White', alpha=0.7)

        ax.set_title('Position Score Trends')
        ax.set_xlabel('Move Number')
        ax.set_ylabel('Position Score')
        ax.legend()

    def generate_summary_stats(self):
        total_games = len(self.metrics['win_history'])
        black_wins = self.metrics['win_history'].count('B')
        white_wins = self.metrics['win_history'].count('W')
        draws = self.metrics['win_history'].count('D')

        avg_game_length = np.mean(self.metrics['game_lengths'])
        avg_move_time_black = np.mean(self.metrics['move_times']['B'])
        avg_move_time_white = np.mean(self.metrics['move_times']['W'])

        return {
            'total_games': total_games,
            'black_win_rate': (black_wins / total_games) * 100,
            'white_win_rate': (white_wins / total_games) * 100,
            'draw_rate': (draws / total_games) * 100,
            'avg_game_length': avg_game_length,
            'avg_move_time_black': avg_move_time_black,
            'avg_move_time_white': avg_move_time_white
        }


# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 100))
pygame.display.set_caption("AI Tournament Visualization")
font = pygame.font.Font(None, 36)


def draw_board(board):
    screen.fill(BACKGROUND_COLOR)

    # Draw grid
    for i in range(9):
        pygame.draw.line(screen, GRID_COLOR, (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE))
        pygame.draw.line(screen, GRID_COLOR, (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE))

    # Draw pieces
    for row in range(8):
        for col in range(8):
            if board[row][col]:
                color = BLACK if board[row][col] == 'B' else WHITE
                center = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
                pygame.draw.circle(screen, color, center, CELL_SIZE // 2 - 5)


def draw_stats(game_number, black_wins, white_wins, draws):
    stats_rect = pygame.Rect(0, WINDOW_SIZE, WINDOW_SIZE, 100)
    pygame.draw.rect(screen, (200, 200, 200), stats_rect)

    progress_text = f"Game: {game_number}/{NUM_GAMES}"
    score_text = f"Black: {black_wins} White: {white_wins} Draws: {draws}"

    progress_surface = font.render(progress_text, True, BLACK)
    score_surface = font.render(score_text, True, BLACK)

    screen.blit(progress_surface, (20, WINDOW_SIZE + 20))
    screen.blit(score_surface, (20, WINDOW_SIZE + 60))


def get_opponent(player):
    return 'W' if player == 'B' else 'B'


def is_valid_move(board, row, col, player):
    if row < 0 or row >= 8 or col < 0 or col >= 8:
        return False
    if board[row][col] is not None:
        return False

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    opponent = get_opponent(player)

    for dx, dy in directions:
        x, y = row + dx, col + dy
        if not (0 <= x < 8 and 0 <= y < 8):
            continue
        if board[x][y] != opponent:
            continue

        x, y = x + dx, y + dy
        while 0 <= x < 8 and 0 <= y < 8 and board[x][y] is not None:
            if board[x][y] == player:
                return True
            x, y = x + dx, y + dy

    return False


def place_piece(board, row, col, player):
    if not is_valid_move(board, row, col, player):
        return False

    board[row][col] = player
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    opponent = get_opponent(player)
    pieces_flipped = False

    for dx, dy in directions:
        x, y = row + dx, col + dy
        to_flip = []

        while 0 <= x < 8 and 0 <= y < 8 and board[x][y] is not None:
            if board[x][y] == opponent:
                to_flip.append((x, y))
            elif board[x][y] == player:
                for flip_x, flip_y in to_flip:
                    board[flip_x][flip_y] = player
                pieces_flipped = True if to_flip else pieces_flipped
                break
            x, y = x + dx, y + dy

    return True


def count_pieces(board):
    black_count = sum(row.count('B') for row in board)
    white_count = sum(row.count('W') for row in board)
    return black_count, white_count


def get_valid_moves(board, player):
    moves = []
    for row in range(8):
        for col in range(8):
            if is_valid_move(board, row, col, player):
                moves.append((row, col))
    return moves


def self_play_tournament():
    analytics = TournamentAnalytics()
    black_wins = 0
    white_wins = 0
    draws = 0
    clock = pygame.time.Clock()

    for game_num in range(1, NUM_GAMES + 1):
        print(f"\nStarting game {game_num}")

        # Initialize board with starting position
        board = [[None for _ in range(8)] for _ in range(8)]
        board[3][3] = board[4][4] = 'W'
        board[3][4] = board[4][3] = 'B'

        current_player = 'B'
        consecutive_passes = 0
        move_count = 0

        while consecutive_passes < 2:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            valid_moves = get_valid_moves(board, current_player)
            print(f"Player {current_player} has {len(valid_moves)} valid moves")

            if not valid_moves:
                consecutive_passes += 1
                print(f"Player {current_player} passes")
                current_player = get_opponent(current_player)
                continue

            consecutive_passes = 0
            try:
                move_start_time = time.time()
                move = select_move_with_td(current_player, board)
                move_time_taken = time.time() - move_start_time

                analytics.record_move_time(current_player, move_time_taken)
                analytics.record_valid_moves(current_player, len(valid_moves))
                analytics.record_position_score(current_player, evaluate_board_with_position(board, current_player))

                print(f"Player {current_player} selected move: {move}")

                if move and isinstance(move, tuple) and len(move) == 2:
                    row, col = move
                    if place_piece(board, row, col, current_player):
                        print(f"Successfully placed piece at ({row}, {col})")
                    else:
                        print(f"Invalid move attempted at ({row}, {col})")
                else:
                    print(f"Invalid move format returned: {move}")
                    break

            except Exception as e:
                print(f"Error during move selection: {e}")
                break

            # Update display
            draw_board(board)
            draw_stats(game_num, black_wins, white_wins, draws)
            pygame.display.flip()
            clock.tick(2)

            current_player = get_opponent(current_player)
            move_count += 1

        # Count pieces and determine winner
        black_count, white_count = count_pieces(board)
        analytics.record_piece_count(black_count, white_count)
        analytics.record_game_length(move_count)

        print(f"Game {game_num} finished - Black: {black_count}, White: {white_count}")

        if black_count > white_count:
            black_wins += 1
            analytics.record_win('B')
            print("Black wins!")
        elif white_count > black_count:
            white_wins += 1
            analytics.record_win('W')
            print("White wins!")
        else:
            draws += 1
            analytics.record_win('D')
            print("Draw!")

        # Final display update for this game
        draw_board(board)
        draw_stats(game_num, black_wins, white_wins, draws)
        pygame.display.flip()
        time.sleep(1)

    # Plot all metrics after the tournament ends
    analytics.plot_all_metrics()

    return black_wins, white_wins, draws


if __name__ == "__main__":
    try:
        print("Starting AI Tournament Visualization...")
        black_wins, white_wins, draws = self_play_tournament()
        print("\nFinal Tournament Results:")
        print(f"Black Wins: {black_wins}")
        print(f"White Wins: {white_wins}")
        print(f"Draws: {draws}")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()
    finally:
        pygame.quit()