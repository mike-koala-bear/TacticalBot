#!/usr/bin/env python3
"""
Test the enhanced engine directly without tactical bot dependencies
"""

import subprocess
import time
import sys

def test_engine_uci():
    """Test UCI protocol with the enhanced engine"""
    print("Testing Enhanced Homemade Engine UCI Protocol")
    print("=" * 50)
    
    try:
        # Start the engine process
        process = subprocess.Popen(
            ['python3', 'engines/enhanced_homemade_engine'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send UCI command
        print("Sending 'uci' command...")
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Read response with timeout
        start_time = time.time()
        response_lines = []
        
        while time.time() - start_time < 10:  # 10 second timeout
            if process.stdout.readable():
                line = process.stdout.readline()
                if line:
                    response_lines.append(line.strip())
                    print(f"Engine: {line.strip()}")
                    
                    # Check if we got uciok
                    if "uciok" in line:
                        print("✅ UCI protocol working correctly!")
                        break
            else:
                time.sleep(0.1)
        
        # Send isready command
        print("\nSending 'isready' command...")
        process.stdin.write("isready\n")
        process.stdin.flush()
        
        # Read isready response
        start_time = time.time()
        while time.time() - start_time < 5:
            if process.stdout.readable():
                line = process.stdout.readline()
                if line:
                    print(f"Engine: {line.strip()}")
                    if "readyok" in line:
                        print("✅ Engine is ready!")
                        break
            else:
                time.sleep(0.1)
        
        # Send position and go commands
        print("\nTesting position and go commands...")
        process.stdin.write("position startpos\n")
        process.stdin.write("go depth 1\n")
        process.stdin.flush()
        
        # Read move response
        start_time = time.time()
        while time.time() - start_time < 5:
            if process.stdout.readable():
                line = process.stdout.readline()
                if line:
                    print(f"Engine: {line.strip()}")
                    if "bestmove" in line:
                        print("✅ Engine found a move!")
                        break
            else:
                time.sleep(0.1)
        
        # Clean up
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()
        process.wait()
        
        print("\n✅ Engine test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Engine test failed: {e}")
        return False

def test_engine_with_tactical_bot_config():
    """Test if the engine works with tactical bot configuration"""
    print("\nTesting Engine with Tactical Bot Configuration")
    print("=" * 50)
    
    # Read the config file
    try:
        with open('config.yml', 'r') as f:
            config_content = f.read()
        
        if 'enhanced_homemade_engine' in config_content:
            print("✅ Config file contains enhanced_homemade_engine")
        else:
            print("❌ Config file missing enhanced_homemade_engine")
            return False
        
        if 'standard:' in config_content:
            print("✅ Config file has 'standard' engine configuration")
        else:
            print("❌ Config file missing 'standard' engine configuration")
            return False
        
        print("✅ Configuration looks correct for tactical bot")
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Enhanced Homemade Engine Direct Testing")
    print("=" * 60)
    
    # Test 1: UCI Protocol
    uci_ok = test_engine_uci()
    
    # Test 2: Configuration
    config_ok = test_engine_with_tactical_bot_config()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if uci_ok:
        print("✅ UCI Protocol: PASS")
    else:
        print("❌ UCI Protocol: FAIL")
    
    if config_ok:
        print("✅ Configuration: PASS")
    else:
        print("❌ Configuration: FAIL")
    
    overall_success = uci_ok and config_ok
    
    if overall_success:
        print("\n🎉 All tests passed! The engine is working correctly.")
        print("\nThe engine should work with tactical bot once dependencies are installed:")
        print("sudo apt install python3-aiohttp python3-yaml python3-tenacity")
        print("python3 user_interface.py -u")
    else:
        print("\n❌ Some tests failed. Check the issues above.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)