import os
import pygame
import numpy as np
from multiprocessing import Pool
from game import SnakeGame
from agent import Agent

# Configuration from environment variables.
TRAIN_RENDER = os.environ.get("TRAIN_RENDER", "0").lower() in ("1", "true", "yes")
TRAIN_N_WORKERS = int(os.environ.get("TRAIN_N_WORKERS", "4"))
TRAIN_EPISODES_PER_WORKER = int(os.environ.get("TRAIN_EPISODES_PER_WORKER", "100"))
TRAIN_BEST_SCORE = int(os.environ.get("TRAIN_BEST_SCORE", "1000"))

if TRAIN_RENDER and TRAIN_N_WORKERS != 1:
    print("WARNING: When TRAIN_RENDER is enabled, use a single worker (TRAIN_N_WORKERS=1) for reliable visuals.")

# Multiple hyperparameter sets for multi-policy training.
HYPERPARAMS = [
    {"lr": 0.1, "gamma": 0.9, "epsilon": 1.0, "epsilon_decay": 0.995, "epsilon_min": 0.01},
    {"lr": 0.05, "gamma": 0.95, "epsilon": 1.0, "epsilon_decay": 0.99, "epsilon_min": 0.01},
    {"lr": 0.2, "gamma": 0.8, "epsilon": 1.0, "epsilon_decay": 0.997, "epsilon_min": 0.01},
    {"lr": 0.1, "gamma": 0.95, "epsilon": 1.0, "epsilon_decay": 0.995, "epsilon_min": 0.01}
]


def train_worker(worker_id, episodes):
    """
    Worker function for training.

    Args:
        worker_id (int): Worker ID.
        episodes (int): Number of episodes.

    Returns:
        tuple: (best_score, q_table)
    """
    hyperparams = HYPERPARAMS[worker_id % len(HYPERPARAMS)]
    agent = Agent(lr=hyperparams["lr"],
                  gamma=hyperparams["gamma"],
                  epsilon=hyperparams["epsilon"],
                  epsilon_decay=hyperparams["epsilon_decay"],
                  epsilon_min=hyperparams["epsilon_min"])

    # Only render if TRAIN_RENDER is True and this is worker 0.
    render_val = TRAIN_RENDER and (worker_id == 0)
    game = SnakeGame(render=render_val)

    best_score = 0
    for ep in range(episodes):
        game.reset()
        state = agent.get_state(game)
        score = 0
        while True:
            action = agent.get_action(state)
            reward, done, score = game.play_step(action)
            next_state = agent.get_state(game)
            agent.train_short_memory(state, action, reward, next_state, done)
            state = next_state
            if done:
                if score > best_score:
                    best_score = score
                break
        if render_val:
            pygame.display.set_caption(f"Snake AI - Episode {ep + 1} Score: {score}")
            pygame.time.wait(100)  # Brief pause for visualization.
    return best_score, agent.q_table


def merge_q_tables(q_tables):
    """
    Merge multiple Q-tables.

    Args:
        q_tables (list): List of Q-table dicts.

    Returns:
        dict: Merged Q-table.
    """
    merged = {}
    counts = {}
    for table in q_tables:
        for state, q_vals in table.items():
            if state not in merged:
                merged[state] = np.array(q_vals, dtype=float)
                counts[state] = 1
            else:
                merged[state] += np.array(q_vals, dtype=float)
                counts[state] += 1
    for state in merged:
        merged[state] = (merged[state] / counts[state]).tolist()
    return merged


def train(n_workers, episodes_per_worker, target_score):
    """
    Train until one worker achieves the target score.

    Args:
        n_workers (int): Number of workers.
        episodes_per_worker (int): Episodes per batch.
        target_score (int): Target score threshold.
    """
    best_overall_score = 0
    best_q_table = None
    batch = 0
    while best_overall_score < target_score:
        batch += 1
        print(f"Starting batch {batch} with {n_workers} worker(s), {episodes_per_worker} episodes each.")
        args = [(worker_id, episodes_per_worker) for worker_id in range(n_workers)]
        with Pool(n_workers) as pool:
            results = pool.starmap(train_worker, args)
        q_tables = []
        for worker_id, (score, q_table) in enumerate(results):
            print(f"Worker {worker_id} achieved best score: {score}")
            q_tables.append(q_table)
            if score > best_overall_score:
                best_overall_score = score
                best_q_table = q_table
        print(f"After batch {batch}, best overall score is: {best_overall_score}")
    print("Training complete. Saving best Q-table to 'qtable_trained.npy'")
    np.save("qtable_trained.npy", best_q_table)


if __name__ == "__main__":
    pygame.init()
    train(n_workers=TRAIN_N_WORKERS,
          episodes_per_worker=TRAIN_EPISODES_PER_WORKER,
          target_score=TRAIN_BEST_SCORE)
