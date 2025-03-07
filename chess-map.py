import chess
import chess.svg
import chess.pgn
import chess.engine
import pygame
import sys

# Constants
WIDTH, HEIGHT = 640, 720
SQUARE_SIZE = WIDTH // 8
BUTTON_HEIGHT = 40
BUTTON_COLOR = (50, 50, 50)
BUTTON_TEXT_COLOR = (255, 255, 255)
TOGGLE_BUTTON_COLOR = (70, 70, 70)


def load_images():
    pieces = {}
    for piece in "PRNBQKprnbqk":
        pieces[piece] = pygame.image.load(f"images/{piece}.png")
    return pieces


def calculate_attack_map(board, color):
    attack_map = [[0] * 8 for _ in range(8)]
    for square in chess.SQUARES:
        if board.attackers(color, square):
            rank, file = divmod(square, 8)
            attack_map[7 - rank][file] = len(board.attackers(color, square))
    return attack_map


def draw_board(
    screen,
    white_attack_map,
    black_attack_map,
    selected_square=None,
    legal_moves=None,
    show_white_attacks=True,
    show_black_attacks=True,
):
    colors = [pygame.Color("white"), pygame.Color("gray")]
    for rank in range(8):
        for file in range(8):
            color = colors[(rank + file) % 2]
            pygame.draw.rect(
                screen,
                color,
                pygame.Rect(
                    file * SQUARE_SIZE, rank * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE
                ),
            )

            # Draw heatmap overlay for white attacks
            if show_white_attacks:
                white_intensity = min(white_attack_map[rank][file] * 50, 255)
                if white_intensity > 0:
                    alpha = min(white_intensity, 255)
                    heatmap_color = (255, 0, 0, alpha)
                    heatmap_surface = pygame.Surface(
                        (SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA
                    )
                    heatmap_surface.fill(heatmap_color)
                    screen.blit(
                        heatmap_surface, (file * SQUARE_SIZE, rank * SQUARE_SIZE)
                    )

            # Draw heatmap overlay for black attacks
            if show_black_attacks:
                black_intensity = min(black_attack_map[rank][file] * 50, 255)
                if black_intensity > 0:
                    alpha = min(black_intensity, 255)
                    heatmap_color = (0, 0, 255, alpha)
                    heatmap_surface = pygame.Surface(
                        (SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA
                    )
                    heatmap_surface.fill(heatmap_color)
                    screen.blit(
                        heatmap_surface, (file * SQUARE_SIZE, rank * SQUARE_SIZE)
                    )

    # Highlight selected square and legal moves
    if selected_square is not None:
        rank, file = divmod(selected_square, 8)
        highlight_color = (0, 255, 0, 100)  # Green
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight_surface.fill(highlight_color)
        screen.blit(highlight_surface, (file * SQUARE_SIZE, (7 - rank) * SQUARE_SIZE))

        if legal_moves:
            for move in legal_moves:
                if move.from_square == selected_square:
                    target_rank, target_file = divmod(move.to_square, 8)
                    target_highlight_color = (
                        0,
                        255,
                        255,
                        100,
                    )  # Cyan
                    target_highlight_surface = pygame.Surface(
                        (SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA
                    )
                    target_highlight_surface.fill(target_highlight_color)
                    screen.blit(
                        target_highlight_surface,
                        (target_file * SQUARE_SIZE, (7 - target_rank) * SQUARE_SIZE),
                    )


def draw_pieces(screen, board, images):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            rank, file = divmod(square, 8)
            piece_image = images[piece.symbol()]

            # Calculate the offset to center the piece within the tile
            x_offset = (SQUARE_SIZE - piece_image.get_width()) // 2
            y_offset = (SQUARE_SIZE - piece_image.get_height()) // 2

            # Draw the piece at the centered position
            screen.blit(
                piece_image,
                (file * SQUARE_SIZE + x_offset, (7 - rank) * SQUARE_SIZE + y_offset),
            )


def draw_button(screen, text, font, rect, color):
    pygame.draw.rect(screen, color, rect)
    text_surface = font.render(text, True, BUTTON_TEXT_COLOR)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)
    return rect


def main(fen):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    board = chess.Board(fen)
    images = load_images()
    dragging = False
    selected_square = None
    font = pygame.font.Font(None, 36)

    # Toggles for showing attacks
    show_white_attacks = True
    show_black_attacks = True

    # Stack to keep track of undone moves for redo functionality
    move_stack_undone = []

    while True:
        white_attack_map = calculate_attack_map(board, chess.WHITE)
        black_attack_map = calculate_attack_map(board, chess.BLACK)

        screen.fill(pygame.Color("black"))
        draw_board(
            screen,
            white_attack_map,
            black_attack_map,
            selected_square,
            board.legal_moves if selected_square else None,
            show_white_attacks,
            show_black_attacks,
        )
        draw_pieces(screen, board, images)

        # Draw buttons
        undo_button_rect = pygame.Rect(
            0, HEIGHT - BUTTON_HEIGHT * 2, WIDTH // 2, BUTTON_HEIGHT
        )
        redo_button_rect = pygame.Rect(
            WIDTH // 2, HEIGHT - BUTTON_HEIGHT * 2, WIDTH // 2, BUTTON_HEIGHT
        )
        white_toggle_button_rect = pygame.Rect(
            0, HEIGHT - BUTTON_HEIGHT, WIDTH // 2, BUTTON_HEIGHT
        )
        black_toggle_button_rect = pygame.Rect(
            WIDTH // 2, HEIGHT - BUTTON_HEIGHT, WIDTH // 2, BUTTON_HEIGHT
        )

        draw_button(screen, "Undo Move", font, undo_button_rect, BUTTON_COLOR)
        draw_button(screen, "Redo Move", font, redo_button_rect, BUTTON_COLOR)
        draw_button(
            screen,
            f"White Attacks: {'Y' if show_white_attacks else 'N'}",
            font,
            white_toggle_button_rect,
            TOGGLE_BUTTON_COLOR,
        )
        draw_button(
            screen,
            f"Black Attacks: {'Y' if show_black_attacks else 'N'}",
            font,
            black_toggle_button_rect,
            TOGGLE_BUTTON_COLOR,
        )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if undo_button_rect.collidepoint(x, y):  # Undo Move button
                    if len(board.move_stack) > 0:
                        move = board.pop()  # Undo the last move
                        move_stack_undone.append(move)  # Add to undone stack
                elif redo_button_rect.collidepoint(x, y):  # Redo Move button
                    if len(move_stack_undone) > 0:
                        move = move_stack_undone.pop()  # Pop from undone stack
                        board.push(move)  # Redo the move
                elif white_toggle_button_rect.collidepoint(
                    x, y
                ):  # Toggle White Attacks
                    show_white_attacks = not show_white_attacks
                elif black_toggle_button_rect.collidepoint(
                    x, y
                ):  # Toggle Black Attacks
                    show_black_attacks = not show_black_attacks
                else:
                    file, rank = x // SQUARE_SIZE, 7 - (y // SQUARE_SIZE)
                    square = chess.square(file, rank)
                    if board.piece_at(square):
                        selected_square = square
                        dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging:
                    x, y = event.pos
                    file, rank = x // SQUARE_SIZE, 7 - (y // SQUARE_SIZE)
                    target_square = chess.square(file, rank)
                    move = chess.Move(selected_square, target_square)
                    if move in board.legal_moves:
                        board.push(move)
                        move_stack_undone.clear()  # Clear redo stack after a new move
                    dragging = False
                    selected_square = None

        clock.tick(60)


fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # Initial position
main(fen)
