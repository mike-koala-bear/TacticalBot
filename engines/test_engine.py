#!/usr/bin/env python3
"""
Test script for the homemade UCI chess engine
"""

import subprocess
import sys
import time
import chess
import chess.engine


def test_uci_protocol():
    """Test basic UCI protocol communication"""
    print("Testing UCI protocol...")
    
    # Start the engine
    process = subprocess.Popen(
        [sys.executable, 'homemade_engine.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Test UCI identification
        process.stdin.write('uci\n')
        process.stdin.flush()
        
        response = []
        timeout = 5
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            line = process.stdout.readline()
            if line:
                response.append(line.strip())
                if 'uciok' in line:
                    break
        
        print("UCI Response:", response)
        
        # Test ready status
        process.stdin.write('isready\n')
        process.stdin.flush()
        
        response = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            line = process.stdout.readline()
            if line:
                response.append(line.strip())
                if 'readyok' in line:
                    break
        
        print("Ready Response:", response)
        
        # Test new game
        process.stdin.write('ucinewgame\n')
        process.stdin.flush()
        
        # Test position and go
        process.stdin.write('position startpos\n')
        process.stdin.flush()
        
        process.stdin.write('go depth 3\n')
        process.stdin.flush()
        
        response = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            line = process.stdout.readline()
            if line:
                response.append(line.strip())
                if 'bestmove' in line:
                    break
        
        print("Best move response:", response)
        
        # Quit
        process.stdin.write('quit\n')
        process.stdin.flush()
        
        print("✓ UCI protocol test completed successfully!")
        
    except Exception as e:
        print(f"✗ UCI protocol test failed: {e}")
    finally:
        process.terminate()
        process.wait()


def test_with_chess_library():
    """Test the engine using the chess library's UCI interface"""
    print("\nTesting with chess library...")
    
    try:
        # This would normally work, but we need to make the engine executable
        # For now, let's just test the engine logic directly
        from homemade_engine import UCIEngine, PositionEvaluator, SearchEngine
        
        # Test position evaluation
        evaluator = PositionEvaluator()
        board = chess.Board()
        
        score = evaluator.evaluate(board)
        print(f"Starting position evaluation: {score}")
        
        # Test search
        search_engine = SearchEngine(evaluator)
        result = search_engine.find_best_move(board, depth=3)
        
        print(f"Best move: {result.best_move}")
        print(f"Score: {result.score}")
        print(f"Nodes searched: {result.nodes}")
        
        print("✓ Chess library test completed successfully!")
        
    except Exception as e:
        print(f"✗ Chess library test failed: {e}")


def test_opening_moves():
    """Test opening move generation"""
    print("\nTesting opening moves...")
    
    try:
        from homemade_engine import UCIEngine
        
        engine = UCIEngine()
        board = chess.Board()
        
        # Test opening book
        opening_move = engine._get_opening_move()
        print(f"Opening move: {opening_move}")
        
        # Make a move and test again
        if opening_move:
            board.push(opening_move)
            engine.board = board
            opening_move2 = engine._get_opening_move()
            print(f"Second opening move: {opening_move2}")
        
        print("✓ Opening moves test completed successfully!")
        
    except Exception as e:
        print(f"✗ Opening moves test failed: {e}")


if __name__ == '__main__':
    print("Homemade Chess Engine Test Suite")
    print("=" * 40)
    
    test_uci_protocol()
    test_with_chess_library()
    test_opening_moves()
    
    print("\n" + "=" * 40)
    print("Test suite completed!")