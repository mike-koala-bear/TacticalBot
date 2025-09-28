#!/usr/bin/env python3
"""
Polyglot opening book reader for chess engines.
Supports the standard Polyglot binary format used by most chess engines.
"""

import os
import struct
import random
from typing import Optional

import chess


class PolyglotBook:
    """Polyglot opening book reader"""
    
    def __init__(self, book_path: str | None = None):
        self.book_path = book_path
        self.entries: dict[int, list[tuple[chess.Move, int, int]]] = {}  # position_hash -> [(move, weight, learn)]
        self.loaded = False
        
        if book_path and os.path.exists(book_path):
            self.load_book(book_path)
    
    def load_book(self, book_path: str):
        """Load Polyglot opening book from binary file"""
        try:
            with open(book_path, 'rb') as f:
                while True:
                    # Read 16 bytes per entry
                    data = f.read(16)
                    if len(data) < 16:
                        break
                    
                    # Unpack: key (8 bytes), move (2 bytes), weight (2 bytes), learn (4 bytes)
                    key, move_raw, weight, learn = struct.unpack('>QHHI', data)
                    
                    # Convert move from Polyglot format to chess.Move
                    move = self._polyglot_to_chess_move(move_raw)
                    if move:
                        if key not in self.entries:
                            self.entries[key] = []
                        self.entries[key].append((move, weight, learn))
            
            self.loaded = True
            print(f"Loaded Polyglot book with {len(self.entries)} positions from {os.path.basename(book_path)}")
            
        except Exception as e:
            print(f"Failed to load Polyglot book {book_path}: {e}")
            self.loaded = False
    
    def _polyglot_to_chess_move(self, move_raw: int) -> Optional[chess.Move]:
        """Convert Polyglot move format to chess.Move"""
        try:
            # Extract from/to squares and promotion piece
            from_square = move_raw & 0x3F
            to_square = (move_raw >> 6) & 0x3F
            promotion = (move_raw >> 12) & 0x7
            
            # Convert to chess.Move
            move = chess.Move(from_square, to_square)
            
            # Handle promotion
            if promotion > 0:
                promotion_pieces = [None, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
                if promotion < len(promotion_pieces):
                    move = chess.Move(from_square, to_square, promotion=promotion_pieces[promotion])
            
            return move
            
        except Exception:
            return None
    
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get a move from the opening book for the given position"""
        if not self.loaded or not self.entries:
            return None
        
        # Calculate position hash (simplified Zobrist hash)
        position_hash = self._calculate_position_hash(board)
        
        if position_hash in self.entries:
            moves = self.entries[position_hash]
            
            # Filter legal moves
            legal_moves = [(move, weight, learn) for move, weight, learn in moves if move in board.legal_moves]
            
            if legal_moves:
                # Weighted random selection based on move weights
                total_weight = sum(weight for _, weight, _ in legal_moves)
                if total_weight > 0:
                    rand = random.randint(1, total_weight)
                    current_weight = 0
                    
                    for move, weight, _ in legal_moves:
                        current_weight += weight
                        if rand <= current_weight:
                            return move
        
        return None
    
    def _calculate_position_hash(self, board: chess.Board) -> int:
        """Calculate a simple position hash for book lookup"""
        # This is a simplified hash - in practice, you'd use a proper Zobrist hash
        # For now, we'll use the FEN as a simple hash
        fen = board.fen()
        return hash(fen.split()[0])  # Use only the piece placement part
    
    def has_move(self, board: chess.Board) -> bool:
        """Check if there's a move available in the book for this position"""
        return self.get_move(board) is not None


class MultiBook:
    """Multiple opening books with weighted selection"""
    
    def __init__(self, book_paths: list[str]):
        self.books: list[PolyglotBook] = []
        self.weights: list[int] = []
        
        for book_path in book_paths:
            if os.path.exists(book_path):
                book = PolyglotBook(book_path)
                if book.loaded:
                    self.books.append(book)
                    # Weight based on file size (larger books get higher weight)
                    weight = min(os.path.getsize(book_path) // 1000, 100)  # Cap at 100
                    self.weights.append(max(weight, 1))
                    print(f"Added book: {os.path.basename(book_path)} (weight: {weight})")
    
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get a move from the best available book"""
        if not self.books:
            return None
        
        # Try books in order of weight (highest first)
        book_indices = sorted(range(len(self.books)), key=lambda i: self.weights[i], reverse=True)
        
        for book_idx in book_indices:
            move = self.books[book_idx].get_move(board)
            if move:
                return move
        
        return None
    
    def has_move(self, board: chess.Board) -> bool:
        """Check if any book has a move for this position"""
        return any(book.has_move(board) for book in self.books)
    
    def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the best move from all books (highest weighted book first)"""
        return self.get_move(board)