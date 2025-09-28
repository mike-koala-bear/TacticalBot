# Homemade Chess Engine

A simple but functional UCI-compatible chess engine written in Python.

## Features

- **UCI Protocol**: Full UCI (Universal Chess Interface) implementation
- **Position Evaluation**: Material and positional piece-square tables
- **Search Algorithm**: Minimax with alpha-beta pruning
- **Opening Book**: Simple opening move database
- **Iterative Deepening**: Progressive depth search
- **Transposition Table**: Basic move caching for efficiency

## Installation

The engine requires the `chess` library:

```bash
pip install chess
```

## Usage

### Command Line

Run the engine directly:

```bash
python homemade_engine.py
```

The engine will start in UCI mode and wait for commands.

### UCI Commands

The engine supports all standard UCI commands:

- `uci` - Engine identification
- `isready` - Check if engine is ready
- `ucinewgame` - Start a new game
- `position [fen <fenstring> | startpos] moves <move1> ... <movei>` - Set position
- `go [wtime <x>] [btime <x>] [winc <x>] [binc <x>] [movetime <x>] [depth <x>]` - Start search
- `quit` - Quit engine

### Example UCI Session

```
uci
id name HomemadeChessEngine
id author AI Assistant
uciok

isready
readyok

ucinewgame

position startpos

go depth 4
bestmove e2e4

quit
```

### Integration with Chess GUIs

The engine can be used with any UCI-compatible chess GUI:

1. **Arena Chess GUI**: Add as UCI engine
2. **ChessBase**: Import as UCI engine
3. **Cute Chess**: Add as UCI engine
4. **PyChess**: Add as UCI engine

### Configuration Options

The engine supports these UCI options:

- `Hash` (1-1024): Transposition table size (default: 32)
- `Depth` (1-20): Maximum search depth (default: 6)
- `Time` (100-60000): Time limit in milliseconds (default: 1000)

## Testing

Run the test suite:

```bash
python test_engine.py
```

This will test:
- UCI protocol communication
- Position evaluation
- Search algorithm
- Opening book

## Engine Strength

This is a basic engine suitable for:
- Learning chess programming concepts
- Testing chess GUIs
- Educational purposes
- Light recreational play

The engine is not designed for competitive play against strong engines.

## Technical Details

### Evaluation Function

The engine evaluates positions using:

1. **Material Values**:
   - Pawn: 100
   - Knight: 320
   - Bishop: 330
   - Rook: 500
   - Queen: 900
   - King: 20000

2. **Positional Factors**:
   - Piece-square tables for each piece type
   - Mobility bonus (number of legal moves)
   - Center control

### Search Algorithm

- **Minimax** with alpha-beta pruning
- **Iterative deepening** for time management
- **Transposition table** for move caching
- **Quiescence search** (basic implementation)

### Opening Book

Simple hardcoded opening moves:
- e2e4, d2d4, g1f3, c2c4, b1c3, f2f4, g2g3, b2b3

## License

This engine is provided as educational software. Feel free to modify and improve it!