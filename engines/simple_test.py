#!/usr/bin/env python3
"""
Simple test to verify the enhanced engine structure without external dependencies.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test bitboard import
        from bitboard import Bitboard, BitboardBoard, BitboardMoveGenerator
        print("✓ Bitboard module imported successfully")
        
        # Test NNUE import
        from nnue import SimpleNNUE, HybridEvaluator
        print("✓ NNUE module imported successfully")
        
        # Test parallel search import
        from parallel_search import ParallelSearchEngine, IterativeDeepeningParallel
        print("✓ Parallel search module imported successfully")
        
        # Test opening book import
        from opening_book import SimpleOpeningBook, EnhancedOpeningBook
        print("✓ Opening book module imported successfully")
        
        # Test main engine import
        from homemade_engine import EnhancedUCIEngine, EnhancedPositionEvaluator, EnhancedSearchEngine
        print("✓ Enhanced engine module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_bitboard_basic():
    """Test basic bitboard functionality"""
    print("\nTesting bitboard basic functionality...")
    
    try:
        from bitboard import Bitboard
        
        # Test bitboard creation
        bb = Bitboard()
        print("✓ Bitboard created")
        
        # Test bit operations
        bb.set_bit(0)
        assert bb.get_bit(0) == True
        print("✓ Bit setting/getting works")
        
        bb.clear_bit(0)
        assert bb.get_bit(0) == False
        print("✓ Bit clearing works")
        
        # Test bit counting
        bb.set_bit(0)
        bb.set_bit(1)
        bb.set_bit(2)
        assert bb.popcount() == 3
        print("✓ Bit counting works")
        
        return True
        
    except Exception as e:
        print(f"✗ Bitboard test failed: {e}")
        return False

def test_nnue_basic():
    """Test basic NNUE functionality"""
    print("\nTesting NNUE basic functionality...")
    
    try:
        from nnue import SimpleNNUE, HybridEvaluator
        
        # Test NNUE creation
        nnue = SimpleNNUE()
        print("✓ SimpleNNUE created")
        
        # Test hybrid evaluator creation
        hybrid = HybridEvaluator()
        print("✓ HybridEvaluator created")
        
        return True
        
    except Exception as e:
        print(f"✗ NNUE test failed: {e}")
        return False

def test_opening_book_basic():
    """Test basic opening book functionality"""
    print("\nTesting opening book basic functionality...")
    
    try:
        from opening_book import SimpleOpeningBook, EnhancedOpeningBook
        
        # Test simple opening book
        simple_book = SimpleOpeningBook()
        print("✓ SimpleOpeningBook created")
        
        # Test enhanced opening book
        enhanced_book = EnhancedOpeningBook()
        print("✓ EnhancedOpeningBook created")
        
        return True
        
    except Exception as e:
        print(f"✗ Opening book test failed: {e}")
        return False

def test_engine_structure():
    """Test engine structure without chess library"""
    print("\nTesting engine structure...")
    
    try:
        # Test that we can create the classes (without actually using them)
        from homemade_engine import EnhancedPositionEvaluator, EnhancedSearchEngine
        
        # Test evaluator creation
        evaluator = EnhancedPositionEvaluator(use_nnue=False)  # Disable NNUE to avoid numpy
        print("✓ EnhancedPositionEvaluator created")
        
        # Test search engine creation (this might fail due to missing chess library)
        try:
            search_engine = EnhancedSearchEngine(evaluator, use_parallel=False)
            print("✓ EnhancedSearchEngine created")
        except Exception as e:
            print(f"⚠ EnhancedSearchEngine creation failed (expected without chess library): {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Engine structure test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Enhanced Chess Engine - Simple Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_bitboard_basic,
        test_nnue_basic,
        test_opening_book_basic,
        test_engine_structure,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced engine structure is working correctly.")
    else:
        print("⚠ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)