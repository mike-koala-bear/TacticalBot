#!/usr/bin/env python3
"""
Homemade UCI Chess Engine
A simple but functional chess engine that implements the UCI protocol.
"""

import sys
import time
import threading
from typing import List, Optional, Tuple, Dict, Any
import chess
import chess.engine
from dataclasses import dataclass
import random


@dataclass
class SearchResult:
    """Result of a search operation"""
    best_move: Optional[chess.Move]
    score: int
    depth: int
    nodes: int
    pv: List[chess.Move]  # Principal variation


class PositionEvaluator:
    """Handles position evaluation"""
    
    # Piece values
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    # Positional piece-square tables
    PAWN_TABLE = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    KNIGHT_TABLE = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    BISHOP_TABLE = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    ROOK_TABLE = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]
    
    QUEEN_TABLE = [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]
    
    KING_TABLE = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
    
    def __init__(self):
        self.tables = {
            chess.PAWN: self.PAWN_TABLE,
            chess.KNIGHT: self.KNIGHT_TABLE,
            chess.BISHOP: self.BISHOP_TABLE,
            chess.ROOK: self.ROOK_TABLE,
            chess.QUEEN: self.QUEEN_TABLE,
            chess.KING: self.KING_TABLE
        }
    
    def evaluate(self, board: chess.Board) -> int:
        """Evaluate the current position"""
        if board.is_checkmate():
            return -30000 if board.turn == chess.WHITE else 30000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        score = 0
        
        # Material and positional evaluation
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue
            
            piece_value = self.PIECE_VALUES[piece.piece_type]
            
            # Get positional bonus
            if piece.color == chess.WHITE:
                positional_bonus = self.tables[piece.piece_type][square]
            else:
                # Flip table for black pieces
                positional_bonus = self.tables[piece.piece_type][chess.square_mirror(square)]
            
            total_value = piece_value + positional_bonus
            
            if piece.color == chess.WHITE:
                score += total_value
            else:
                score -= total_value
        
        # Mobility bonus
        white_moves = len(list(board.legal_moves))
        board.turn = chess.BLACK
        black_moves = len(list(board.legal_moves))
        board.turn = chess.WHITE
        
        score += (white_moves - black_moves) * 10
        
        return score


class SearchEngine:
    """Handles the search algorithm"""
    
    def __init__(self, evaluator: PositionEvaluator):
        self.evaluator = evaluator
        self.nodes_searched = 0
        self.stop_search = False
        self.best_move = None
        self.transposition_table = {}
    
    def search(self, board: chess.Board, depth: int, alpha: int = -30000, beta: int = 30000, 
               maximizing_player: bool = True) -> int:
        """Minimax search with alpha-beta pruning"""
        self.nodes_searched += 1
        
        if depth == 0 or self.stop_search:
            return self.evaluator.evaluate(board)
        
        # Check transposition table
        board_hash = hash(board.fen())
        if board_hash in self.transposition_table:
            return self.transposition_table[board_hash]
        
        legal_moves = list(board.legal_moves)
        
        if not legal_moves:
            return self.evaluator.evaluate(board)
        
        if maximizing_player:
            max_eval = -30000
            for move in legal_moves:
                board.push(move)
                eval_score = self.search(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            self.transposition_table[board_hash] = max_eval
            return max_eval
        else:
            min_eval = 30000
            for move in legal_moves:
                board.push(move)
                eval_score = self.search(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            self.transposition_table[board_hash] = min_eval
            return min_eval
    
    def find_best_move(self, board: chess.Board, depth: int, time_limit: Optional[float] = None) -> SearchResult:
        """Find the best move using iterative deepening"""
        self.nodes_searched = 0
        self.stop_search = False
        self.best_move = None
        self.transposition_table.clear()
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return SearchResult(None, 0, 0, 0, [])
        
        # If only one move, return it
        if len(legal_moves) == 1:
            return SearchResult(legal_moves[0], 0, 1, 1, legal_moves)
        
        best_score = -30000 if board.turn == chess.WHITE else 30000
        best_move = legal_moves[0]
        pv = []
        
        # Iterative deepening
        for current_depth in range(1, depth + 1):
            if self.stop_search:
                break
            
            move_scores = []
            
            for move in legal_moves:
                board.push(move)
                score = self.search(board, current_depth - 1, -30000, 30000, board.turn == chess.BLACK)
                board.pop()
                move_scores.append((move, score))
            
            # Sort moves by score
            if board.turn == chess.WHITE:
                move_scores.sort(key=lambda x: x[1], reverse=True)
            else:
                move_scores.sort(key=lambda x: x[1])
            
            if move_scores:
                best_move, best_score = move_scores[0]
                pv = [best_move]
        
        return SearchResult(best_move, best_score, depth, self.nodes_searched, pv)


class UCIEngine:
    """Main UCI engine class"""
    
    def __init__(self):
        self.board = chess.Board()
        self.evaluator = PositionEvaluator()
        self.search_engine = SearchEngine(self.evaluator)
        self.search_thread = None
        self.running = True
        
        # UCI options
        self.options = {
            'Hash': {'type': 'spin', 'default': 32, 'min': 1, 'max': 1024},
            'Depth': {'type': 'spin', 'default': 6, 'min': 1, 'max': 20},
            'Time': {'type': 'spin', 'default': 1000, 'min': 100, 'max': 60000}
        }
        
        # Current settings
        self.hash_size = 32
        self.max_depth = 6
        self.time_limit = 1000  # milliseconds
    
    def run(self):
        """Main UCI loop"""
        while self.running:
            try:
                line = input().strip()
                if not line:
                    continue
                
                self.handle_command(line)
            except EOFError:
                break
            except KeyboardInterrupt:
                break
    
    def handle_command(self, command: str):
        """Handle UCI commands"""
        parts = command.split()
        
        if command == 'uci':
            self.send_uci()
        elif command == 'isready':
            self.send_ready()
        elif command == 'ucinewgame':
            self.new_game()
        elif command.startswith('position'):
            self.set_position(command)
        elif command.startswith('go'):
            self.go(command)
        elif command == 'quit':
            self.quit()
        elif command.startswith('setoption'):
            self.set_option(command)
        else:
            # Unknown command - ignore
            pass
    
    def send_uci(self):
        """Send UCI identification"""
        print('id name HomemadeChessEngine')
        print('id author AI Assistant')
        print('uciok')
    
    def send_ready(self):
        """Send ready status"""
        print('readyok')
    
    def new_game(self):
        """Start a new game"""
        self.board = chess.Board()
        self.search_engine.transposition_table.clear()
    
    def set_position(self, command: str):
        """Set the position"""
        parts = command.split()
        
        if parts[1] == 'startpos':
            self.board = chess.Board()
            if len(parts) > 2 and parts[2] == 'moves':
                moves = parts[3:]
                for move_str in moves:
                    move = chess.Move.from_uci(move_str)
                    self.board.push(move)
        elif parts[1] == 'fen':
            fen_parts = parts[2:8]
            fen = ' '.join(fen_parts)
            self.board = chess.Board(fen)
            if len(parts) > 8 and parts[8] == 'moves':
                moves = parts[9:]
                for move_str in moves:
                    move = chess.Move.from_uci(move_str)
                    self.board.push(move)
    
    def go(self, command: str):
        """Start searching for the best move"""
        parts = command.split()
        
        # Parse time limits
        time_limit = None
        depth_limit = self.max_depth
        
        for i, part in enumerate(parts):
            if part == 'wtime' and i + 1 < len(parts):
                if self.board.turn == chess.WHITE:
                    time_limit = int(parts[i + 1]) / 1000.0  # Convert to seconds
            elif part == 'btime' and i + 1 < len(parts):
                if self.board.turn == chess.BLACK:
                    time_limit = int(parts[i + 1]) / 1000.0  # Convert to seconds
            elif part == 'depth' and i + 1 < len(parts):
                depth_limit = int(parts[i + 1])
            elif part == 'movetime' and i + 1 < len(parts):
                time_limit = int(parts[i + 1]) / 1000.0  # Convert to seconds
        
        # Start search in a separate thread
        self.search_thread = threading.Thread(
            target=self._search_thread,
            args=(depth_limit, time_limit)
        )
        self.search_thread.daemon = True
        self.search_thread.start()
    
    def _search_thread(self, depth_limit: int, time_limit: Optional[float]):
        """Search thread function"""
        start_time = time.time()
        
        # Simple opening book
        opening_move = self._get_opening_move()
        if opening_move:
            print(f'bestmove {opening_move.uci()}')
            return
        
        # Perform search
        result = self.search_engine.find_best_move(self.board, depth_limit, time_limit)
        
        if result.best_move:
            print(f'bestmove {result.best_move.uci()}')
        else:
            # No legal moves - game over
            print('bestmove 0000')
    
    def _get_opening_move(self) -> Optional[chess.Move]:
        """Simple opening book"""
        if len(self.board.move_stack) > 6:  # Only use opening book for first few moves
            return None
        
        # Simple opening moves
        opening_moves = [
            'e2e4', 'd2d4', 'g1f3', 'c2c4', 'b1c3', 'f2f4', 'g2g3', 'b2b3'
        ]
        
        legal_moves = [move.uci() for move in self.board.legal_moves]
        available_openings = [move for move in opening_moves if move in legal_moves]
        
        if available_openings:
            return chess.Move.from_uci(random.choice(available_openings))
        
        return None
    
    def set_option(self, command: str):
        """Set UCI option"""
        parts = command.split()
        if len(parts) >= 4 and parts[1] == 'name' and parts[3] == 'value':
            option_name = parts[2]
            option_value = parts[4]
            
            if option_name == 'Hash':
                self.hash_size = int(option_value)
            elif option_name == 'Depth':
                self.max_depth = int(option_value)
            elif option_name == 'Time':
                self.time_limit = int(option_value)
    
    def quit(self):
        """Quit the engine"""
        self.running = False
        if self.search_thread and self.search_thread.is_alive():
            self.search_engine.stop_search = True
            self.search_thread.join(timeout=1.0)


def main():
    """Main entry point"""
    engine = UCIEngine()
    engine.run()


if __name__ == '__main__':
    main()