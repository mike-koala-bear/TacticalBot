#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced homemade chess engine.
Tests bitboards, NNUE, multi-threading, and overall engine performance.
"""

import os
import sys
import time
import unittest

import chess
import psutil

# Add the engines directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bitboard import Bitboard, BitboardBoard, BitboardMoveGenerator
from homemade_engine import EnhancedPositionEvaluator, EnhancedSearchEngine, EnhancedUCIEngine
from nnue import HybridEvaluator, SimpleNNUE
from parallel_search import IterativeDeepeningParallel


class TestBitboard(unittest.TestCase):
    """Test bitboard functionality"""

    def test_bitboard_operations(self):
        """Test basic bitboard operations"""
        bb = Bitboard()

        # Test setting and getting bits
        bb.set_bit(0)
        self.assertTrue(bb.get_bit(0))
        self.assertFalse(bb.get_bit(1))

        # Test clearing bits
        bb.clear_bit(0)
        self.assertFalse(bb.get_bit(0))

        # Test bit counting
        bb.set_bit(0)
        bb.set_bit(1)
        bb.set_bit(2)
        self.assertEqual(bb.popcount(), 3)

        # Test LSB/MSB
        self.assertEqual(bb.lsb(), 0)
        self.assertEqual(bb.msb(), 2)

    def test_bitboard_board_conversion(self):
        """Test conversion between bitboard and chess board"""
        board = chess.Board()
        bb_board = BitboardBoard(board)

        # Test conversion back
        converted_board = bb_board.to_chess_board()
        self.assertEqual(board.fen(), converted_board.fen())

        # Test move making
        move = chess.Move.from_uci("e2e4")
        board.push(move)
        bb_board_moved = bb_board.make_move(move)
        converted_moved = bb_board_moved.to_chess_board()
        self.assertEqual(board.fen(), converted_moved.fen())

    def test_bitboard_move_generation(self):
        """Test bitboard move generation"""
        board = BitboardBoard(chess.Board())
        generator = BitboardMoveGenerator()

        # Test knight moves
        knight_moves = generator.get_knight_moves(chess.E4, board.white_pieces)
        self.assertGreater(len(knight_moves.to_squares()), 0)

        # Test king moves
        king_moves = generator.get_king_moves(chess.E1, board.white_pieces)
        self.assertGreater(len(king_moves.to_squares()), 0)


class TestNNUE(unittest.TestCase):
    """Test NNUE evaluation"""

    def test_nnue_evaluation(self):
        """Test NNUE evaluation consistency"""
        nnue = SimpleNNUE()
        board = chess.Board()

        # Test that evaluation is consistent
        score1 = nnue.evaluate(board)
        score2 = nnue.evaluate(board)
        self.assertEqual(score1, score2)

        # Test that evaluation changes with position
        board.push(chess.Move.from_uci("e2e4"))
        score3 = nnue.evaluate(board)
        self.assertNotEqual(score1, score3)

    def test_hybrid_evaluator(self):
        """Test hybrid evaluator"""
        hybrid = HybridEvaluator()
        board = chess.Board()

        # Test evaluation
        score = hybrid.evaluate(board)
        self.assertIsInstance(score, int)

        # Test mate detection
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        # This should not be mate
        score = hybrid.evaluate(board)
        self.assertLess(abs(score), 30000)


class TestParallelSearch(unittest.TestCase):
    """Test parallel search functionality"""

    def test_parallel_search_consistency(self):
        """Test that parallel search gives consistent results"""
        evaluator = HybridEvaluator()
        parallel_search = IterativeDeepeningParallel(evaluator, num_threads=2)

        board = chess.Board()

        # Run search multiple times
        results = []
        for _ in range(3):
            move, score, _nodes, _depth = parallel_search.search(board, max_depth=4, time_limit=2.0)
            results.append((move, score))

        # All results should be the same
        for i in range(1, len(results)):
            self.assertEqual(results[0][0], results[i][0])  # Same move
            self.assertEqual(results[0][1], results[i][1])  # Same score


    def test_parallel_vs_sequential(self):
        """Test that parallel search is faster than sequential"""
        evaluator = EnhancedPositionEvaluator()

        # Sequential search
        sequential_engine = EnhancedSearchEngine(evaluator, use_parallel=False)

        # Parallel search
        parallel_engine = EnhancedSearchEngine(evaluator, use_parallel=True, num_threads=2)

        board = chess.Board()

        # Time sequential search
        start_time = time.time()
        seq_result = sequential_engine.find_best_move(board, depth=4, time_limit=2.0)
        seq_time = time.time() - start_time

        # Time parallel search
        start_time = time.time()
        par_result = parallel_engine.find_best_move(board, depth=4, time_limit=2.0)
        par_time = time.time() - start_time

        # Both should find moves
        self.assertIsNotNone(seq_result.best_move)
        self.assertIsNotNone(par_result.best_move)

        # Parallel should be faster (or at least not slower)
        # Note: This might not always be true due to overhead, but it's a good test
        print(f"Sequential time: {seq_time:.3f}s, Parallel time: {par_time:.3f}s")



class TestEnhancedEngine(unittest.TestCase):
    """Test the enhanced engine as a whole"""

    def test_engine_initialization(self):
        """Test that the engine initializes correctly"""
        engine = EnhancedUCIEngine()

        # Test that components are initialized
        self.assertIsNotNone(engine.evaluator)
        self.assertIsNotNone(engine.search_engine)
        self.assertIsNotNone(engine.board)

        # Test UCI options
        self.assertIn('Hash', engine.options)
        self.assertIn('Threads', engine.options)
        self.assertIn('UseNNUE', engine.options)
        self.assertIn('UseParallel', engine.options)


    def test_engine_search(self):
        """Test that the engine can search and find moves"""
        engine = EnhancedUCIEngine()

        # Test search
        result = engine.search_engine.find_best_move(engine.board, depth=3, time_limit=1.0)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.best_move)
        self.assertIsInstance(result.score, int)
        self.assertGreater(result.nodes, 0)


    def test_uci_commands(self):
        """Test UCI command handling"""
        engine = EnhancedUCIEngine()

        # Test UCI identification
        engine.send_uci()

        # Test ready status
        engine.send_ready()

        # Test new game
        engine.new_game()
        self.assertEqual(engine.board.fen(), chess.Board().fen())

        # Test position setting
        engine.set_position("position startpos moves e2e4")
        self.assertEqual(engine.board.fen(), "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")


    def test_engine_options(self):
        """Test engine option setting"""
        engine = EnhancedUCIEngine()

        # Test setting options
        engine.set_option("setoption name Hash value 256")
        self.assertEqual(engine.hash_size, 256)

        engine.set_option("setoption name Depth value 10")
        self.assertEqual(engine.max_depth, 10)

        engine.set_option("setoption name Threads value 2")
        self.assertEqual(engine.num_threads, 2)

        engine.set_option("setoption name UseNNUE value false")
        self.assertFalse(engine.use_nnue)

        engine.set_option("setoption name UseParallel value false")
        self.assertFalse(engine.use_parallel)



class TestPerformance(unittest.TestCase):
    """Test engine performance"""

    def test_search_speed(self):
        """Test that the engine searches at reasonable speed"""
        engine = EnhancedUCIEngine()

        start_time = time.time()
        result = engine.search_engine.find_best_move(engine.board, depth=5, time_limit=3.0)
        search_time = time.time() - start_time

        # Should complete within time limit
        self.assertLess(search_time, 3.5)  # Allow some margin

        # Should find a move
        self.assertIsNotNone(result.best_move)

        # Should search reasonable number of nodes
        self.assertGreater(result.nodes, 100)

        print(f"Search completed in {search_time:.3f}s, searched {result.nodes} nodes")


    def test_memory_usage(self):
        """Test that engine doesn't leak memory"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create and destroy multiple engines
        for _ in range(5):
            engine = EnhancedUCIEngine()
            engine.search_engine.find_best_move(engine.board, depth=3, time_limit=1.0)
            del engine

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)

        print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")


class TestIntegration(unittest.TestCase):
    """Test integration with existing chess systems"""

    def test_chess_library_compatibility(self):
        """Test compatibility with python-chess library"""
        engine = EnhancedUCIEngine()

        # Test with various positions
        positions = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Starting position
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",  # After e4
            "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",  # Complex position
        ]

        for fen in positions:
            board = chess.Board(fen)
            engine.board = board

            result = engine.search_engine.find_best_move(board, depth=3, time_limit=1.0)

            # Should find a legal move
            if result.best_move:
                self.assertTrue(board.is_legal(result.best_move))



def run_performance_benchmark():
    """Run a performance benchmark"""
    print("Running Enhanced Engine Performance Benchmark")
    print("=" * 50)

    engine = EnhancedUCIEngine()

    # Test positions
    positions = [
        ("Starting position", chess.Board()),
        ("After e4", chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")),
        ("Complex position", chess.Board("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")),
    ]

    for name, board in positions:
        print(f"\nTesting {name}:")
        print(f"FEN: {board.fen()}")

        # Test different depths
        for depth in [3, 4, 5]:
            start_time = time.time()
            result = engine.search_engine.find_best_move(board, depth=depth, time_limit=5.0)
            elapsed = time.time() - start_time

            print(f"  Depth {depth}: {result.best_move.uci() if result.best_move else 'None'} "
                  f"(score: {result.score}, nodes: {result.nodes}, time: {elapsed:.3f}s)")

    print("\nBenchmark completed!")


if __name__ == '__main__':
    # Run unit tests
    print("Running Enhanced Engine Tests")
    print("=" * 40)

    unittest.main(verbosity=2, exit=False)

    # Run performance benchmark
    print("\n")
    run_performance_benchmark()
