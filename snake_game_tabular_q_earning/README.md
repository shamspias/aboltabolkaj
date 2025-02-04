# Snake AI Reinforcement Learning Project

## Overview

This project implements a classic Snake game where an AI agent learns to play using reinforcement learning. The agent is trained with **tabular Q-learning**, a model-free algorithm, and the game environment is built using Python and Pygame. During training, the agent learns to maximize its score by updating a Q‑table based on the rewards it receives while interacting with the environment.

## Process & Methodology

### Process

1. **Environment Setup:**  
   The Snake game is implemented using Pygame. The game environment provides a discrete state space and a set of three possible actions:
   - **Straight**
   - **Turn Right**
   - **Turn Left**

2. **State Representation:**  
   The game state is represented as an 11-dimensional binary tuple, which includes:
   - Immediate danger (collision) in the three directions (straight, right, left).
   - Current movement direction (left, right, up, down).
   - Relative position of the food (left, right, up, down).

3. **Action Selection:**  
   The agent selects actions using an **epsilon‑greedy policy**:
   - With probability ε, a random action is chosen (exploration).
   - Otherwise, the action with the highest Q‑value is selected (exploitation).

4. **Reward Structure:**  
   The reward function is designed to encourage the following:
   - **+10** for eating food.
   - **–10** for collisions (with walls or itself).
   - A small **+1** reward if the snake moves closer to the food and **–1** if it moves farther away.  
   This reward shaping helps the agent learn even if the positive events (like eating food) occur infrequently.

5. **Learning Process:**  
   The Q‑learning update rule is applied on every step of an episode. Multiple episodes are run (optionally in parallel via multiprocessing) to train the agent, and the best Q‑table is saved once the target score is achieved.

### Methodology

- **Reinforcement Learning (RL):**  
  RL is a learning paradigm where an agent learns to make decisions by interacting with an environment to maximize cumulative reward.

- **Tabular Q-Learning:**  
  This project uses tabular Q‑learning to update the Q‑table. The algorithm is “model-free,” meaning the agent does not need a model of the environment. Instead, it updates its Q‑values directly based on experience.

### Mathematical Formulation

The core of Q‑learning is the update rule:

![Q-learning equation](https://quicklatex.com/cache3/91/ql_9c89a9cbcd0b770737871df43f0d7b91_l3.png)



Where:
- \( s \) = current state
- \( a \) = action taken
- \( r \) = reward received after taking action \( a \)
- \( s' \) = next state after action \( a \)
- \( \alpha \) = learning rate (how quickly the algorithm updates)
- \( \gamma \) = discount factor (how much future rewards are taken into account)
- \( \max_{a'} Q(s', a') \) = estimated maximum future reward for the next state

### Algorithms Used and Alternatives

- **Current Algorithm:**  
  - **Tabular Q-Learning:**  
    Uses a table (dictionary) to store Q‑values for each state-action pair. It is simple and works well for environments with small, discrete state spaces.
  
- **Potential Alternatives:**  
  - **Deep Q-Network (DQN):**  
    When the state space becomes large or continuous, a neural network can approximate the Q‑function. This approach replaces the Q‑table with a network that is trained using techniques from deep learning.
  - **Other Algorithms:**  
    Other reinforcement learning methods such as SARSA, Actor-Critic models, or Policy Gradient methods can also be applied depending on the complexity of the environment.

## How It Works

1. **Initialization:**  
   - The Snake game environment and the Q‑learning agent are initialized.
   - The agent’s state is derived from the current game configuration (e.g., snake’s head position, food position, direction, and nearby obstacles).

2. **Episode Execution:**  
   - In each episode, the agent takes actions according to its epsilon‑greedy policy.
   - The Q‑learning update rule is applied after every step to refine the Q‑table.
   - The agent receives immediate feedback (reward) which is used to adjust its future actions.

3. **Training Loop:**  
   - Training is conducted over many episodes, potentially using multiple worker processes (via Python’s multiprocessing) for faster simulation.
   - The simulation can run in **fast mode** (headless or with skipped frame delays) during training to maximize speed.
   - Once a worker achieves the target score, the best Q‑table is saved.

4. **Evaluation:**  
   - When running the game (with `main.py`), the agent loads the trained Q‑table.
   - The agent uses a greedy policy (minimal exploration) to demonstrate the learned behavior.

## Setup and Execution

### Requirements

- **Python 3.12+**
- **Pygame**
- **NumPy**

Install the required packages using:

```bash
pip install pygame numpy
```

### File Structure

```
snake_game/
├── agent.py
├── constants.py
├── game.py
├── main.py
└── train.py
```

### Training the Agent

The training script (`train.py`) supports various configurations via environment variables:

- `TRAIN_RENDER`:  
  Set to `1` or `true` to display the game window during training; otherwise, training runs headless.
  
- `TRAIN_N_WORKERS`:  
  Number of parallel worker processes (default: 4).

- `TRAIN_EPISODES_PER_WORKER`:  
  Number of episodes each worker runs per batch.

- `TRAIN_BEST_SCORE`:  
  Target score at which training stops.

- `FAST_SIM`:  
  Set to `1` to run fast simulation (skip frame delays) even if rendering is enabled.

**Example (Headless Fast Training):**

```bash
export TRAIN_RENDER=0
export TRAIN_N_WORKERS=4
export TRAIN_EPISODES_PER_WORKER=100
export TRAIN_BEST_SCORE=1000
python train.py
```

**Example (Training with Visuals and Fast Simulation):**

```bash
export TRAIN_RENDER=1
export FAST_SIM=1
export TRAIN_N_WORKERS=1
export TRAIN_EPISODES_PER_WORKER=100
export TRAIN_BEST_SCORE=1000
python train.py
```

### Running the Game (Evaluation)

After training, run the game with the trained agent using:

```bash
python main.py
```

In evaluation mode, the agent uses a greedy policy (minimal exploration) to demonstrate the learned behavior.

## Conclusion

This project demonstrates the application of reinforcement learning to a classic game environment using tabular Q‑learning. The methodology includes a discrete state representation, reward shaping, and iterative Q‑table updates. While this implementation uses a simple Q‑learning approach, more advanced methods such as Deep Q‑Networks (DQN) can be applied for more complex scenarios.

Happy coding, and enjoy training your Snake AI!
