# Snake AI with Deep Q-Network (DQN) Reinforcement Learning

## Overview

This project implements a classic Snake game where an AI agent learns to play using Deep Q-Networks (DQN). The agent is trained using reinforcement learning techniques with a neural network approximating the Q‑function. The game environment is built with Python and Pygame, and the neural network and training are implemented using PyTorch. Techniques such as experience replay and an epsilon‑greedy strategy are used to stabilize and accelerate training.

## Process & Methodology

### Process

1. **Environment Setup:**  
   The Snake game is created using Pygame. The game environment defines a discrete state space consisting of 11 binary features that capture:
   - Immediate danger (collision) in three directions (straight, right, left)
   - The snake's current moving direction (left, right, up, down)
   - The relative location of the food (left, right, up, down)

2. **Action Selection:**  
   The agent has three possible actions:
   - **Straight**
   - **Turn Right**
   - **Turn Left**  
   An **epsilon‑greedy strategy** is used to balance exploration and exploitation. Early in training, the agent takes random actions; later, it favors actions with the highest predicted Q‑values.

3. **Reward Structure:**  
   The reward function is designed to encourage:
   - **+10** for eating food.
   - **–10** for collisions (hitting the wall or itself).
   - A small **+1** reward for moving closer to the food and **–1** for moving farther away, which helps guide the agent during the early stages of learning.

4. **Learning Process:**  
   The DQN approximates the Q‑function using a fully-connected neural network. The agent stores its experiences (state, action, reward, next state, done) in an experience replay buffer. Random mini-batches are sampled from this buffer to perform gradient descent updates using the Mean Squared Error (MSE) loss between the predicted Q‑values and the target Q‑values.

### Methodology

- **Deep Q-Network (DQN):**  
  Instead of maintaining a Q‑table, the agent uses a neural network to approximate Q‑values for each action given a state. This is especially useful when the state space is large or continuous.
  
- **Experience Replay:**  
  By storing past experiences in a buffer and training on random mini-batches, the agent breaks the correlation between sequential data and stabilizes learning.

- **Epsilon‑Greedy Policy:**  
  The agent starts with a high exploration rate (epsilon) and gradually decays it, ensuring that it explores enough of the state space early on and later exploits the learned policy.

### Mathematical Formulation

The core idea behind Q‑learning (and thus DQN) is to approximate the optimal action-value function \( Q^*(s,a) \) using the Bellman equation:

![Q‑learning](https://quicklatex.com/cache3/19/ql_5f8679b1a895c827e9ea829d0ee43819_l3.png)

In DQN, this equation is used to compute the target Q‑value during training. The neural network parameters \( \theta \) are updated by minimizing the loss:
![DQN](https://quicklatex.com/cache3/2e/ql_fc635e1506b823e007ddef19073ddf2e_l3.png)


Where:

![description](https://quicklatex.com/cache3/ed/ql_648c3be9f4207d4a16754a86bb0e45ed_l3.png)

This loss is minimized via stochastic gradient descent using optimizers such as Adam.

## Project Structure

```
snake_game_dqn/
├── agent.py         # Contains the DQN model, training routines, and experience replay buffer.
├── constants.py     # Global constants for the game.
├── game.py          # Pygame-based Snake game environment.
├── train.py         # Training loop for the DQN agent.
└── main.py          # Runs the game in evaluation mode using the trained model.
```

## How It Works

1. **Initialization:**  
   - The Snake game environment and DQN agent are initialized.
   - The state is represented as an 11-dimensional binary vector.

2. **Gameplay & Training:**  
   - In each game (episode), the agent selects an action using an epsilon‑greedy strategy.
   - The game environment returns a reward and a new state.
   - The experience is stored in the replay buffer.
   - Mini-batches from the buffer are used to update the neural network via backpropagation.
   - The training process continues until manually stopped or until a target performance is reached.

3. **Evaluation:**  
   - After training, the model parameters are saved to disk (e.g., `model_dqn.pth`).
   - In evaluation mode (run via `main.py`), the trained model is loaded, and the agent uses a greedy policy (with exploration turned off) to play the game.

## Setup and Execution

### Requirements

- Python 3.12+  
- [Pygame](https://www.pygame.org/)  
- [PyTorch](https://pytorch.org/)  
- NumPy  
- Matplotlib

Install the required packages using:

```bash
pip install pygame torch numpy matplotlib
```

### Training the Agent

To train the DQN agent (using fast, headless simulation), run:

```bash
python train.py
```

You can adjust simulation speed and other parameters via environment variables. For example, to run training with visuals in fast simulation mode, use:

```bash
export TRAIN_RENDER=1
export FAST_SIM=1
python train.py
```

*Note:* Visual mode is best used with a single game instance.

### Running the Game (Evaluation)

After training and saving the model (as `model_dqn.pth`), run:

```bash
python main.py
```

This launches the game with the trained DQN agent playing using a greedy policy.

## Conclusion

This project demonstrates the application of Deep Q-Networks to the classic Snake game. By leveraging a neural network to approximate the Q‑function along with techniques like experience replay and an epsilon‑greedy strategy, the agent learns to maximize its score over time. While this implementation uses a simple fully-connected network, you can experiment further by tuning hyperparameters, modifying the network architecture, or employing more advanced techniques such as target networks.

Happy coding, and enjoy training your Snake AI with DQN!