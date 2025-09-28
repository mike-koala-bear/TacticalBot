#!/usr/bin/env python3
"""
Example of how to integrate the homemade engine with TacticalBot
"""

import asyncio
import sys
import os
import chess
import chess.engine
from pathlib import Path

# Add parent directory to path to import TacticalBot modules
sys.path.append(str(Path(__file__).parent.parent))

from configs import Engine_Config, Limit_Config, Syzygy_Config
from engine import Engine


class HomemadeEngineWrapper:
    """Wrapper to make the homemade engine compatible with TacticalBot's Engine class"""
    
    def __init__(self, engine_path: str):
        self.engine_path = engine_path
        self.transport = None
        self.engine = None
    
    async def start(self):
        """Start the homemade engine"""
        stderr = subprocess.DEVNULL
        self.transport, self.engine = await chess.engine.popen_uci(self.engine_path, stderr=stderr)
        return self.engine
    
    async def stop(self):
        """Stop the homemade engine"""
        if self.engine:
            await self.engine.quit()
        if self.transport:
            self.transport.close()


async def test_homemade_engine():
    """Test the homemade engine integration"""
    print("Testing homemade engine integration...")
    
    # Path to our homemade engine
    engine_path = Path(__file__).parent / "homemade_engine.py"
    
    # Create engine configuration
    engine_config = Engine_Config(
        path=str(engine_path),
        ponder=False,
        silence_stderr=True,
        limits=Limit_Config(time=2.0, depth=4, nodes=None),
        uci_options={}
    )
    
    # Create opponent info
    opponent = chess.engine.Opponent(chess.engine.OpponentType.HUMAN, "TestPlayer", 1500)
    
    # Create syzygy config (disabled)
    syzygy_config = Syzygy_Config(False, [], 0, False)
    
    try:
        # Create engine instance
        engine = await Engine.from_config(engine_config, syzygy_config, opponent)
        
        print(f"Engine name: {engine.name}")
        
        # Test making a move
        board = chess.Board()
        move, info = await engine.make_move(board, 30.0, 30.0, 0.0)
        
        print(f"Best move: {move}")
        print(f"Move info: {info}")
        
        # Clean up
        await engine.close()
        
        print("✓ Homemade engine integration test successful!")
        
    except Exception as e:
        print(f"✗ Homemade engine integration test failed: {e}")
        import traceback
        traceback.print_exc()


async def compare_engines():
    """Compare homemade engine with a reference engine"""
    print("\nComparing engines...")
    
    # Test positions
    test_positions = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Starting position
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",  # Tactical position
    ]
    
    engine_path = Path(__file__).parent / "homemade_engine.py"
    
    for i, fen in enumerate(test_positions):
        print(f"\nTest position {i+1}:")
        print(f"FEN: {fen}")
        
        board = chess.Board(fen)
        
        # Test with homemade engine
        try:
            import subprocess
            import time
            
            process = subprocess.Popen(
                [sys.executable, str(engine_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send UCI commands
            commands = [
                "uci",
                "isready", 
                f"position fen {fen}",
                "go depth 3"
            ]
            
            for cmd in commands:
                process.stdin.write(cmd + "\n")
                process.stdin.flush()
                time.sleep(0.1)
            
            # Read response
            response = []
            start_time = time.time()
            while time.time() - start_time < 5:
                line = process.stdout.readline()
                if line:
                    response.append(line.strip())
                    if "bestmove" in line:
                        break
            
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.terminate()
            
            print(f"Homemade engine response: {response[-1] if response else 'No response'}")
            
        except Exception as e:
            print(f"Error testing homemade engine: {e}")


if __name__ == "__main__":
    print("Homemade Engine Integration Example")
    print("=" * 40)
    
    # Run the tests
    asyncio.run(test_homemade_engine())
    asyncio.run(compare_engines())
    
    print("\n" + "=" * 40)
    print("Integration example completed!")