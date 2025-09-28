#!/usr/bin/env python3
"""
NNUE (Efficiently Updatable Neural Networks) implementation for chess position evaluation.
This is a simplified version that can be extended with more sophisticated features.
"""

import struct
from dataclasses import dataclass

import chess
import numpy as np


@dataclass
class NNUEWeights:
    """NNUE network weights and biases"""
    input_weights: np.ndarray  # Shape: (input_features, hidden_size)
    hidden_weights: np.ndarray  # Shape: (hidden_size, 1)
    input_bias: np.ndarray     # Shape: (hidden_size,)
    hidden_bias: float         # Scalar


class NNUEFeatureExtractor:
    """Extract features for NNUE evaluation"""

    def __init__(self):
        # Piece-square features for each piece type and color
        self.feature_size = 64 * 12  # 64 squares * 12 piece types (6 pieces * 2 colors)
        self.piece_to_index = {
            (chess.WHITE, chess.PAWN): 0,
            (chess.WHITE, chess.KNIGHT): 1,
            (chess.WHITE, chess.BISHOP): 2,
            (chess.WHITE, chess.ROOK): 3,
            (chess.WHITE, chess.QUEEN): 4,
            (chess.WHITE, chess.KING): 5,
            (chess.BLACK, chess.PAWN): 6,
            (chess.BLACK, chess.KNIGHT): 7,
            (chess.BLACK, chess.BISHOP): 8,
            (chess.BLACK, chess.ROOK): 9,
            (chess.BLACK, chess.QUEEN): 10,
            (chess.BLACK, chess.KING): 11,
        }

    def extract_features(self, board: chess.Board) -> list[int]:
        """Extract active features from board position"""
        features = []

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                feature_index = self.piece_to_index[(piece.color, piece.piece_type)] * 64 + square
                features.append(feature_index)

        return features

    def extract_features_bitboard(self, board) -> list[int]:
        """Extract features using bitboard representation"""
        features = []

        for square in chess.SQUARES:
            piece_info = board.get_piece_at(square)
            if piece_info:
                piece_color, piece_type = piece_info
                feature_index = self.piece_to_index[(piece_color, piece_type)] * 64 + square
                features.append(feature_index)

        return features


class SimpleNNUE:
    """Simplified NNUE implementation"""

    def __init__(self, input_size: int = 768, hidden_size: int = 256):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.feature_extractor = NNUEFeatureExtractor()

        # Initialize weights randomly
        self.weights = NNUEWeights(
            input_weights=np.random.randn(input_size, hidden_size) * 0.1,
            hidden_weights=np.random.randn(hidden_size, 1) * 0.1,
            input_bias=np.zeros(hidden_size),
            hidden_bias=0.0
        )

        # Accumulator for efficient updates
        self.accumulator = np.zeros(hidden_size)
        self.active_features = set()

    def evaluate(self, board: chess.Board) -> int:
        """Evaluate position using NNUE"""
        features = self.feature_extractor.extract_features(board)

        # Compute hidden layer activations
        hidden = np.zeros(self.hidden_size)
        for feature in features:
            hidden += self.weights.input_weights[feature]
        hidden += self.weights.input_bias
        hidden = np.maximum(0, hidden)  # ReLU activation

        # Compute output
        output = np.dot(hidden, self.weights.hidden_weights) + self.weights.hidden_bias

        # Convert to centipawns and apply perspective
        score = int(output[0] * 100)
        if board.turn == chess.BLACK:
            score = -score

        return score

    def evaluate_bitboard(self, board) -> int:
        """Evaluate position using bitboard representation"""
        features = self.feature_extractor.extract_features_bitboard(board)

        # Compute hidden layer activations
        hidden = np.zeros(self.hidden_size)
        for feature in features:
            hidden += self.weights.input_weights[feature]
        hidden += self.weights.input_bias
        hidden = np.maximum(0, hidden)  # ReLU activation

        # Compute output
        output = np.dot(hidden, self.weights.hidden_weights) + self.weights.hidden_bias

        # Convert to centipawns and apply perspective
        score = int(output[0] * 100)
        if board.turn == chess.BLACK:
            score = -score

        return score

    def update_accumulator(self, added_features: list[int], removed_features: list[int]):
        """Efficiently update accumulator for incremental evaluation"""
        # Remove old features
        for feature in removed_features:
            if feature in self.active_features:
                self.accumulator -= self.weights.input_weights[feature]
                self.active_features.remove(feature)

        # Add new features
        for feature in added_features:
            if feature not in self.active_features:
                self.accumulator += self.weights.input_weights[feature]
                self.active_features.add(feature)

    def evaluate_from_accumulator(self) -> int:
        """Evaluate using current accumulator state"""
        hidden = self.accumulator + self.weights.input_bias
        hidden = np.maximum(0, hidden)  # ReLU activation

        output = np.dot(hidden, self.weights.hidden_weights) + self.weights.hidden_bias
        return int(output[0] * 100)

    def save_weights(self, filename: str):
        """Save NNUE weights to file"""
        with open(filename, 'wb') as f:
            # Write header
            f.write(struct.pack('IIII', self.input_size, self.hidden_size, 1, 0))

            # Write weights
            self.weights.input_weights.astype(np.float32).tofile(f)
            self.weights.hidden_weights.astype(np.float32).tofile(f)
            self.weights.input_bias.astype(np.float32).tofile(f)
            f.write(struct.pack('f', self.weights.hidden_bias))

    def load_weights(self, filename: str):
        """Load NNUE weights from file"""
        with open(filename, 'rb') as f:
            # Read header
            header = struct.unpack('IIII', f.read(16))
            input_size, hidden_size, output_size, _ = header

            # Read weights
            input_weights = np.fromfile(f, dtype=np.float32, count=input_size * hidden_size)
            self.weights.input_weights = input_weights.reshape(input_size, hidden_size)

            hidden_weights = np.fromfile(f, dtype=np.float32, count=hidden_size * output_size)
            self.weights.hidden_weights = hidden_weights.reshape(hidden_size, output_size)

            input_bias = np.fromfile(f, dtype=np.float32, count=hidden_size)
            self.weights.input_bias = input_bias

            hidden_bias = struct.unpack('f', f.read(4))[0]
            self.weights.hidden_bias = hidden_bias


class HybridEvaluator:
    """Combines traditional evaluation with NNUE"""

    def __init__(self):
        self.nnue = SimpleNNUE()
        self.traditional_weight = 0.3
        self.nnue_weight = 0.7

    def evaluate(self, board: chess.Board) -> int:
        """Hybrid evaluation combining traditional and NNUE"""
        # Traditional evaluation
        traditional_score = self._traditional_evaluate(board)

        # NNUE evaluation
        nnue_score = self.nnue.evaluate(board)

        # Combine scores
        return int(
            self.traditional_weight * traditional_score +
            self.nnue_weight * nnue_score
        )

    def _traditional_evaluate(self, board: chess.Board) -> int:
        """Traditional position evaluation"""
        if board.is_checkmate():
            return -30000 if board.turn == chess.WHITE else 30000

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0

        # Material values
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        # Evaluate material and position
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue

            piece_value = piece_values[piece.piece_type]

            # Simple positional bonus
            positional_bonus = self._get_positional_bonus(square, piece)
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

    def _get_positional_bonus(self, square: int, piece: chess.Piece) -> int:
        """Get positional bonus for piece on square"""
        rank, file = divmod(square, 8)

        # Center control bonus
        center_bonus = 0
        if 2 <= rank <= 5 and 2 <= file <= 5:
            center_bonus = 20

        # Piece-specific bonuses
        if piece.piece_type == chess.PAWN:
            # Pawn advancement
            advancement = rank if piece.color == chess.WHITE else 7 - rank
            return center_bonus + advancement * 5

        if piece.piece_type == chess.KNIGHT:
            # Knight centralization
            return center_bonus + 10

        if piece.piece_type == chess.BISHOP:
            # Bishop mobility
            return center_bonus + 5

        if piece.piece_type == chess.ROOK:
            # Rook on open files
            return center_bonus

        if piece.piece_type == chess.QUEEN:
            # Queen centralization
            return center_bonus + 5

        if piece.piece_type == chess.KING:
            # King safety (prefer back rank)
            if piece.color == chess.WHITE:
                return -rank * 10
            return -(7 - rank) * 10

        return center_bonus


def train_nnue_on_games(nnue: SimpleNNUE, games: list[list[chess.Board]],
                       learning_rate: float = 0.01, epochs: int = 10):
    """Train NNUE on a collection of games"""
    for epoch in range(epochs):
        total_loss = 0
        game_count = 0

        for game in games:
            for _i, board in enumerate(game):
                # Get features
                features = nnue.feature_extractor.extract_features(board)

                # Simple target: material count
                target = nnue.evaluate(board) / 100.0

                # Forward pass
                hidden = np.zeros(nnue.hidden_size)
                for feature in features:
                    hidden += nnue.weights.input_weights[feature]
                hidden += nnue.weights.input_bias
                hidden = np.maximum(0, hidden)

                output = np.dot(hidden, nnue.weights.hidden_weights) + nnue.weights.hidden_bias

                # Compute loss
                loss = (output[0] - target) ** 2
                total_loss += loss

                # Backward pass (simplified)
                error = output[0] - target

                # Update weights
                for feature in features:
                    nnue.weights.input_weights[feature] -= learning_rate * error * hidden

                nnue.weights.input_bias -= learning_rate * error
                nnue.weights.hidden_weights -= learning_rate * error * hidden.reshape(-1, 1)
                nnue.weights.hidden_bias -= learning_rate * error

            game_count += 1

        avg_loss = total_loss / game_count if game_count > 0 else 0
        print(f"Epoch {epoch + 1}/{epochs}, Average Loss: {avg_loss:.4f}")


# Example usage and testing
if __name__ == "__main__":
    # Test NNUE evaluation
    board = chess.Board()
    nnue = SimpleNNUE()
    hybrid = HybridEvaluator()

    print("Initial position evaluation:")
    print(f"NNUE: {nnue.evaluate(board)}")
    print(f"Hybrid: {hybrid.evaluate(board)}")

    # Test with some moves
    board.push(chess.Move.from_uci("e2e4"))
    print("\nAfter e4:")
    print(f"NNUE: {nnue.evaluate(board)}")
    print(f"Hybrid: {hybrid.evaluate(board)}")
