class GameState:
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.en_passant_possible = () # Coordinates for the square where en passant capture is possible
        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]

    def make_move(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move

        if move.piece_moved == 'wK':
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == 'bK':
            self.black_king_location = (move.end_row, move.end_col)

        # Pawn promotion (simplified: always promotes to Queen)
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + 'Q'

        # En Passant update
        if move.piece_moved[1] == 'P' and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row) // 2, move.end_col)
        else:
            self.en_passant_possible = ()

        # En Passant capture
        if move.is_en_passant_move:
            self.board[move.end_row + (1 if move.piece_moved[0] == 'b' else -1)][move.end_col] = "--"

        # Castle move
        if move.is_castle_move:
            if move.end_col - move.start_col == 2: # Kingside castle
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1] # Move rook
                self.board[move.end_row][move.end_col + 1] = "--" # Clear old rook square
            else: # Queenside castle
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2] # Move rook
                self.board[move.end_row][move.end_col - 2] = "--" # Clear old rook square

        # Update castling rights - whenever a King or Rook moves
        self.update_castle_rights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))


    def undo_move(self):
        if self.move_log:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move

            if move.piece_moved == 'wK':
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == 'bK':
                self.black_king_location = (move.start_row, move.start_col)

            # Undo en passant
            if move.is_en_passant_move:
                self.board[move.end_row][move.end_col] = "--" # Remove empty square
                self.board[move.start_row][move.end_col] = move.piece_captured # Restore captured pawn
                self.en_passant_possible = (move.end_row, move.end_col)
            # If the piece moved was a pawn and moved two squares, reset en_passant_possible
            if move.piece_moved[1] == 'P' and abs(move.start_row - move.end_row) == 2:
                self.en_passant_possible = () # This needs to be more robust, potentially checking previous moves

            # Undo castling rights
            self.castle_rights_log.pop() # Remove new castle rights from the move we are undoing
            self.current_castling_rights = self.castle_rights_log[-1] # Set current castle rights to the previous one

            # Undo castle move
            if move.is_castle_move:
                if move.end_col - move.start_col == 2: # Kingside
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = "--"
                else: # Queenside
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = "--"


    def update_castle_rights(self, move):
        if move.piece_moved == 'wK':
            self.current_castling_rights.wks = False
            self.current_castling_rights.wqs = False
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bks = False
            self.current_castling_rights.bqs = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 7:
                    self.current_castling_rights.wks = False
                elif move.start_col == 0:
                    self.current_castling_rights.wqs = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 7:
                    self.current_castling_rights.bks = False
                elif move.start_col == 0:
                    self.current_castling_rights.bqs = False
        # If a rook is captured, castling rights for that side/rook are also lost
        if move.piece_captured == 'wR':
            if move.end_row == 7:
                if move.end_col == 7:
                    self.current_castling_rights.wks = False
                elif move.end_col == 0:
                    self.current_castling_rights.wqs = False
        elif move.piece_captured == 'bR':
            if move.end_row == 0:
                if move.end_col == 7:
                    self.current_castling_rights.bks = False
                elif move.end_col == 0:
                    self.current_castling_rights.bqs = False


    def get_valid_moves(self):
        # 1. Generate all possible moves
        moves = self.get_all_possible_moves()
        # 2. For each move, make the move
        # 3. Generate all opponent's moves
        # 4. For each of opponent's moves, see if they attack the king
        # 5. If king is attacked, it's an invalid move
        # 6. Undo the move
        for i in range(len(moves) - 1, -1, -1):
            self.make_move(moves[i])
            # For pawn promotion, need to consider the actual promoted piece for in_check
            # For simplicity here, it treats it as original pawn, but would need to be smarter
            self.white_to_move = not self.white_to_move # Switch turn back to check if previous player is in check
            if self.in_check():
                moves.remove(moves[i])
            self.white_to_move = not self.white_to_move # Switch turn back to current player
            self.undo_move() # Undo the move to restore board state

        # Add castling moves after filtering basic valid moves
        if self.white_to_move:
            self.get_castle_moves(self.white_king_location[0], self.white_king_location[1], moves)
        else:
            self.get_castle_moves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.in_check():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        return moves

    def in_check(self):
        if self.white_to_move:
            return self.square_under_attack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.square_under_attack(self.black_king_location[0], self.black_king_location[1])

    def square_under_attack(self, r, c):
        # Check from perspective of current player, if the given square is attacked by opponent
        # Temporarily switch turn to opponent to generate their moves
        self.white_to_move = not self.white_to_move
        opponent_moves = self.get_all_possible_moves() # This is the expensive part to optimize
        self.white_to_move = not self.white_to_move # Switch back

        for move in opponent_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False

    def get_all_possible_moves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                    piece = self.board[r][c][1]
                    self.move_functions[piece](self, r, c, moves)
        return moves

    move_functions = {
        'P': lambda self, r, c, moves: self.get_pawn_moves(r, c, moves),
        'R': lambda self, r, c, moves: self.get_rook_moves(r, c, moves),
        'N': lambda self, r, c, moves: self.get_knight_moves(r, c, moves),
        'B': lambda self, r, c, moves: self.get_bishop_moves(r, c, moves),
        'Q': lambda self, r, c, moves: self.get_queen_moves(r, c, moves),
        'K': lambda self, r, c, moves: self.get_king_moves(r, c, moves),
    }

    def get_pawn_moves(self, r, c, moves):
        if self.white_to_move:
            # 1 square pawn advance
            if self.board[r-1][c] == "--":
                moves.append(Move((r, c), (r-1, c), self.board))
                # 2 square pawn advance
                if r == 6 and self.board[r-2][c] == "--":
                    moves.append(Move((r, c), (r-2, c), self.board))
            # captures
            if c-1 >= 0: # captures to the left
                if self.board[r-1][c-1][0] == 'b':
                    moves.append(Move((r, c), (r-1, c-1), self.board))
                elif (r-1, c-1) == self.en_passant_possible: # en passant
                    moves.append(Move((r, c), (r-1, c-1), self.board, is_en_passant_move=True))
            if c+1 <= 7: # captures to the right
                if self.board[r-1][c+1][0] == 'b':
                    moves.append(Move((r, c), (r-1, c+1), self.board))
                elif (r-1, c+1) == self.en_passant_possible: # en passant
                    moves.append(Move((r, c), (r-1, c+1), self.board, is_en_passant_move=True))

        else: # Black pawn moves
            # 1 square pawn advance
            if self.board[r+1][c] == "--":
                moves.append(Move((r, c), (r+1, c), self.board))
                # 2 square pawn advance
                if r == 1 and self.board[r+2][c] == "--":
                    moves.append(Move((r, c), (r+2, c), self.board))
            # captures
            if c-1 >= 0: # captures to the left
                if self.board[r+1][c-1][0] == 'w':
                    moves.append(Move((r, c), (r+1, c-1), self.board))
                elif (r+1, c-1) == self.en_passant_possible: # en passant
                    moves.append(Move((r, c), (r+1, c-1), self.board, is_en_passant_move=True))
            if c+1 <= 7: # captures to the right
                if self.board[r+1][c+1][0] == 'w':
                    moves.append(Move((r, c), (r+1, c+1), self.board))
                elif (r+1, c+1) == self.en_passant_possible: # en passant
                    moves.append(Move((r, c), (r+1, c+1), self.board, is_en_passant_move=True))

    def get_rook_moves(self, r, c, moves):
        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        enemy_color = 'b' if self.white_to_move else 'w'
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_knight_moves(self, r, c, moves):
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2),
                        (1, -2), (2, -1), (1, 2), (2, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        for m in knight_moves:
            end_row = r + m[0]
            end_col = c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_bishop_moves(self, r, c, moves):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        enemy_color = 'b' if self.white_to_move else 'w'
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_queen_moves(self, r, c, moves):
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_king_moves(self, r, c, moves):
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                      (0, 1), (1, -1), (1, 0), (1, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        for i in range(8):
            end_row = r + king_moves[i][0]
            end_col = c + king_moves[i][1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_castle_moves(self, r, c, moves):
        if self.in_check():
            return # Can't castle if in check
        if (self.white_to_move and self.current_castling_rights.wks) or \
           (not self.white_to_move and self.current_castling_rights.bks):
            self._get_kingside_castle_moves(r, c, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or \
           (not self.white_to_move and self.current_castling_rights.bqs):
            self._get_queenside_castle_moves(r, c, moves)

    def _get_kingside_castle_moves(self, r, c, moves):
        if self.board[r][c+1] == "--" and self.board[r][c+2] == "--":
            if not self.square_under_attack(r, c+1) and not self.square_under_attack(r, c+2):
                moves.append(Move((r, c), (r, c+2), self.board, is_castle_move=True))

    def _get_queenside_castle_moves(self, r, c, moves):
        if self.board[r][c-1] == "--" and self.board[r][c-2] == "--" and self.board[r][c-3] == "--":
            if not self.square_under_attack(r, c-1) and not self.square_under_attack(r, c-2):
                moves.append(Move((r, c), (r, c-2), self.board, is_castle_move=True))


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks # white kingside
        self.bks = bks # black kingside
        self.wqs = wqs # white queenside
        self.bqs = bqs # black queenside

class Move:
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, is_en_passant_move=False, is_castle_move=False):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        # Pawn promotion flag
        self.is_pawn_promotion = (self.piece_moved == 'wP' and self.end_row == 0) or \
                                 (self.piece_moved == 'bP' and self.end_row == 7)

        # En passant flag
        self.is_en_passant_move = is_en_passant_move
        if self.is_en_passant_move:
            self.piece_captured = 'wP' if self.piece_moved == 'bP' else 'bP'

        # Castle move flag
        self.is_castle_move = is_castle_move

        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        return isinstance(other, Move) and self.move_id == other.move_id

    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, r, c):
        return self.cols_to_files[c] + self.rows_to_ranks[r]