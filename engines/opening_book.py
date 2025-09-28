#!/usr/bin/env python3
"""
Opening book integration for the enhanced chess engine.
Provides better opening play by using existing book files.
"""

import os
import random

import chess


class OpeningBook:
    """Simple opening book implementation"""

    def __init__(self, book_path: str | None = None):
        self.book_path = book_path
        self.book_moves: dict[str, list[chess.Move]] = {}
        self.loaded = False

        if book_path and os.path.exists(book_path):
            self.load_book(book_path)

    def load_book(self, book_path: str):
        """Load opening book from file"""
        try:
            # Try to load as a simple text format first
            if book_path.endswith('.txt'):
                self._load_text_book(book_path)
            else:
                # Try to load as binary format
                self._load_binary_book(book_path)
            self.loaded = True
            print(f"Loaded opening book with {len(self.book_moves)} positions")
        except Exception as e:
            print(f"Failed to load opening book: {e}")
            self.loaded = False

    def _load_text_book(self, book_path: str):
        """Load book from text format (FEN -> moves)"""
        with open(book_path) as f:
            for line in f:
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue

                parts = stripped_line.split('|')
                if len(parts) >= 2:
                    fen = parts[0].strip()
                    moves_str = parts[1].strip().split()
                    moves = []

                    for move_str in moves_str:
                        try:
                            move = chess.Move.from_uci(move_str)
                            moves.append(move)
                        except ValueError:
                            continue

                    if moves:
                        self.book_moves[fen] = moves

    def _load_binary_book(self, book_path: str):
        """Load book from binary format (simplified)"""
        # This is a simplified binary format loader
        # In practice, you'd need to implement the specific format
        try:
            with open(book_path, 'rb') as f:
                # Read header
                header = f.read(16)
                if len(header) < 16:
                    return

                # Read entries
                while True:
                    entry = f.read(8)
                    if len(entry) < 8:
                        break

                    # This is a simplified format - in practice you'd need
                    # to implement the actual binary format
        except (OSError, ValueError):
            pass

    def get_move(self, board: chess.Board) -> chess.Move | None:
        """Get a move from the opening book"""
        if not self.loaded:
            return None

        # Try exact FEN match
        fen = board.fen()
        if fen in self.book_moves:
            moves = self.book_moves[fen]
            return random.choice(moves)

        # Try without move counters and castling rights
        fen_parts = fen.split()
        simplified_fen = ' '.join(fen_parts[:4])  # Remove move counters and castling

        for book_fen, moves in self.book_moves.items():
            book_parts = book_fen.split()
            if len(book_parts) >= 4:
                book_simplified = ' '.join(book_parts[:4])
                if simplified_fen == book_simplified:
                    return random.choice(moves)

        return None

    def has_move(self, board: chess.Board) -> bool:
        """Check if there's a move in the book for this position"""
        return self.get_move(board) is not None


class SimpleOpeningBook:
    """Simple hardcoded opening book for common openings"""

    def __init__(self):
        self.opening_moves = {
            # Starting position
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": [
                "e2e4", "d2d4", "g1f3", "c2c4", "b1c3", "f2f4", "g2g3", "b2b3"
            ],

            # After 1.e4
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1": [
                "e7e5", "c7c5", "e7e6", "c7c6", "d7d6", "g8f6", "b8c6", "d7d5"
            ],

            # After 1.d4
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1": [
                "d7d5", "g8f6", "e7e6", "c7c5", "f7f5", "d7d6", "g7g6", "b8c6"
            ],

            # After 1.Nf3 (different position)
            "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R w KQkq - 1 1": [
                "d2d4", "e2e4", "c2c4", "g2g3", "b2b3", "f2f4", "b1c3", "e2e3"
            ],

            # After 1.c4
            "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq c3 0 1": [
                "e7e5", "c7c5", "g8f6", "e7e6", "d7d5", "c7c6", "g7g6", "b8c6"
            ],
        }

    def get_move(self, board: chess.Board) -> chess.Move | None:
        """Get a move from the simple opening book"""
        fen = board.fen()

        # Try exact match first
        if fen in self.opening_moves:
            moves = self.opening_moves[fen]
            move_str = random.choice(moves)
            try:
                return chess.Move.from_uci(move_str)
            except ValueError:
                return None

        # Try without move counters
        fen_parts = fen.split()
        simplified_fen = ' '.join(fen_parts[:4])

        for book_fen, moves in self.opening_moves.items():
            book_parts = book_fen.split()
            if len(book_parts) >= 4:
                book_simplified = ' '.join(book_parts[:4])
                if simplified_fen == book_simplified:
                    move_str = random.choice(moves)
                    try:
                        return chess.Move.from_uci(move_str)
                    except ValueError:
                        return None

        return None

    def has_move(self, board: chess.Board) -> bool:
        """Check if there's a move in the book for this position"""
        return self.get_move(board) is not None


class EnhancedOpeningBook:
    """Enhanced opening book that combines multiple sources"""

    def __init__(self, book_paths: list[str] | None = None):
        self.books = []

        # Add simple book as fallback
        self.books.append(SimpleOpeningBook())

        # Add external books if available
        if book_paths:
            for book_path in book_paths:
                if os.path.exists(book_path):
                    book = OpeningBook(book_path)
                    if book.loaded:
                        self.books.append(book)

        # Add some common opening patterns
        self._add_common_patterns()

    def _add_common_patterns(self):
        """Add common opening patterns"""
        # This could be expanded with more sophisticated pattern matching

    def get_move(self, board: chess.Board) -> chess.Move | None:
        """Get a move from any available book"""
        for book in self.books:
            move = book.get_move(board)
            if move and board.is_legal(move):
                return move
        return None

    def has_move(self, board: chess.Board) -> bool:
        """Check if any book has a move for this position"""
        return any(book.has_move(board) for book in self.books)


def create_simple_book_file(book_path: str):
    """Create a simple opening book file for testing"""
    book_content = """# Simple Opening Book
# Format: FEN|move1 move2 move3 ...
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1|e2e4 d2d4 g1f3 c2c4 b1c3 f2f4 g2g3 b2b3
rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1|e7e5 c7c5 e7e6 c7c6 d7d6 g8f6 b8c6 d7d5
rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1|d7d5 g8f6 e7e6 c7c5 f7f5 d7d6 g7g6 b8c6
rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1|d7d5 e2e4 c7c5 g8f6 e7e6 c7c6 d7d6 g7g6
"""

    with open(book_path, 'w') as f:
        f.write(book_content)


# Example usage and testing
if __name__ == "__main__":
    # Test simple opening book
    print("Testing Simple Opening Book")
    print("=" * 30)

    book = SimpleOpeningBook()
    board = chess.Board()

    print(f"Starting position: {board.fen()}")
    move = book.get_move(board)
    print(f"Book move: {move.uci() if move else 'None'}")

    if move:
        board.push(move)
        print(f"After {move.uci()}: {board.fen()}")

        move2 = book.get_move(board)
        print(f"Book move: {move2.uci() if move2 else 'None'}")

    # Test enhanced book
    print("\nTesting Enhanced Opening Book")
    print("=" * 35)

    enhanced_book = EnhancedOpeningBook()
    board = chess.Board()

    print(f"Starting position: {board.fen()}")
    move = enhanced_book.get_move(board)
    print(f"Book move: {move.uci() if move else 'None'}")

    # Create and test file-based book
    print("\nTesting File-based Opening Book")
    print("=" * 35)

    book_file = "test_book.txt"
    create_simple_book_file(book_file)

    file_book = OpeningBook(book_file)
    board = chess.Board()

    print(f"Starting position: {board.fen()}")
    move = file_book.get_move(board)
    print(f"Book move: {move.uci() if move else 'None'}")

    # Clean up
    if os.path.exists(book_file):
        os.remove(book_file)
