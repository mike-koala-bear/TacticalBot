#!/usr/bin/env python3
"""
Multi-threading support for parallel chess search.
Implements Lazy SMP (Symmetric Multi-Processing) algorithm.
"""

import threading
import time
import queue
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future
import chess
from enum import Enum


class SearchState(Enum):
    """Search thread states"""
    IDLE = "idle"
    SEARCHING = "searching"
    STOPPED = "stopped"


@dataclass
class SearchTask:
    """Task for search thread"""
    board: chess.Board
    depth: int
    alpha: int
    beta: int
    maximizing: bool
    move: Optional[chess.Move] = None
    task_id: int = 0


@dataclass
class SearchResult:
    """Result from search thread"""
    score: int
    best_move: Optional[chess.Move]
    depth: int
    nodes: int
    task_id: int
    thread_id: int


class SearchThread:
    """Individual search thread"""
    
    def __init__(self, thread_id: int, evaluator, shared_tt: Dict, 
                 shared_killer_moves: Dict, shared_history: Dict):
        self.thread_id = thread_id
        self.evaluator = evaluator
        self.shared_tt = shared_tt
        self.shared_killer_moves = shared_killer_moves
        self.shared_history = shared_history
        
        self.state = SearchState.IDLE
        self.current_task: Optional[SearchTask] = None
        self.nodes_searched = 0
        self.stop_requested = False
        
        # Thread-local storage
        self.local_tt = {}
        self.local_killer_moves = {}
        self.local_history = {}
        
        # Thread communication
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.thread = threading.Thread(target=self._search_loop, daemon=True)
        self.thread.start()
    
    def _search_loop(self):
        """Main search loop for this thread"""
        while not self.stop_requested:
            try:
                # Get task with timeout
                task = self.task_queue.get(timeout=0.1)
                self.current_task = task
                self.state = SearchState.SEARCHING
                self.nodes_searched = 0
                
                # Perform search
                result = self._search(task)
                
                # Send result
                self.result_queue.put(result)
                self.state = SearchState.IDLE
                self.current_task = None
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Search thread {self.thread_id} error: {e}")
                self.state = SearchState.IDLE
                self.current_task = None
    
    def _search(self, task: SearchTask) -> SearchResult:
        """Perform search for given task"""
        if task.depth <= 0:
            score = self.evaluator.evaluate(task.board)
            return SearchResult(score, None, 0, 1, task.task_id, self.thread_id)
        
        # Check for stop
        if self.stop_requested:
            return SearchResult(0, None, task.depth, self.nodes_searched, task.task_id, self.thread_id)
        
        # Check transposition table
        board_hash = hash(task.board.fen())
        if board_hash in self.shared_tt:
            tt_entry = self.shared_tt[board_hash]
            if tt_entry['depth'] >= task.depth:
                return SearchResult(tt_entry['score'], tt_entry['move'], 
                                 task.depth, 1, task.task_id, self.thread_id)
        
        legal_moves = list(task.board.legal_moves)
        if not legal_moves:
            score = self.evaluator.evaluate(task.board)
            return SearchResult(score, None, task.depth, 1, task.task_id, self.thread_id)
        
        # Move ordering
        ordered_moves = self._order_moves(task.board, legal_moves, task.depth)
        
        best_score = -30000 if task.maximizing else 30000
        best_move = ordered_moves[0] if ordered_moves else None
        alpha, beta = task.alpha, task.beta
        
        for move in ordered_moves:
            if self.stop_requested:
                break
            
            # Make move
            task.board.push(move)
            self.nodes_searched += 1
            
            # Recursive search
            if task.maximizing:
                score = self._search_minimax(task.board, task.depth - 1, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
            else:
                score = self._search_minimax(task.board, task.depth - 1, alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)
            
            # Undo move
            task.board.pop()
            
            # Alpha-beta pruning
            if beta <= alpha:
                break
        
        # Store in transposition table
        self.shared_tt[board_hash] = {
            'score': best_score,
            'move': best_move,
            'depth': task.depth
        }
        
        return SearchResult(best_score, best_move, task.depth, self.nodes_searched, 
                          task.task_id, self.thread_id)
    
    def _search_minimax(self, board: chess.Board, depth: int, alpha: int, beta: int, 
                       maximizing: bool) -> int:
        """Minimax search with alpha-beta pruning"""
        if depth <= 0 or self.stop_requested:
            return self.evaluator.evaluate(board)
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return self.evaluator.evaluate(board)
        
        if maximizing:
            max_eval = -30000
            for move in legal_moves:
                board.push(move)
                eval_score = self._search_minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 30000
            for move in legal_moves:
                board.push(move)
                eval_score = self._search_minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def _order_moves(self, board: chess.Board, moves: List[chess.Move], depth: int) -> List[chess.Move]:
        """Order moves for better alpha-beta pruning"""
        move_scores = []
        
        for move in moves:
            score = 0
            
            # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                moving_piece = board.piece_at(move.from_square)
                
                if captured_piece and moving_piece:
                    piece_values = {
                        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                        chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100
                    }
                    score += piece_values[captured_piece.piece_type] * 1000
                    score -= piece_values[moving_piece.piece_type]
            
            # Killer moves
            if depth in self.shared_killer_moves:
                if move in self.shared_killer_moves[depth]:
                    score += 100
            
            # History heuristic
            move_key = (move.from_square, move.to_square)
            if move_key in self.shared_history:
                score += self.shared_history[move_key]
            
            # Promotion bonus
            if move.promotion:
                score += 50
            
            move_scores.append((move, score))
        
        # Sort by score (descending)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]
    
    def stop(self):
        """Stop the search thread"""
        self.stop_requested = True
        self.state = SearchState.STOPPED
    
    def join(self):
        """Wait for thread to finish"""
        self.thread.join()


class ParallelSearchEngine:
    """Parallel search engine using multiple threads"""
    
    def __init__(self, evaluator, num_threads: int = None):
        self.evaluator = evaluator
        self.num_threads = num_threads or min(4, threading.active_count())
        
        # Shared data structures
        self.shared_tt = {}
        self.shared_killer_moves = {}
        self.shared_history = {}
        
        # Search threads
        self.search_threads: List[SearchThread] = []
        for i in range(self.num_threads):
            thread = SearchThread(i, evaluator, self.shared_tt, 
                                self.shared_killer_moves, self.shared_history)
            self.search_threads.append(thread)
        
        # Search state
        self.searching = False
        self.stop_search = False
        self.best_move = None
        self.best_score = 0
        self.search_depth = 0
        self.total_nodes = 0
    
    def search(self, board: chess.Board, depth: int, time_limit: Optional[float] = None) -> Tuple[chess.Move, int, int]:
        """Perform parallel search"""
        self.searching = True
        self.stop_search = False
        self.best_move = None
        self.best_score = 0
        self.search_depth = depth
        self.total_nodes = 0
        
        # Clear shared data
        self.shared_tt.clear()
        self.shared_killer_moves.clear()
        self.shared_history.clear()
        
        # Start search threads
        start_time = time.time()
        task_id = 0
        
        # Lazy SMP: Each thread searches different depths
        for thread_id, thread in enumerate(self.search_threads):
            if thread.state == SearchState.IDLE:
                # Different depths for each thread
                thread_depth = max(1, depth - thread_id)
                task = SearchTask(board, thread_depth, -30000, 30000, 
                                board.turn == chess.WHITE, task_id=task_id)
                thread.task_queue.put(task)
                task_id += 1
        
        # Collect results
        best_result = None
        results_received = 0
        
        while self.searching and not self.stop_search:
            # Check time limit
            if time_limit and (time.time() - start_time) > time_limit:
                self.stop_search = True
                break
            
            # Check for results
            for thread in self.search_threads:
                try:
                    result = thread.result_queue.get_nowait()
                    results_received += 1
                    
                    if best_result is None or abs(result.score) > abs(best_result.score):
                        best_result = result
                        self.best_move = result.best_move
                        self.best_score = result.score
                    
                    self.total_nodes += result.nodes
                    
                except queue.Empty:
                    continue
            
            # Check if all threads are done
            if all(thread.state == SearchState.IDLE for thread in self.search_threads):
                break
            
            time.sleep(0.001)  # Small delay to prevent busy waiting
        
        # Stop all threads
        for thread in self.search_threads:
            thread.stop()
        
        self.searching = False
        
        if best_result:
            return best_result.best_move, best_result.score, self.total_nodes
        else:
            # Fallback to first legal move
            legal_moves = list(board.legal_moves)
            return legal_moves[0] if legal_moves else None, 0, 0
    
    def stop(self):
        """Stop the search"""
        self.stop_search = True
        for thread in self.search_threads:
            thread.stop()
    
    def cleanup(self):
        """Clean up resources"""
        for thread in self.search_threads:
            thread.join()


class IterativeDeepeningParallel:
    """Iterative deepening with parallel search"""
    
    def __init__(self, evaluator, num_threads: int = None):
        self.parallel_engine = ParallelSearchEngine(evaluator, num_threads)
        self.evaluator = evaluator
    
    def search(self, board: chess.Board, max_depth: int, time_limit: Optional[float] = None) -> Tuple[chess.Move, int, int, int]:
        """Iterative deepening search with parallel threads"""
        start_time = time.time()
        best_move = None
        best_score = 0
        total_nodes = 0
        depth_reached = 0
        
        # Iterative deepening
        for depth in range(1, max_depth + 1):
            # Check time limit
            if time_limit and (time.time() - start_time) > time_limit * 0.8:  # Leave 20% buffer
                break
            
            # Search at current depth
            move, score, nodes = self.parallel_engine.search(board, depth, time_limit)
            
            if move:
                best_move = move
                best_score = score
                total_nodes += nodes
                depth_reached = depth
                
                # Print search info
                elapsed = time.time() - start_time
                print(f"info depth {depth} score cp {score} nodes {total_nodes} time {int(elapsed * 1000)} pv {move.uci()}")
            
            # Stop if we found a mate
            if abs(score) > 20000:
                break
        
        return best_move, best_score, total_nodes, depth_reached
    
    def cleanup(self):
        """Clean up resources"""
        self.parallel_engine.cleanup()


# Example usage
if __name__ == "__main__":
    from nnue import HybridEvaluator
    
    # Test parallel search
    evaluator = HybridEvaluator()
    parallel_search = IterativeDeepeningParallel(evaluator, num_threads=4)
    
    board = chess.Board()
    move, score, nodes, depth = parallel_search.search(board, max_depth=6, time_limit=5.0)
    
    print(f"Best move: {move}")
    print(f"Score: {score}")
    print(f"Nodes: {nodes}")
    print(f"Depth: {depth}")
    
    parallel_search.cleanup()