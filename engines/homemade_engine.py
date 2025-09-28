#!/usr/bin/env python3
"""
Enhanced Homemade UCI Chess Engine
A modern chess engine combining traditional techniques with neural networks.
Features: Bitboards, NNUE evaluation, Multi-threading, Advanced search algorithms.
"""

import os
import random
import threading
import time
from dataclasses import dataclass

import chess
import chess.engine

# Import our enhanced modules
from bitboard import BitboardMoveGenerator
from nnue import HybridEvaluator
from opening_book import EnhancedOpeningBook
from parallel_search import IterativeDeepeningParallel


@dataclass
class SearchResult:
    """Result of a search operation"""
    best_move: chess.Move | None
    score: int
    depth: int
    nodes: int
    pv: list[chess.Move]  # Principal variation


class EnhancedPositionEvaluator:
    """Enhanced position evaluator using hybrid approach"""

    def __init__(self, use_nnue: bool = True):
        self.use_nnue = use_nnue
        if use_nnue:
            self.hybrid_evaluator = HybridEvaluator()
        else:
            self.hybrid_evaluator = None
            self._init_traditional_evaluator()

    def _init_traditional_evaluator(self):
        """Initialize traditional evaluation components"""
        # Piece values
        self.PIECE_VALUES = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        # Enhanced piece-square tables
        self.PAWN_TABLE = [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ]

        self.KNIGHT_TABLE = [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ]

        self.BISHOP_TABLE = [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ]

        self.ROOK_TABLE = [
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            0,  0,  0,  5,  5,  0,  0,  0
        ]

        self.QUEEN_TABLE = [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -5,  0,  5,  5,  5,  5,  0, -5,
            0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20
        ]

        self.KING_TABLE = [
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            20, 20,  0,  0,  0,  0, 20, 20,
            20, 30, 10,  0,  0, 10, 30, 20
        ]

        self.tables = {
            chess.PAWN: self.PAWN_TABLE,
            chess.KNIGHT: self.KNIGHT_TABLE,
            chess.BISHOP: self.BISHOP_TABLE,
            chess.ROOK: self.ROOK_TABLE,
            chess.QUEEN: self.QUEEN_TABLE,
            chess.KING: self.KING_TABLE
        }

    def evaluate(self, board: chess.Board) -> int:
        """Evaluate the current position using hybrid approach"""
        if self.use_nnue and self.hybrid_evaluator:
            return self.hybrid_evaluator.evaluate(board)
        return self._traditional_evaluate(board)

    def _traditional_evaluate(self, board: chess.Board) -> int:
        """Traditional position evaluation"""
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


class EnhancedSearchEngine:
    """Enhanced search engine with bitboards and parallel search"""

    def __init__(self, evaluator: EnhancedPositionEvaluator, use_parallel: bool = True, num_threads: int | None = None):
        self.evaluator = evaluator
        self.use_parallel = use_parallel
        self.num_threads = num_threads or min(4, os.cpu_count() or 1)

        # Initialize bitboard components
        self.bitboard_generator = BitboardMoveGenerator()

        # Initialize parallel search if enabled
        if use_parallel:
            self.parallel_search = IterativeDeepeningParallel(evaluator, self.num_threads)
        else:
            self.parallel_search = None

        # Search state
        self.nodes_searched = 0
        self.stop_search = False
        self.best_move = None
        self.transposition_table = {}
        self.killer_moves = {}
        self.history_heuristic = {}

    def search(self, board: chess.Board, depth: int, alpha: int = -30000, beta: int = 30000,
               maximizing_player: bool = True) -> int:
        """Enhanced minimax search with advanced pruning"""
        self.nodes_searched += 1

        if depth == 0 or self.stop_search:
            return self.evaluator.evaluate(board)

        # Check transposition table
        board_hash = hash(board.fen())
        if board_hash in self.transposition_table:
            tt_entry = self.transposition_table[board_hash]
            if tt_entry['depth'] >= depth:
                return tt_entry['score']

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return self.evaluator.evaluate(board)

        # Move ordering
        ordered_moves = self._order_moves(board, legal_moves, depth)

        if maximizing_player:
            max_eval = -30000
            for move in ordered_moves:
                board.push(move)
                eval_score = self.search(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    # Store killer move
                    if depth not in self.killer_moves:
                        self.killer_moves[depth] = []
                    if move not in self.killer_moves[depth]:
                        self.killer_moves[depth].insert(0, move)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop()
                    break  # Beta cutoff
            self.transposition_table[board_hash] = {'score': max_eval, 'depth': depth}
            return max_eval
        min_eval = 30000
        for move in ordered_moves:
            board.push(move)
            eval_score = self.search(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                # Store killer move
                if depth not in self.killer_moves:
                    self.killer_moves[depth] = []
                if move not in self.killer_moves[depth]:
                    self.killer_moves[depth].insert(0, move)
                    if len(self.killer_moves[depth]) > 2:
                        self.killer_moves[depth].pop()
                break  # Alpha cutoff
        self.transposition_table[board_hash] = {'score': min_eval, 'depth': depth}
        return min_eval

    def _order_moves(self, board: chess.Board, moves: list[chess.Move], depth: int) -> list[chess.Move]:
        """Order moves for better alpha-beta pruning"""
        move_scores = []

        for move in moves:
            score = 0

            # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                moving_piece = board.piece_at(move.from_square)

                if captured_piece and moving_piece:
                    piece_values = {
                        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                        chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100
                    }
                    score += piece_values[captured_piece.piece_type] * 1000
                    score -= piece_values[moving_piece.piece_type]

            # Killer moves
            if depth in self.killer_moves:
                if move in self.killer_moves[depth]:
                    score += 100

            # History heuristic
            move_key = (move.from_square, move.to_square)
            if move_key in self.history_heuristic:
                score += self.history_heuristic[move_key]

            # Promotion bonus
            if move.promotion:
                score += 50

            move_scores.append((move, score))

        # Sort by score (descending)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def find_best_move(self, board: chess.Board, depth: int, time_limit: float | None = None) -> SearchResult:
        """Find the best move using enhanced search"""
        if self.use_parallel and self.parallel_search is not None:
            return self._parallel_search(board, depth, time_limit)
        return self._sequential_search(board, depth, time_limit)

    def _parallel_search(self, board: chess.Board, depth: int, time_limit: float | None = None) -> SearchResult:
        """Use parallel search for better performance"""
        if self.parallel_search is None:
            return self._sequential_search(board, depth, time_limit)

        try:
            best_move, best_score, total_nodes, depth_reached = self.parallel_search.search(
                board, depth, time_limit
            )
            return SearchResult(best_move, best_score, depth_reached, total_nodes, [best_move] if best_move else [])
        except Exception as e:
            print(f"Parallel search error: {e}, falling back to sequential")
            return self._sequential_search(board, depth, time_limit)

    def _sequential_search(self, board: chess.Board, depth: int, time_limit: float | None = None) -> SearchResult:
        """Sequential search with iterative deepening"""
        self.nodes_searched = 0
        self.stop_search = False
        self.best_move = None
        self.transposition_table.clear()
        self.killer_moves.clear()
        self.history_heuristic.clear()

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return SearchResult(None, 0, 0, 0, [])

        # If only one move, return it
        if len(legal_moves) == 1:
            return SearchResult(legal_moves[0], 0, 1, 1, legal_moves)

        best_score = -30000 if board.turn == chess.WHITE else 30000
        best_move = legal_moves[0]
        pv = []

        start_time = time.time()

        # Iterative deepening
        for current_depth in range(1, depth + 1):
            if self.stop_search:
                break

            # Check time limit
            if time_limit and (time.time() - start_time) > time_limit:
                break

            move_scores = []

            for move in legal_moves:
                if self.stop_search:
                    break

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

                # Update history heuristic
                move_key = (best_move.from_square, best_move.to_square)
                self.history_heuristic[move_key] = self.history_heuristic.get(move_key, 0) + 1

        return SearchResult(best_move, best_score, depth, self.nodes_searched, pv)

    def stop(self):
        """Stop the search"""
        self.stop_search = True
        if self.parallel_search:
            self.parallel_search.parallel_engine.stop()

    def cleanup(self):
        """Clean up resources"""
        if self.parallel_search:
            self.parallel_search.cleanup()


class EnhancedUCIEngine:
    """Enhanced UCI engine with modern features"""

    def __init__(self):
        self.board = chess.Board()
        self.evaluator = EnhancedPositionEvaluator(use_nnue=True)
        self.search_engine = EnhancedSearchEngine(self.evaluator, use_parallel=True)
        self.search_thread = None
        self.running = True

        # Initialize opening book
        book_paths = []
        # Look for book files in the books directory
        books_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'books')
        if os.path.exists(books_dir):
            book_paths.extend(os.path.join(books_dir, file)
                            for file in os.listdir(books_dir)
                            if file.endswith(('.bin', '.txt')))

        self.opening_book = EnhancedOpeningBook(book_paths)

        # UCI options
        self.options = {
            'Hash': {'type': 'spin', 'default': 128, 'min': 1, 'max': 2048},
            'Depth': {'type': 'spin', 'default': 8, 'min': 1, 'max': 25},
            'Time': {'type': 'spin', 'default': 3000, 'min': 100, 'max': 60000},
            'Threads': {'type': 'spin', 'default': 4, 'min': 1, 'max': 16},
            'UseNNUE': {'type': 'check', 'default': True},
            'UseParallel': {'type': 'check', 'default': True}
        }

        # Current settings
        self.hash_size = 128
        self.max_depth = 8
        self.time_limit = 3000  # milliseconds
        self.num_threads = 4
        self.use_nnue = True
        self.use_parallel = True

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
        print('id name EnhancedHomemadeChessEngine')
        print('id author AI Assistant')
        print('id version 2.0')
        print('option name Hash type spin default 128 min 1 max 2048')
        print('option name Depth type spin default 8 min 1 max 25')
        print('option name Time type spin default 3000 min 100 max 60000')
        print('option name Threads type spin default 4 min 1 max 16')
        print('option name UseNNUE type check default true')
        print('option name UseParallel type check default true')
        print('uciok')

    def send_ready(self):
        """Send ready status"""
        print('readyok')

    def new_game(self):
        """Start a new game"""
        self.board = chess.Board()
        self.search_engine.transposition_table.clear()
        self.search_engine.killer_moves.clear()
        self.search_engine.history_heuristic.clear()

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

    def _search_thread(self, depth_limit: int, time_limit: float | None):
        """Search thread function"""
        start_time = time.time()

        # Simple opening book
        opening_move = self._get_opening_move()
        if opening_move:
            print(f'bestmove {opening_move.uci()}')
            return

        # Perform enhanced search
        result = self.search_engine.find_best_move(self.board, depth_limit, time_limit)

        # Print search info
        elapsed = time.time() - start_time
        pv_str = " ".join([move.uci() for move in result.pv])
        print(f'info depth {result.depth} score cp {result.score} nodes {result.nodes} '
              f'time {int(elapsed * 1000)} pv {pv_str}')

        if result.best_move:
            print(f'bestmove {result.best_move.uci()}')
        else:
            # No legal moves - game over
            print('bestmove 0000')

    def _get_opening_move(self) -> chess.Move | None:
        """Enhanced opening book"""
        # Use opening book for first 10 moves
        if len(self.board.move_stack) > 10:
            return None

        # Try to get move from opening book
        move = self.opening_book.get_move(self.board)
        if move and self.board.is_legal(move):
            return move

        # Fallback to simple opening moves
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
            elif option_name == 'Threads':
                self.num_threads = int(option_value)
                # Recreate search engine with new thread count
                self.search_engine = EnhancedSearchEngine(self.evaluator, self.use_parallel, self.num_threads)
            elif option_name == 'UseNNUE':
                self.use_nnue = option_value.lower() == 'true'
                self.evaluator = EnhancedPositionEvaluator(use_nnue=self.use_nnue)
                self.search_engine = EnhancedSearchEngine(self.evaluator, self.use_parallel, self.num_threads)
            elif option_name == 'UseParallel':
                self.use_parallel = option_value.lower() == 'true'
                self.search_engine = EnhancedSearchEngine(self.evaluator, self.use_parallel, self.num_threads)

    def quit(self):
        """Quit the engine"""
        self.running = False
        if self.search_thread and self.search_thread.is_alive():
            self.search_engine.stop()
            self.search_thread.join(timeout=1.0)
        self.search_engine.cleanup()


def main():
    """Main entry point"""
    engine = EnhancedUCIEngine()
    engine.run()


if __name__ == '__main__':
    main()
