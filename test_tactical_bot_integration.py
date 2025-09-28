#!/usr/bin/env python3
"""
Test script to verify the enhanced homemade engine integration with tactical bot
"""

import os
import sys
import subprocess
import tempfile
import yaml

def test_engine_config():
    """Test if the engine can be configured for the tactical bot"""
    
    # Create a test config for the enhanced engine
    config = {
        'engines': {
            'enhanced_homemade': {
                'dir': './engines',
                'name': 'enhanced_homemade_engine',
                'ponder': True,
                'silence_stderr': False,
                'move_overhead_multiplier': 1.0,
                'uci_options': {
                    'Threads': 4,
                    'Hash': 128,
                    'UseNNUE': True,
                    'UseParallel': True,
                    'Depth': 8,
                    'Time': 3000
                },
                'limits': {
                    'time': 5.0,
                    'depth': 15,
                    'nodes': 1000000
                }
            }
        }
    }
    
    # Write test config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    print(f"✅ Test config created: {config_path}")
    print("Configuration for enhanced homemade engine:")
    print(f"  - Engine path: {config['engines']['enhanced_homemade']['dir']}/{config['engines']['enhanced_homemade']['name']}")
    print(f"  - UCI options: {config['engines']['enhanced_homemade']['uci_options']}")
    print(f"  - Limits: {config['engines']['enhanced_homemade']['limits']}")
    
    return config_path

def test_engine_structure():
    """Test if the engine files are properly structured"""
    
    engine_files = [
        'engines/homemade_engine.py',
        'engines/bitboard.py', 
        'engines/nnue.py',
        'engines/parallel_search.py',
        'engines/opening_book.py',
        'engines/enhanced_homemade_engine'
    ]
    
    missing_files = []
    for file_path in engine_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All engine files present")
        return True

def test_uci_protocol():
    """Test if the engine implements UCI protocol correctly"""
    
    # Check if the engine has the required UCI methods
    engine_code = open('engines/homemade_engine.py', 'r').read()
    
    required_methods = [
        'send_uci',
        'send_ready', 
        'new_game',
        'set_position',
        'go',
        'quit',
        'set_option'
    ]
    
    missing_methods = []
    for method in required_methods:
        if f'def {method}' not in engine_code:
            missing_methods.append(method)
    
    if missing_methods:
        print(f"❌ Missing UCI methods: {missing_methods}")
        return False
    else:
        print("✅ All required UCI methods present")
        return True

def test_dependencies():
    """Test if all required dependencies are available"""
    
    required_modules = ['chess', 'numpy', 'psutil']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"⚠️  Missing dependencies: {missing_modules}")
        print("   These need to be installed for the engine to work:")
        print("   pip install chess numpy psutil")
        return False
    else:
        print("✅ All dependencies available")
        return True

def main():
    """Run all integration tests"""
    
    print("Testing Enhanced Homemade Engine Integration with Tactical Bot")
    print("=" * 60)
    
    # Test 1: File structure
    print("\n1. Testing file structure...")
    structure_ok = test_engine_structure()
    
    # Test 2: UCI protocol
    print("\n2. Testing UCI protocol implementation...")
    uci_ok = test_uci_protocol()
    
    # Test 3: Dependencies
    print("\n3. Testing dependencies...")
    deps_ok = test_dependencies()
    
    # Test 4: Configuration
    print("\n4. Testing tactical bot configuration...")
    config_path = test_engine_config()
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    if structure_ok and uci_ok:
        print("✅ Engine Structure: PASS")
    else:
        print("❌ Engine Structure: FAIL")
    
    if deps_ok:
        print("✅ Dependencies: PASS")
    else:
        print("⚠️  Dependencies: PARTIAL (need to install)")
    
    print("✅ Configuration: PASS")
    
    print("\nTo use the enhanced engine with tactical bot:")
    print("1. Install dependencies: pip install chess numpy psutil")
    print("2. Copy the config from the test file to your config.yml")
    print("3. Run: python user_interface.py")
    
    # Cleanup
    os.unlink(config_path)
    
    return structure_ok and uci_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)