#!/usr/bin/env python3
"""
Bitboard implementation for efficient chess board representation and move generation.
"""

from collections.abc import Iterator
from typing import ClassVar

import chess


class Bitboard:
    """Efficient bitboard representation for chess positions"""

    # File masks (ranks 0-7)
    FILES: ClassVar[list[int]] = [0x0101010101010101 << i for i in range(8)]

    # Rank masks (files 0-7)
    RANKS: ClassVar[list[int]] = [0xFF << (8 * i) for i in range(8)]

    # Diagonal masks
    DIAGONALS: ClassVar[list[int]] = []
    ANTI_DIAGONALS: ClassVar[list[int]] = []

    # Initialize diagonal masks
    for i in range(15):
        diagonal = 0
        anti_diagonal = 0
        for j in range(8):
            if 0 <= i - j < 8 and 0 <= j < 8:
                diagonal |= 1 << (j * 8 + (i - j))
            if 0 <= i - j < 8 and 0 <= (7 - j) < 8:
                anti_diagonal |= 1 << ((7 - j) * 8 + (i - j))
        DIAGONALS.append(diagonal)
        ANTI_DIAGONALS.append(anti_diagonal)

    def __init__(self, value: int = 0):
        self.value = value & 0xFFFFFFFFFFFFFFFF  # Ensure 64-bit

    def __hash__(self):
        return hash(self.value)

    def __and__(self, other):
        return Bitboard(self.value & other.value)

    def __or__(self, other):
        return Bitboard(self.value | other.value)

    def __xor__(self, other):
        return Bitboard(self.value ^ other.value)

    def __invert__(self):
        return Bitboard(~self.value)

    def __lshift__(self, shift):
        return Bitboard(self.value << shift)

    def __rshift__(self, shift):
        return Bitboard(self.value >> shift)

    def __eq__(self, other):
        return self.value == other.value

    def __bool__(self):
        return self.value != 0

    def __int__(self):
        return self.value

    def __str__(self):
        return f"Bitboard(0x{self.value:016x})"

    def __repr__(self):
        return self.__str__()

    def set_bit(self, square: int):
        """Set bit at given square"""
        self.value |= 1 << square

    def clear_bit(self, square: int):
        """Clear bit at given square"""
        self.value &= ~(1 << square)

    def get_bit(self, square: int) -> bool:
        """Get bit at given square"""
        return bool(self.value & (1 << square))

    def popcount(self) -> int:
        """Count number of set bits"""
        return self.value.bit_count()

    def lsb(self) -> int:
        """Get least significant bit position"""
        if self.value == 0:
            return -1
        return (self.value & -self.value).bit_length() - 1

    def msb(self) -> int:
        """Get most significant bit position"""
        if self.value == 0:
            return -1
        return self.value.bit_length() - 1

    def bitscan_forward(self) -> Iterator[int]:
        """Iterate through set bits from LSB to MSB"""
        temp = self.value
        while temp:
            bit = temp & -temp
            yield bit.bit_length() - 1
            temp &= temp - 1

    def bitscan_reverse(self) -> Iterator[int]:
        """Iterate through set bits from MSB to LSB"""
        temp = self.value
        while temp:
            bit = 1 << (temp.bit_length() - 1)
            yield bit.bit_length() - 1
            temp &= temp - 1

    def to_squares(self) -> list[int]:
        """Convert bitboard to list of square indices"""
        return list(self.bitscan_forward())

    def from_squares(self, squares: list[int]) -> "Bitboard":
        """Create bitboard from list of square indices"""
        result = Bitboard()
        for square in squares:
            result.set_bit(square)
        return result

    def print_board(self):
        """Print bitboard as 8x8 grid"""
        for rank in range(7, -1, -1):
            row = ""
            for file in range(8):
                square = rank * 8 + file
                if self.get_bit(square):
                    row += "1 "
                else:
                    row += ". "
            print(f"{rank + 1} {row}")
        print("  a b c d e f g h")


class BitboardBoard:
    """Chess board using bitboard representation"""

    def __init__(self, board: chess.Board | None = None):
        # Piece bitboards for each color and piece type
        self.pieces = {}
        for color in [chess.WHITE, chess.BLACK]:
            for piece_type in chess.PIECE_TYPES:
                self.pieces[(color, piece_type)] = Bitboard()

        # Combined bitboards
        self.white_pieces = Bitboard()
        self.black_pieces = Bitboard()
        self.all_pieces = Bitboard()

        # Occupancy bitboards for each file, rank, diagonal
        self.file_occupancy = [Bitboard() for _ in range(8)]
        self.rank_occupancy = [Bitboard() for _ in range(8)]
        self.diagonal_occupancy = [Bitboard() for _ in range(15)]
        self.anti_diagonal_occupancy = [Bitboard() for _ in range(15)]

        if board:
            self.from_chess_board(board)

    def from_chess_board(self, board: chess.Board):
        """Initialize from python-chess board"""
        # Clear all bitboards
        for key in self.pieces:
            self.pieces[key] = Bitboard()

        self.white_pieces = Bitboard()
        self.black_pieces = Bitboard()
        self.all_pieces = Bitboard()

        # Set pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                self.pieces[(piece.color, piece.piece_type)].set_bit(square)

                if piece.color == chess.WHITE:
                    self.white_pieces.set_bit(square)
                else:
                    self.black_pieces.set_bit(square)

                self.all_pieces.set_bit(square)

        self._update_occupancy_bitboards()

    def to_chess_board(self) -> chess.Board:
        """Convert to python-chess board"""
        board = chess.Board()
        board.clear()

        for square in chess.SQUARES:
            for color in [chess.WHITE, chess.BLACK]:
                for piece_type in chess.PIECE_TYPES:
                    if self.pieces[(color, piece_type)].get_bit(square):
                        piece = chess.Piece(piece_type, color)
                        board.set_piece_at(square, piece)

        return board

    def _update_occupancy_bitboards(self):
        """Update file, rank, and diagonal occupancy bitboards"""
        # Clear occupancy bitboards
        for i in range(8):
            self.file_occupancy[i] = Bitboard()
            self.rank_occupancy[i] = Bitboard()
        for i in range(15):
            self.diagonal_occupancy[i] = Bitboard()
            self.anti_diagonal_occupancy[i] = Bitboard()

        # Set occupancy
        for square in self.all_pieces.to_squares():
            file = square % 8
            rank = square // 8
            diagonal = file + rank
            anti_diagonal = file - rank + 7

            self.file_occupancy[file].set_bit(square)
            self.rank_occupancy[rank].set_bit(square)
            self.diagonal_occupancy[diagonal].set_bit(square)
            self.anti_diagonal_occupancy[anti_diagonal].set_bit(square)

    def get_piece_at(self, square: int) -> tuple[chess.Color, chess.PieceType] | None:
        """Get piece at square"""
        for color in [chess.WHITE, chess.BLACK]:
            for piece_type in chess.PIECE_TYPES:
                if self.pieces[(color, piece_type)].get_bit(square):
                    return (color, piece_type)
        return None

    def make_move(self, move: chess.Move) -> "BitboardBoard":
        """Make a move and return new board"""
        new_board = BitboardBoard()

        # Copy all piece bitboards
        for key in self.pieces:
            new_board.pieces[key] = Bitboard(self.pieces[key].value)

        new_board.white_pieces = Bitboard(self.white_pieces.value)
        new_board.black_pieces = Bitboard(self.black_pieces.value)
        new_board.all_pieces = Bitboard(self.all_pieces.value)

        # Handle move
        from_square = move.from_square
        to_square = move.to_square

        # Find the piece being moved
        piece_info = None
        for color in [chess.WHITE, chess.BLACK]:
            for piece_type in chess.PIECE_TYPES:
                if new_board.pieces[(color, piece_type)].get_bit(from_square):
                    piece_info = (color, piece_type)
                    break
            if piece_info:
                break

        if not piece_info:
            return new_board

        color, piece_type = piece_info

        # Remove piece from source square
        new_board.pieces[(color, piece_type)].clear_bit(from_square)

        # Handle capture
        if new_board.all_pieces.get_bit(to_square):
            # Remove captured piece
            for captured_color in [chess.WHITE, chess.BLACK]:
                for captured_type in chess.PIECE_TYPES:
                    if new_board.pieces[(captured_color, captured_type)].get_bit(to_square):
                        new_board.pieces[(captured_color, captured_type)].clear_bit(to_square)
                        break

        # Place piece on destination square
        new_board.pieces[(color, piece_type)].set_bit(to_square)

        # Handle special moves
        if move.promotion:
            # Remove pawn and add promoted piece
            new_board.pieces[(color, chess.PAWN)].clear_bit(to_square)
            new_board.pieces[(color, move.promotion)].set_bit(to_square)
        elif move.uci() == "e1g1" or move.uci() == "e8g8":  # Kingside castling
            # Move rook
            rook_from = to_square + 1
            rook_to = to_square - 1
            new_board.pieces[(color, chess.ROOK)].clear_bit(rook_from)
            new_board.pieces[(color, chess.ROOK)].set_bit(rook_to)
        elif move.uci() == "e1c1" or move.uci() == "e8c8":  # Queenside castling
            # Move rook
            rook_from = to_square - 2
            rook_to = to_square + 1
            new_board.pieces[(color, chess.ROOK)].clear_bit(rook_from)
            new_board.pieces[(color, chess.ROOK)].set_bit(rook_to)
        elif move.uci().endswith("e.p."):  # En passant
            # Remove captured pawn
            captured_pawn_square = to_square + (8 if color == chess.WHITE else -8)
            new_board.pieces[(not color, chess.PAWN)].clear_bit(captured_pawn_square)

        # Update combined bitboards
        new_board.white_pieces = Bitboard()
        new_board.black_pieces = Bitboard()
        new_board.all_pieces = Bitboard()

        for color in [chess.WHITE, chess.BLACK]:
            for piece_type in chess.PIECE_TYPES:
                if color == chess.WHITE:
                    new_board.white_pieces = new_board.white_pieces | new_board.pieces[(color, piece_type)]
                else:
                    new_board.black_pieces = new_board.black_pieces | new_board.pieces[(color, piece_type)]
                new_board.all_pieces = new_board.all_pieces | new_board.pieces[(color, piece_type)]

        new_board._update_occupancy_bitboards()
        return new_board


class BitboardMoveGenerator:
    """Efficient move generation using bitboards"""

    def __init__(self):
        # Precomputed attack tables
        self._init_attack_tables()

    def _init_attack_tables(self):
        """Initialize precomputed attack tables"""
        # Knight attacks
        self.knight_attacks = [Bitboard() for _ in range(64)]
        knight_deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

        for square in range(64):
            rank, file = divmod(square, 8)
            for dr, df in knight_deltas:
                new_rank, new_file = rank + dr, file + df
                if 0 <= new_rank < 8 and 0 <= new_file < 8:
                    self.knight_attacks[square].set_bit(new_rank * 8 + new_file)

        # King attacks
        self.king_attacks = [Bitboard() for _ in range(64)]
        king_deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for square in range(64):
            rank, file = divmod(square, 8)
            for dr, df in king_deltas:
                new_rank, new_file = rank + dr, file + df
                if 0 <= new_rank < 8 and 0 <= new_file < 8:
                    self.king_attacks[square].set_bit(new_rank * 8 + new_file)

        # Pawn attacks
        self.pawn_attacks = {}
        for color in [chess.WHITE, chess.BLACK]:
            self.pawn_attacks[color] = [Bitboard() for _ in range(64)]
            direction = -1 if color == chess.WHITE else 1
            attack_deltas = [(-1, direction), (1, direction)]

            for square in range(64):
                rank, file = divmod(square, 8)
                for dr, df in attack_deltas:
                    new_rank, new_file = rank + dr, file + df
                    if 0 <= new_rank < 8 and 0 <= new_file < 8:
                        self.pawn_attacks[color][square].set_bit(new_rank * 8 + new_file)

    def get_knight_moves(self, square: int, own_pieces: Bitboard) -> Bitboard:
        """Get knight moves from square"""
        return self.knight_attacks[square] & ~own_pieces

    def get_king_moves(self, square: int, own_pieces: Bitboard) -> Bitboard:
        """Get king moves from square"""
        return self.king_attacks[square] & ~own_pieces

    def get_pawn_moves(self, square: int, color: chess.Color, all_pieces: Bitboard, own_pieces: Bitboard) -> Bitboard:
        """Get pawn moves from square"""
        moves = Bitboard()
        rank, file = divmod(square, 8)
        direction = -1 if color == chess.WHITE else 1
        start_rank = 6 if color == chess.WHITE else 1

        # Single push
        new_rank = rank + direction
        if 0 <= new_rank < 8 and not all_pieces.get_bit(new_rank * 8 + file):
            moves.set_bit(new_rank * 8 + file)

            # Double push
            if rank == start_rank:
                new_rank = rank + 2 * direction
                if 0 <= new_rank < 8 and not all_pieces.get_bit(new_rank * 8 + file):
                    moves.set_bit(new_rank * 8 + file)

        # Captures
        for df in [-1, 1]:
            new_file = file + df
            if 0 <= new_file < 8:
                new_rank = rank + direction
                if 0 <= new_rank < 8:
                    target_square = new_rank * 8 + new_file
                    if all_pieces.get_bit(target_square) and not own_pieces.get_bit(target_square):
                        moves.set_bit(target_square)

        return moves

    def get_pawn_attacks(self, square: int, color: chess.Color) -> Bitboard:
        """Get pawn attack squares from square"""
        return self.pawn_attacks[color][square]

    def get_rook_moves(self, square: int, all_pieces: Bitboard, own_pieces: Bitboard) -> Bitboard:
        """Get rook moves from square using bitboard magic"""
        moves = Bitboard()
        rank, file = divmod(square, 8)

        # Horizontal moves
        rank_bb = Bitboard(Bitboard.RANKS[rank])
        occupied = all_pieces & rank_bb
        moves |= self._get_ray_attacks(square, 8, occupied, own_pieces, rank_bb)

        # Vertical moves
        file_bb = Bitboard(Bitboard.FILES[file])
        occupied = all_pieces & file_bb
        moves |= self._get_ray_attacks(square, 1, occupied, own_pieces, file_bb)

        return moves

    def get_bishop_moves(self, square: int, all_pieces: Bitboard, own_pieces: Bitboard) -> Bitboard:
        """Get bishop moves from square using bitboard magic"""
        moves = Bitboard()
        rank, file = divmod(square, 8)

        # Diagonal moves
        diagonal = file + rank
        diagonal_bb = Bitboard(Bitboard.DIAGONALS[diagonal])
        occupied = all_pieces & diagonal_bb
        moves |= self._get_ray_attacks(square, 9, occupied, own_pieces, diagonal_bb)

        # Anti-diagonal moves
        anti_diagonal = file - rank + 7
        anti_diagonal_bb = Bitboard(Bitboard.ANTI_DIAGONALS[anti_diagonal])
        occupied = all_pieces & anti_diagonal_bb
        moves |= self._get_ray_attacks(square, 7, occupied, own_pieces, anti_diagonal_bb)

        return moves

    def get_queen_moves(self, square: int, all_pieces: Bitboard, own_pieces: Bitboard) -> Bitboard:
        """Get queen moves (rook + bishop)"""
        return self.get_rook_moves(square, all_pieces, own_pieces) | self.get_bishop_moves(
            square, all_pieces, own_pieces
        )

    def _get_ray_attacks(
        self, square: int, step: int, occupied: Bitboard, own_pieces: Bitboard, mask: Bitboard
    ) -> Bitboard:
        """Get ray attacks in a direction"""
        moves = Bitboard()

        # Forward direction
        current = square + step
        while current < 64 and mask.get_bit(current):
            moves.set_bit(current)
            if occupied.get_bit(current):
                break
            current += step

        # Backward direction
        current = square - step
        while current >= 0 and mask.get_bit(current):
            moves.set_bit(current)
            if occupied.get_bit(current):
                break
            current -= step

        return moves & ~own_pieces

    def generate_moves(self, board: BitboardBoard, color: chess.Color) -> list[chess.Move]:
        """Generate all legal moves for color"""
        moves = []
        own_pieces = board.white_pieces if color == chess.WHITE else board.black_pieces

        for square in own_pieces.to_squares():
            piece_info = board.get_piece_at(square)
            if not piece_info:
                continue

            _, piece_type = piece_info

            if piece_type == chess.PAWN:
                pawn_moves = self.get_pawn_moves(square, color, board.all_pieces, own_pieces)
                for target_square in pawn_moves.to_squares():
                    # Handle promotion
                    if (color == chess.WHITE and target_square < 8) or (color == chess.BLACK and target_square >= 56):
                        moves.extend(
                            chess.Move(square, target_square, promotion)
                            for promotion in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
                        )
                    else:
                        moves.append(chess.Move(square, target_square))

            elif piece_type == chess.KNIGHT:
                knight_moves = self.get_knight_moves(square, own_pieces)
                moves.extend(chess.Move(square, target_square) for target_square in knight_moves.to_squares())

            elif piece_type == chess.BISHOP:
                bishop_moves = self.get_bishop_moves(square, board.all_pieces, own_pieces)
                moves.extend(chess.Move(square, target_square) for target_square in bishop_moves.to_squares())

            elif piece_type == chess.ROOK:
                rook_moves = self.get_rook_moves(square, board.all_pieces, own_pieces)
                moves.extend(chess.Move(square, target_square) for target_square in rook_moves.to_squares())

            elif piece_type == chess.QUEEN:
                queen_moves = self.get_queen_moves(square, board.all_pieces, own_pieces)
                moves.extend(chess.Move(square, target_square) for target_square in queen_moves.to_squares())

            elif piece_type == chess.KING:
                king_moves = self.get_king_moves(square, own_pieces)
                moves.extend(chess.Move(square, target_square) for target_square in king_moves.to_squares())

        return moves
