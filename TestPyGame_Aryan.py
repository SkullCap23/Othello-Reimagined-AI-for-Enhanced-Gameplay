import pygame
import sys
import math
import copy

#--------------DQN Libraries-----------
# import torch
# import torch.nn as nn
# import torch.optim as optim
# import random
# import numpy as np
#--------------------------------------

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
FPS = 90

# Set up the display
screen = pygame.display.set_mode((BOARD_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Othello by Project X")
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
    for piece in flipping_pieces:
        piece[4] += 1  # Move the frame forward

        if piece[4] >= FLIP_DURATION:
            # After the animation is complete, finalize the flip
            board[piece[0]][piece[1]] = piece[3]  # Change to the final color (B or W)
            flipping_pieces.remove(piece)


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
    logo = pygame.image.load(r"C:\Users\Aarya\Desktop\othello.png")
    logo = pygame.transform.scale(logo, (460, 215))

    # Load the team logo for the bottom
    bottom_image = pygame.image.load(r"C:\Users\Aarya\Desktop\project_x.png")
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
                            return 2
                        elif i == 1:  # Intermediate
                            return 4
                        elif i == 2:  # Advanced
                            return 6
                        # elif i == 3:
                        #     return 8

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

    # Queue all pieces that will flip and start the animation
    for r, c in flips:
        flipping_pieces.append([r, c, board[r][c], player, 0])

    board[row][col] = player  # Place the new piece
    return True


def switch_player(current_player):
    return 'W' if current_player == 'B' else 'B'


def evaluate_board(board_state):
    black_score = sum(row.count('B') for row in board_state)
    white_score = sum(row.count('W') for row in board_state)
    return black_score - white_score


def get_valid_moves(player, board_state):
    valid_moves = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            valid, _ = is_valid_move(row, col, player, board_state)
            if valid:
                valid_moves.append((row, col))
    return valid_moves


def highlight_valid_moves(player,board_state):
    valid_moves = get_valid_moves(player,board_state)
    for row, col in valid_moves:
        center = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
        pygame.draw.circle(screen, LIGHT_GREEN, center, CELL_SIZE // 2 - 5, 3)


def minimax(depth, maximizing_player, player, board_state, alpha=float('-inf'), beta=float('inf')):
    opponent = 'W' if player == 'B' else 'B'
    if depth == 0 or not get_valid_moves(player, board_state):
        return evaluate_board(board_state), None

    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        for move in get_valid_moves(player, board_state):
            temp_board = copy.deepcopy(board_state)
            make_move(temp_board, move[0], move[1], player)
            evaluation, _ = minimax(depth - 1, False, opponent, temp_board, alpha, beta)
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:  # Beta cut-off
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for move in get_valid_moves(player, board_state):
            temp_board = copy.deepcopy(board_state)
            make_move(temp_board, move[0], move[1], player)
            evaluation, _ = minimax(depth - 1, True, opponent, temp_board, alpha, beta)
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:  # Alpha cut-off
                break
        return min_eval, best_move


def ai_move(player, board_state, depth):
    _, move = minimax(depth, True, player, board_state)
    return move

def make_move(board_state, row, col, player):
    valid, flips = is_valid_move(row, col, player, board_state)
    if not valid:
        return False
    board_state[row][col] = player
    for r, c in flips:
        board_state[r][c] = player
    return True


def game_over():
    # Check if the board is full or if neither player has valid moves
    return (all(cell is not None for row in board for cell in row) or
            (not get_valid_moves('B', board) and not get_valid_moves('W', board)))


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

    pygame.time.wait(2000)

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False


def main():
    running = True
    current_player = 'B'  # Human player (Black)

    show_name_entry_dialog()
    depth = show_difficulty_selection()
    show_rules_screen()  # Show rules after name entry
    initialize_board()

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
                pygame.quit()
                sys.exit()

            if current_player == 'B' and event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_board_position(pos)

                if place_piece(row, col, current_player):
                    current_player = switch_player(current_player)

        # Check for game over after the human player moves
        if game_over():
            display_winner()
            running = False
            break  # Exit the loop if the game is over

        if current_player == 'W' and not flipping_pieces:
            board_copy = copy.deepcopy(board)
            ai_move_position = ai_move(current_player, board_copy, depth)
            if ai_move_position:
                place_piece(ai_move_position[0], ai_move_position[1], current_player)
                current_player = switch_player(current_player)

        # Check for game over after the AI moves
        if game_over():
            display_winner()
            running = False
            break  # Exit the loop if the game is over

        # Check if the current player has no valid moves
        if not get_valid_moves(current_player, board):
            current_player = switch_player(current_player)
            # If the new current player also has no valid moves, the game is over
            if not get_valid_moves(current_player, board):
                display_winner()
                running = False
                break

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()