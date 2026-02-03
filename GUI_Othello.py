import pygame
import sys
import math
import copy
import pickle
import os
import random

# Filepath for storing the AI's knowledge
# KNOWLEDGE_FILE = "value_table.pkl"

# Load knowledge from file if it exists
def load_value_table(filename):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    return {}  # Start fresh if no file exists

# Save knowledge to file after each game
def save_value_table(filename):
    with open(filename, 'wb') as file:
        pickle.dump(value_table, file)

# Initialize Pygame
pygame.init()

# Constants
BOARD_SIZE = 8
CELL_SIZE = 60
BOARD_WIDTH = BOARD_SIZE * CELL_SIZE
BOARD_HEIGHT = BOARD_SIZE * CELL_SIZE + 100
SCOREBOARD_HEIGHT = 100  # Adjust height for the scoreboard
WINDOW_HEIGHT = BOARD_HEIGHT + SCOREBOARD_HEIGHT  # Total height including the scoreboard
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
LIGHT_GREEN = (144, 238, 144)
GRAY = (128, 128, 128)
DEPTH = 6
FPS = 60

# Value table for TD learning
value_table = {}


# Function to encode board states as a tuple for dictionary keys
def encode_state(board):
    return tuple(tuple(row) for row in board)


# Retrieve or initialize the value of a board state
def get_state_value(board):
    state = encode_state(board)
    if state not in value_table:
        value_table[state] = 0.5  # Neutral starting value
    return value_table[state]

# TD learning update rule
def td_update(current_board, next_board, reward, alpha, gamma=0.95):
    """
    Updated TD learning with position-weighted evaluation
    """
    current_state = encode_state(current_board)
    next_state = encode_state(next_board)

    if current_state not in value_table:
        # Initialize with position-weighted evaluation
        value_table[current_state] = 0.5 + 0.1 * evaluate_board_with_position(current_board, 'B')

    if next_state not in value_table:
        value_table[next_state] = 0.5 + 0.1 * evaluate_board_with_position(next_board, 'B')

    # TD(0) update with additional features
    current_value = value_table[current_state]
    next_value = value_table[next_state]

    # Include mobility and stability in the update
    mobility_factor = 0.05 * mobility(next_board, 'B')
    position_factor = 0.1 * evaluate_board_with_position(next_board, 'B')

    # Updated TD formula with additional features
    value_table[current_state] = current_value + alpha * (
            reward +
            gamma * (next_value + mobility_factor + position_factor) -
            current_value
    )

# AI move selection based on TD learning values
def select_move_with_td(player, board_state, exploration_rate=0.1):
    """
    Select a move using TD learning values with epsilon-greedy exploration
    and incorporating minimax evaluation
    """
    valid_moves = get_valid_moves(player, board_state)
    if not valid_moves:
        return None

    # Epsilon-greedy exploration
    if random.random() < exploration_rate:
        return random.choice(valid_moves)

    best_move = None
    best_value = float('-inf')

    for move in valid_moves:
        temp_board = copy.deepcopy(board_state)
        make_move(temp_board, move[0], move[1], player)

        # Combine TD value with minimax evaluation
        td_value = get_state_value(temp_board)

        # Get minimax value (first element of tuple)
        minimax_result = alpha_beta_pruning(3, False, 'W' if player == 'B' else 'B',
                                            temp_board, float('-inf'), float('inf'))
        minimax_value = minimax_result[0] if minimax_result[0] is not None else 0

        # Weighted combination of TD and minimax values
        combined_value = 0.3 * td_value + 0.7 * minimax_value

        if combined_value > best_value:
            best_value = combined_value
            best_move = move

    return best_move


# Set up the display
screen = pygame.display.set_mode((BOARD_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Othello Game")
clock = pygame.time.Clock()

# Create the game board (2D array)
board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

# Animation variables
flipping_pieces = []
FLIP_DURATION = 60  # Increased duration for slower animation
player_name = ""

def draw_rounded_rect(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect.inflate(-radius * 2, -radius * 2))
    pygame.draw.rect(surface, color, rect.inflate(-radius * 2, 0))
    pygame.draw.rect(surface, color, rect.inflate(0, -radius * 2))
    pygame.draw.circle(surface, color, (rect.topleft[0] + radius, rect.topleft[1] + radius), radius)
    pygame.draw.circle(surface, color, (rect.topright[0] - radius, rect.topright[1] + radius), radius)
    pygame.draw.circle(surface, color, (rect.bottomleft[0] + radius, rect.bottomleft[1] - radius), radius)
    pygame.draw.circle(surface, color, (rect.bottomright[0] - radius, rect.bottomright[1] - radius), radius)

def draw_board():
    screen.fill(GREEN)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, BLACK, rect, 1)


def draw_scoreboard(current_player):
    font = pygame.font.Font(None, 36)
    black_score = sum(row.count('B') for row in board)
    white_score = sum(row.count('W') for row in board)

    # Scoreboard background (Positioned below the game board)
    scoreboard_rect = pygame.Rect(0, BOARD_HEIGHT, BOARD_WIDTH, SCOREBOARD_HEIGHT)
    draw_rounded_rect(screen, (50, 50, 50), scoreboard_rect, 10)

    # Set colors for active and inactive players
    player_bg_color = LIGHT_GREEN if current_player == 'B' else (30, 30, 30)
    ai_bg_color = LIGHT_GREEN if current_player == 'W' else (30, 30, 30)

    # Player score (left side of the scoreboard)
    player_rect = pygame.Rect(20, BOARD_HEIGHT + 20, (BOARD_WIDTH - 40) // 2 - 10, 60)
    draw_rounded_rect(screen, player_bg_color, player_rect, 5)
    player_text = font.render(f"{player_name}", True, WHITE)
    screen.blit(player_text, (player_rect.x + 10, player_rect.y + 5))
    score_text = font.render(f"{black_score}", True, WHITE)
    screen.blit(score_text, (player_rect.right - score_text.get_width() - 10, player_rect.y + 5))

    # AI score (right side of the scoreboard)
    ai_rect = pygame.Rect(BOARD_WIDTH // 2 + 10, BOARD_HEIGHT + 20, (BOARD_WIDTH - 40) // 2 - 10, 60)
    draw_rounded_rect(screen, ai_bg_color, ai_rect, 5)
    ai_text = font.render("AI", True, WHITE)
    screen.blit(ai_text, (ai_rect.x + 10, ai_rect.y + 5))
    ai_score_text = font.render(f"{white_score}", True, WHITE)
    screen.blit(ai_score_text, (ai_rect.right - ai_score_text.get_width() - 10, ai_rect.y + 5))

def get_board_position(pos):
    x, y = pos
    row = y // CELL_SIZE
    col = x // CELL_SIZE
    return row, col


def initialize_board():
    mid = BOARD_SIZE // 2
    board[mid - 1][mid - 1] = 'W'
    board[mid - 1][mid] = 'B'
    board[mid][mid - 1] = 'B'
    board[mid][mid] = 'W'


def draw_pieces():
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col]:
                draw_piece(row, col, board[row][col])


def draw_piece(row, col, color):
    center = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
    pygame.draw.circle(screen, BLACK if color == 'B' else WHITE, center, CELL_SIZE // 2 - 5)


def update_flipping_pieces():
    for piece in flipping_pieces[:]:  # Iterate over a copy to safely modify the list
        piece[4] += 1  # Advance the animation frame

        if piece[4] >= FLIP_DURATION:
            # Complete the flip after animation
            board[piece[0]][piece[1]] = piece[3]  # Set to final color (B or W)
            flipping_pieces.remove(piece)  # Remove from animation list once flipped


def draw_flipping_pieces():
    for piece in flipping_pieces:
        row, col, from_color, to_color, frame = piece
        progress = frame / FLIP_DURATION

        # Calculate the angle of rotation based on progress
        angle = progress * math.pi

        # Calculate the height of the ellipse based on the angle
        height = abs(math.cos(angle)) * (CELL_SIZE // 2 - 5)
        width = CELL_SIZE // 2 - 5

        center = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)

        # Determine the color based on the angle
        if angle < math.pi / 2:
            color = BLACK if from_color == 'B' else WHITE
        else:
            color = BLACK if to_color == 'B' else WHITE

        # Draw the ellipse (flipping coin)
        pygame.draw.ellipse(screen, color, (center[0] - width, center[1] - height, width * 2, height * 2))

        # Draw the edge of the coin
        if height > 0:
            pygame.draw.ellipse(screen, GRAY, (center[0] - width, center[1] - height, width * 2, height * 2), 1)


def show_name_entry_dialog():
    global player_name
    font = pygame.font.Font(None, 36)
    input_box = pygame.Rect(BOARD_WIDTH // 4, BOARD_HEIGHT // 2 - 20, BOARD_WIDTH // 2, 40)
    color_inactive = GRAY
    color_active = LIGHT_GREEN
    color = color_inactive
    active = False
    text = ''

    # Load the Othello logo
    logo = pygame.image.load(r"othello.jpg")
    logo = pygame.transform.scale(logo, (460, 215))

    # Load the team logo for the bottom
    bottom_image = pygame.image.load(r"projectX.jpg")
    bottom_image = pygame.transform.scale(bottom_image, (377, 260))

    overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT + 100), pygame.SRCALPHA)
    overlay.fill((41, 82, 64, 180))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        player_name = text
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        screen.blit(overlay, (0, 0))

        # Draw the logo at the top center
        logo_rect = logo.get_rect(center=(BOARD_WIDTH // 2, 100))  # Center it at the top
        screen.blit(logo, logo_rect)

        draw_rounded_rect(screen, color, input_box, 5)

        # Center align the entered name text
        txt_surface = font.render(text, True, WHITE)
        text_x = input_box.x + (input_box.width - txt_surface.get_width()) // 2
        screen.blit(txt_surface, (text_x, input_box.y + 10))

        # Center align the prompt text
        prompt_surface = font.render("Enter your name:", True, WHITE)
        screen.blit(prompt_surface, ((BOARD_WIDTH - prompt_surface.get_width()) // 2, BOARD_HEIGHT // 2 - 60))

        # Draw the bottom image centered with specified spacing from the bottom
        bottom_image_rect = bottom_image.get_rect(
            center=(BOARD_WIDTH // 2, BOARD_HEIGHT - bottom_image.get_height() // 2 + 120))
        screen.blit(bottom_image, bottom_image_rect)

        pygame.display.flip()


def show_rules_screen():
    font = pygame.font.Font(None, 36)
    rules_text = [
        "Othello Rules:",
        "",
        "1. Players take turns placing pieces on the board.",
        "2. A piece can be placed if it sandwiches the opponent's pieces.",
        "3. All sandwiched pieces are flipped to the player's color.",
        "4. The game ends when the board is full or no moves are left.",
        "5. The player with the most pieces on the board wins.",
        "",
        "Press 'Next' to start the game."
    ]

    button_rect = pygame.Rect(BOARD_WIDTH // 2 - 75, WINDOW_HEIGHT - 100, 150, 50)

    while True:
        screen.fill((41, 82, 64))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    return  # Exit the rules screen to start the game

        # Draw the rules text without scrolling
        y_offset = 50  # Start from the top
        for line in rules_text:
            words = line.split(" ")
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                text_surface = font.render(test_line, True, WHITE)
                if text_surface.get_width() > BOARD_WIDTH - 100:  # Adjust for margins
                    screen.blit(font.render(current_line, True, WHITE), (50, y_offset))
                    y_offset += 30  # Space between lines
                    current_line = word + " "  # Start new line
                else:
                    current_line = test_line

            # Draw the last line if there is one
            if current_line:
                screen.blit(font.render(current_line, True, WHITE), (50, y_offset))
                y_offset += 30  # Space between lines

            # Check if we can stop drawing
            if y_offset > WINDOW_HEIGHT - 150:  # Leave space for the button
                break

        # Draw the button
        pygame.draw.rect(screen, (168, 212, 177), button_rect, border_radius=15)
        button_text = font.render("Next", True, BLACK)
        screen.blit(button_text, (button_rect.x + 50, button_rect.y + 10))

        pygame.display.flip()
        clock.tick(FPS)

def show_difficulty_selection():
    font = pygame.font.Font(None, 36)
    heading_font = pygame.font.Font(None, 48)  # Use a larger font for the heading
    heading_text = heading_font.render("Select Difficulty Level", True, WHITE)  # Create the heading text
    difficulties = ["Beginner", "Intermediate", "Advanced"]
    button_rects = []

    for i, difficulty in enumerate(difficulties):
        button_rects.append(pygame.Rect(BOARD_WIDTH // 3, BOARD_HEIGHT // 2 + i * 60, BOARD_WIDTH // 3, 40))

    while True:
        screen.fill((41, 82, 64))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(event.pos):
                        if i == 0:  # Beginner
                            return 2, 0, "value_table_beginner.pkl"  # Depth 2, Learning rate 0.01
                        elif i == 1:  # Intermediate
                            return 4, 0.05, "value_table_intermediate.pkl"  # Depth 4, Learning rate 0.05
                        elif i == 2:  # Advanced
                            return 8, 0.1, "value_table_advanced.pkl"  # Depth 6, Learning rate 0.1

        # Draw heading
        screen.blit(heading_text, (BOARD_WIDTH // 2 - heading_text.get_width() // 2, BOARD_HEIGHT // 2 - 100))

        # Draw buttons
        for i, rect in enumerate(button_rects):
            pygame.draw.rect(screen, LIGHT_GREEN, rect, border_radius=10)  # Rounded button
            # Center text
            text = font.render(difficulties[i], True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(FPS)


def flip_in_direction(row, col, d_row, d_col, player, board_state):
    opponent = 'W' if player == 'B' else 'B'
    flips = []
    r, c = row + d_row, col + d_col

    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board_state[r][c] == opponent:
        flips.append((r, c))
        r += d_row
        c += d_col

    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board_state[r][c] == player:
        return flips
    return []


def is_valid_move(row, col, player, board_state):
    if board_state[row][col] is not None:
        return False, []

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    flips = []

    for d_row, d_col in directions:
        flips_in_direction = flip_in_direction(row, col, d_row, d_col, player, board_state)
        flips += flips_in_direction

    return len(flips) > 0, flips


def place_piece(row, col, player):
    valid, flips = is_valid_move(row, col, player, board)
    if not valid:
        return False

    # Add each piece to flip to flipping_pieces if it’s not yet the player's color
    for r, c in flips:
        if board[r][c] != player:
            flipping_pieces.append([r, c, board[r][c], player, 0])  # Add to animation list

    board[row][col] = player  # Place the new piece
    return True


def switch_player(current_player):
    return 'W' if current_player == 'B' else 'B'

def evaluate_board(board_state, player):
    opponent = 'W' if player == 'B' else 'B'
    player_score = 0
    opponent_score = 0
    for row in board_state:
        for cell in row:
            if cell == player:
                player_score += 1
            elif cell == opponent:
                opponent_score += 1
    return player_score - opponent_score + (player_score * 0.5)

POSITION_WEIGHTS = [
    [100, -10, 10, 5, 5, 10, -10, 100],
    [-10, -20, 1, 1, 1, 1, -20, -10],
    [10, 1, 5, 2, 2, 5, 1, 10],
    [5, 1, 2, 1, 1, 2, 1, 5],
    [5, 1, 2, 1, 1, 2, 1, 5],
    [10, 1, 5, 2, 2, 5, 1, 10],
    [-10, -20, 1, 1, 1, 1, -20, -10],
    [100, -10, 10, 5, 5, 10, -10, 100]
]

def evaluate_board_with_position(board_state, player):
    opponent = 'W' if player == 'B' else 'B'
    player_score = 0
    opponent_score = 0
    for row in range(8):
        for col in range(8):
            if board_state[row][col] == player:
                player_score += POSITION_WEIGHTS[row][col]
            elif board_state[row][col] == opponent:
                opponent_score += POSITION_WEIGHTS[row][col]
    return player_score - opponent_score

def mobility(board_state, player):
    player_moves = len(get_valid_moves(player, board_state))
    opponent = 'W' if player == 'B' else 'B'
    opponent_moves = len(get_valid_moves(opponent, board_state))
    return player_moves - opponent_moves

def combined_evaluation(board_state, player):
    position_score = evaluate_board_with_position(board_state, player)
    mobility_score = mobility(board_state, player)
    return position_score + (2 * mobility_score)


def get_valid_moves(player, board_state):
    valid_moves = []
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            if board_state[x][y] is None and move_would_flip(board_state, (x, y), player):
                valid_moves.append((x, y))
    return valid_moves


def highlight_valid_moves(player,board_state):
    valid_moves = get_valid_moves(player,board_state)
    for row, col in valid_moves:
        center = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
        pygame.draw.circle(screen, LIGHT_GREEN, center, CELL_SIZE // 2 - 5, 3)

def is_unstable(board_state, player):
    # Determine if the board state is "unstable" by checking for moves that lead to large flips.
    # This is a simplified example and can be customized further.
    opponent = 'W' if player == 'B' else 'B'
    for move in get_valid_moves(player, board_state):
        temp_board = copy.deepcopy(board_state)
        make_move(temp_board, move[0], move[1], player)
        flipped_discs = count_flipped_discs(temp_board, move, player)  # Assume you have a function like this
        if flipped_discs > 3:  # Arbitrary threshold, you can tune this based on testing
            return True
    return False


def move_would_flip(board_state, move, player):
    opponent = 'W' if player == 'B' else 'B'
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]

    # Check if the move position is valid (must be None, not occupied)
    if move[0] < 0 or move[0] >= BOARD_SIZE or move[1] < 0 or move[1] >= BOARD_SIZE:
        return False
    if board_state[move[0]][move[1]] is not None:
        return False

    # Check each direction for valid flips
    for dx, dy in directions:
        x, y = move[0] + dx, move[1] + dy
        has_opponent_between = False
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board_state[x][y] == opponent:
            has_opponent_between = True
            x += dx
            y += dy
        if has_opponent_between and 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board_state[x][y] == player:
            return True
    return False

def count_flipped_discs(board_state, move, player):
    opponent = 'W' if player == 'B' else 'B'
    flip_count = 0
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]

    for dx, dy in directions:
        x, y = move[0] + dx, move[1] + dy
        discs_to_flip = []
        while 0 <= x < 8 and 0 <= y < 8 and board_state[x][y] == opponent:
            discs_to_flip.append((x, y))
            x += dx
            y += dy
        if 0 <= x < 8 and 0 <= y < 8 and board_state[x][y] == player:
            flip_count += len(discs_to_flip)  # Only count if we end at a player disc
    return flip_count


def quiescence_search(board_state, alpha, beta, player, depth=2):
    stand_pat = combined_evaluation(board_state, player)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    opponent = 'W' if player == 'B' else 'B'
    for move in get_valid_moves(player, board_state):
        temp_board = copy.deepcopy(board_state)
        make_move(temp_board, move[0], move[1], player)
        score = -quiescence_search(temp_board, -beta, -alpha, opponent, depth - 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


# Integrate Quiescence Search into the Alpha-Beta Pruning function
def alpha_beta_pruning(depth, maximizing_player, player, board_state, alpha, beta):
    opponent = 'W' if player == 'B' else 'B'

    # Base case
    if depth == 0 or not get_valid_moves(player, board_state):
        # Call quiescence search if the board is unstable, otherwise evaluate directly
        if is_unstable(board_state, player):
            return quiescence_search(board_state, alpha, beta, player), None
        else:
            return combined_evaluation(board_state, player), None

    # Alpha-Beta with Maximizing and Minimizing Logic
    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        for move in get_valid_moves(player, board_state):
            temp_board = copy.deepcopy(board_state)
            make_move(temp_board, move[0], move[1], player)
            evaluation, _ = alpha_beta_pruning(depth - 1, False, opponent, temp_board, alpha, beta)
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for move in get_valid_moves(player, board_state):
            temp_board = copy.deepcopy(board_state)
            make_move(temp_board, move[0], move[1], player)
            evaluation, _ = alpha_beta_pruning(depth - 1, True, opponent, temp_board, alpha, beta)
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval, best_move


def ai_move(player, board_state):
    _, best_move = alpha_beta_pruning(DEPTH, True, player, board_state, float('-inf'), float('inf'))
    return best_move


def make_move(board_state, x, y, player):
    opponent = 'W' if player == 'B' else 'B'
    board_state[x][y] = player  # Place the player's disc at the chosen position
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]

    # Check each direction to see if there are opponent discs that can be flipped
    for dx, dy in directions:
        path = []
        nx, ny = x + dx, y + dy
        # Traverse along the direction
        while 0 <= nx < 8 and 0 <= ny < 8 and board_state[nx][ny] == opponent:
            path.append((nx, ny))  # Record opponent positions along the path
            nx += dx
            ny += dy
        # Only flip if there's a player disc at the end of the path
        if 0 <= nx < 8 and 0 <= ny < 8 and board_state[nx][ny] == player:
            # Flip all discs in the recorded path
            for px, py in path:
                board_state[px][py] = player


def game_over():
    # Check if either player has valid moves
    black_moves = get_valid_moves('B', board)
    white_moves = get_valid_moves('W', board)

    # Also check if the board is full
    is_board_full = all(all(cell is not None for cell in row) for row in board)

    # Game is only over if BOTH players have no valid moves OR the board is full
    return (len(black_moves) == 0 and len(white_moves) == 0) or is_board_full



def display_winner():
    black_score = sum(row.count('B') for row in board)
    white_score = sum(row.count('W') for row in board)

    font = pygame.font.Font(None, 36)
    if black_score > white_score:
        text = font.render("Congratulations! You win!", True, WHITE)
    elif white_score > black_score:
        text = font.render("AI wins. Better luck next time!", True, WHITE)
    else:
        text = font.render("It's a tie!", True, WHITE)

    text_rect = text.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2))
    overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    screen.blit(text, text_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

# # At the start of the program, load the value table
# value_table = load_value_table()


# Modify main game loop to incorporate TD learning updates
def main():
    running = True
    current_player = 'B'  # Human player (Black)
    previous_board = None
    game_history = []  # Track moves for learning

    show_name_entry_dialog()
    show_rules_screen()
    depth, learning_rate, knowledge_file = show_difficulty_selection()
    initialize_board()

    load_value_table(knowledge_file)

    while running:
        draw_board()
        draw_scoreboard(current_player)
        draw_pieces()
        update_flipping_pieces()
        draw_flipping_pieces()

        if current_player == 'B':
            highlight_valid_moves(current_player, board)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_value_table(knowledge_file)  # Save before quitting
                pygame.quit()
                sys.exit()

            if current_player == 'B' and event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_board_position(pos)

                if place_piece(row, col, current_player):
                    # Store state for learning
                    game_history.append((copy.deepcopy(previous_board) if previous_board else None,
                                         copy.deepcopy(board)))
                    previous_board = copy.deepcopy(board)
                    current_player = switch_player(current_player)

        if current_player == 'W' and not flipping_pieces:
            board_copy = copy.deepcopy(board)
            ai_move_position = select_move_with_td(current_player, board_copy)

            if ai_move_position:
                place_piece(ai_move_position[0], ai_move_position[1], current_player)
                # Store state for learning
                game_history.append((copy.deepcopy(previous_board) if previous_board else None,
                                     copy.deepcopy(board)))
                previous_board = copy.deepcopy(board)
                current_player = switch_player(current_player)

        if game_over():
            # Calculate final reward based on game outcome
            black_score = sum(row.count('B') for row in board)
            white_score = sum(row.count('W') for row in board)

            final_reward = 1 if black_score > white_score else (-1 if white_score > black_score else 0)

            # Apply TD updates for the entire game history
            for prev_state, curr_state in game_history:
                if prev_state is not None:
                    td_update(prev_state, curr_state,
                              reward=final_reward if curr_state == board else 0, alpha=learning_rate)

            # Save the updated value table
            save_value_table(knowledge_file)

            display_winner()
            running = False

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    # # Load value table at start
    # if os.path.exists(KNOWLEDGE_FILE):
    #     with open(KNOWLEDGE_FILE, 'rb') as f:
    #         value_table = pickle.load(f)
    # else:
    #     value_table = {}

    main()