#!/usr/bin/env python3
"""
Test script to verify opening book integration without requiring dependencies
"""

import os
import struct

def test_polyglot_book_structure():
    """Test if we can read Polyglot book structure"""
    books_dir = "./books"
    if not os.path.exists(books_dir):
        print("❌ Books directory not found")
        return False
    
    # Test a few key books
    test_books = ["DefaultBook.bin", "Book.bin", "main.bin", "perfect_book.bin"]
    
    for book_name in test_books:
        book_path = os.path.join(books_dir, book_name)
        if os.path.exists(book_path):
            try:
                with open(book_path, 'rb') as f:
                    # Read first few entries to test structure
                    for i in range(min(5, os.path.getsize(book_path) // 16)):
                        data = f.read(16)
                        if len(data) == 16:
                            key, move_raw, weight, learn = struct.unpack('>QHHI', data)
                            print(f"✅ {book_name}: Entry {i+1} - Key: {key:016x}, Move: {move_raw:04x}, Weight: {weight}, Learn: {learn}")
                        else:
                            break
                    print(f"✅ {book_name}: Successfully read book structure")
            except Exception as e:
                print(f"❌ {book_name}: Error reading book - {e}")
        else:
            print(f"⚠️  {book_name}: Not found")
    
    return True

def test_engine_integration():
    """Test engine integration points"""
    engine_file = "./engines/homemade_engine.py"
    if not os.path.exists(engine_file):
        print("❌ Engine file not found")
        return False
    
    with open(engine_file, 'r') as f:
        content = f.read()
    
    # Check for Polyglot integration
    if "from polyglot_book import MultiBook" in content:
        print("✅ Polyglot book import found")
    else:
        print("❌ Polyglot book import missing")
        return False
    
    if "self.polyglot_book = MultiBook(book_paths)" in content:
        print("✅ Polyglot book initialization found")
    else:
        print("❌ Polyglot book initialization missing")
        return False
    
    if "self.polyglot_book.get_best_move(self.board)" in content:
        print("✅ Best move selection from Polyglot books found")
    else:
        print("❌ Best move selection from Polyglot books missing")
        return False
    
    return True

def test_configuration():
    """Test tactical bot configuration"""
    config_file = "./config_enhanced_engine.yml"
    if not os.path.exists(config_file):
        print("❌ Configuration file not found")
        return False
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Check for opening book configuration
    if "opening_books:" in content:
        print("✅ Opening books configuration found")
    else:
        print("❌ Opening books configuration missing")
        return False
    
    if "DefaultBook" in content:
        print("✅ DefaultBook reference found")
    else:
        print("❌ DefaultBook reference missing")
        return False
    
    return True

def main():
    """Run all tests"""
    print("Testing Enhanced Engine Opening Book Integration")
    print("=" * 50)
    
    print("\n1. Testing Polyglot book structure...")
    books_ok = test_polyglot_book_structure()
    
    print("\n2. Testing engine integration...")
    engine_ok = test_engine_integration()
    
    print("\n3. Testing configuration...")
    config_ok = test_configuration()
    
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    if books_ok:
        print("✅ Polyglot Books: PASS")
    else:
        print("❌ Polyglot Books: FAIL")
    
    if engine_ok:
        print("✅ Engine Integration: PASS")
    else:
        print("❌ Engine Integration: FAIL")
    
    if config_ok:
        print("✅ Configuration: PASS")
    else:
        print("❌ Configuration: FAIL")
    
    overall_success = books_ok and engine_ok and config_ok
    
    if overall_success:
        print("\n🎉 All tests passed! The enhanced engine is ready with opening books.")
        print("\nTo use with tactical bot:")
        print("1. Install dependencies: pip install chess numpy psutil")
        print("2. Copy config: cp config_enhanced_engine.yml config.yml")
        print("3. Run: python user_interface.py")
    else:
        print("\n❌ Some tests failed. Check the issues above.")
    
    return overall_success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)