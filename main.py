import pygame as p
import chess_engine

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

def load_images():
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK',
              'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        # Using convert_alpha for better performance with transparent backgrounds if images have them
        IMAGES[piece] = p.transform.scale(
            p.image.load("images/" + piece + ".png").convert_alpha(), (SQ_SIZE, SQ_SIZE))

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = chess_engine.GameState()
    valid_moves = gs.get_valid_moves()
    move_made = False
    load_images()
    running = True
    sq_selected = ()  # No square is selected initially, keeps track of the last click (row, col)
    player_clicks = []  # Keeps track of player clicks (two tuples: [(6,4), (4,4)])
    game_over = False
    move_log_font = p.font.SysFont("Arial", 14, False, False) # For move log

    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            # Mouse handling
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  # (x, y) location of mouse
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE

                    if sq_selected == (row, col):  # User clicked the same square twice
                        sq_selected = ()  # Deselect
                        player_clicks = []  # Clear player clicks
                    else:
                        sq_selected = (row, col)
                        player_clicks.append(sq_selected)

                    if len(player_clicks) == 2:  # After 2nd click
                        move = chess_engine.Move(player_clicks[0], player_clicks[1], gs.board,
                                                is_en_passant_move=False, is_castle_move=False) # Default to False, will be updated by engine
                        # Check for en passant and castling flags manually if not handled in Move __init__ for display
                        # This part could be cleaner if Move object itself determined its type more robustly during creation

                        # Validate move
                        valid_move_found = False
                        for valid_move in valid_moves:
                            if move == valid_move: # Use __eq__ for comparison
                                # Overwrite move with the actual valid_move from the engine (which includes special move flags)
                                move = valid_move
                                gs.make_move(move)
                                move_made = True
                                sq_selected = ()  # Reset user clicks
                                player_clicks = []
                                valid_move_found = True
                                break # Exit loop once valid move is found
                        
                        if not valid_move_found:
                            # Invalid move, keep the first square selected and clear the second click
                            player_clicks = [sq_selected]
                            print("Invalid move!") # For debugging, could show a message on screen

            # Key handling
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # Undo move when 'z' is pressed
                    gs.undo_move()
                    move_made = True
                    game_over = False # Game is no longer over if you undo a checkmate/stalemate
                if e.key == p.K_r: # Reset game when 'r' is pressed
                    gs = chess_engine.GameState()
                    valid_moves = gs.get_valid_moves()
                    sq_selected = ()
                    player_clicks = []
                    move_made = False
                    game_over = False


        if move_made:
            valid_moves = gs.get_valid_moves()
            move_made = False

        draw_game_state(screen, gs, valid_moves, sq_selected, move_log_font)

        if gs.checkmate:
            game_over = True
            text = "Black wins by checkmate" if gs.white_to_move else "White wins by checkmate"
            draw_end_game_text(screen, text)
        elif gs.stalemate:
            game_over = True
            draw_end_game_text(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()

def highlight_squares(screen, gs, valid_moves, sq_selected):
    """
    Highlights the selected square and possible moves for that piece.
    """
    if sq_selected: # Only highlight if a square is selected
        r, c = sq_selected
        # Check if the selected piece belongs to the current player
        if gs.board[r][c][0] == ('w' if gs.white_to_move else 'b'):
            # Highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100) # Transparency value 0-255
            s.fill(p.Color('blue'))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

            # Highlight possible moves
            s.fill(p.Color('green'))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE))

def draw_game_state(screen, gs, valid_moves, sq_selected, move_log_font):
    """
    Draws the board, pieces, and potentially the move log.
    """
    draw_board(screen)
    highlight_squares(screen, gs, valid_moves, sq_selected)
    draw_pieces(screen, gs.board)
    draw_move_log(screen, gs, move_log_font) # New: Draw move log

def draw_board(screen):
    """
    Draws the squares on the board.
    """
    colors = [p.Color("#eeeed2"), p.Color("#769656")] # Lighter and darker green for chess board
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_pieces(screen, board):
    """
    Draws the pieces on the board according to the current game state.
    """
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_move_log(screen, gs, font):
    """
    Draws the move log on the screen.
    """
    move_log_rect = p.Rect(WIDTH, 0, 200, HEIGHT) # Assuming we extend WIDTH to make space
    p.draw.rect(screen, p.Color("black"), move_log_rect)
    move_log_string = ""
    for i, move in enumerate(gs.move_log):
        if i % 2 == 0:
            move_log_string += str(i // 2 + 1) + ". " + move.get_chess_notation() + " "
        else:
            move_log_string += move.get_chess_notation() + "  "

    # For simplicity, just render the whole string. For long games, this would need scrolling.
    text_object = font.render(move_log_string, True, p.Color("white"))
    screen.blit(text_object, p.Rect(WIDTH + 5, 5, 200, HEIGHT))


def draw_end_game_text(screen, text):
    """
    Displays game over text in the center of the screen.
    """
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_obj = font.render(text, 0, p.Color("Gray")) # Use a darker color for visibility
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH / 2 - text_obj.get_width() / 2, HEIGHT / 2 - text_obj.get_height() / 2)
    screen.blit(text_obj, text_location)
    text_obj = font.render(text, 0, p.Color("Black")) # Outline effect
    screen.blit(text_obj, text_location.move(2, 2))


if __name__ == "__main__":
    main()