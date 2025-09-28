#!/usr/bin/env python3
"""
Configuration file for the homemade chess engine
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class EngineConfig:
    """Configuration for the homemade chess engine"""

    # Search parameters
    max_depth: int = 6
    max_time_ms: int = 1000
    hash_size: int = 32

    # Evaluation parameters
    material_values: dict[int, int] | None = None
    positional_bonus: bool = True
    mobility_bonus: int = 10

    # Opening book
    use_opening_book: bool = True
    opening_depth: int = 6

    # UCI options
    uci_options: dict[str, dict[str, Any]] | None = None

    def __post_init__(self):
        if self.material_values is None:
            self.material_values = {
                1: 100,   # Pawn
                2: 320,   # Knight
                3: 330,   # Bishop
                4: 500,   # Rook
                5: 900,   # Queen
                6: 20000  # King
            }

        if self.uci_options is None:
            self.uci_options = {
                'Hash': {
                    'type': 'spin',
                    'default': self.hash_size,
                    'min': 1,
                    'max': 1024
                },
                'Depth': {
                    'type': 'spin',
                    'default': self.max_depth,
                    'min': 1,
                    'max': 20
                },
                'Time': {
                    'type': 'spin',
                    'default': self.max_time_ms,
                    'min': 100,
                    'max': 60000
                },
                'UseOpeningBook': {
                    'type': 'check',
                    'default': self.use_opening_book
                }
            }


# Default configuration
DEFAULT_CONFIG = EngineConfig()

# Stronger configuration for better play
STRONG_CONFIG = EngineConfig(
    max_depth=8,
    max_time_ms=5000,
    hash_size=128,
    mobility_bonus=15
)

# Fast configuration for quick games
FAST_CONFIG = EngineConfig(
    max_depth=4,
    max_time_ms=500,
    hash_size=16,
    mobility_bonus=5
)
