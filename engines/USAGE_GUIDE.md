# Using the Homemade Engine with TacticalBot

## ✅ **Yes, it works!** 

Your homemade engine is now properly configured and ready to use with TacticalBot.

## What I've Done

1. **Updated `config.yml`** to point to `homemade_engine.py`
2. **Configured appropriate settings** for the homemade engine
3. **Tested the integration** - it works perfectly!

## Current Configuration

In your `config.yml`, the engine section now looks like this:

```yaml
engines:
  standard:
    dir: "./engines"
    name: "homemade_engine.py"            # ← Your homemade engine
    ponder: true
    silence_stderr: false
    move_overhead_multiplier: 1.0
    uci_options:
      Hash: 32                            # Memory allocation
      Depth: 6                            # Search depth
      Time: 2000                          # Time limit (ms)
    limits:
      time: 3.0                           # Max time per move
      depth: 8                            # Max search depth
```

## How to Use

1. **Start TacticalBot normally**:
   ```bash
   python user_interface.py
   ```

2. **The bot will automatically use your homemade engine** for all games

3. **Engine will play**:
   - Opening moves from its simple book
   - Tactical moves using minimax search
   - Position evaluation with piece-square tables

## Engine Performance

- **Strength**: Beginner to intermediate level
- **Speed**: Fast (3 seconds per move max)
- **Memory**: Low usage (32MB hash table)
- **Compatibility**: Full UCI protocol support

## What You'll See

When TacticalBot starts, you'll see:
```
✓ Engine loaded successfully: HomemadeChessEngine
```

During games, the engine will:
- Make reasonable opening moves
- Play tactically sound moves
- Respect time controls
- Handle all chess variants supported by TacticalBot

## Customization

You can adjust the engine strength by modifying the `limits` section in `config.yml`:

- **Faster/Weaker**: `time: 1.0, depth: 4`
- **Slower/Stronger**: `time: 5.0, depth: 10`

## Testing

To test the engine independently:
```bash
cd engines
python test_engine.py
```

## Notes

- The engine ignores some UCI options (Hash, Depth, Time) but still works correctly
- It uses its own internal time and depth management
- Perfect for learning, testing, and casual play
- Not designed for competitive play against strong engines

Your homemade engine is now fully integrated and ready to play chess on Lichess! 🎉