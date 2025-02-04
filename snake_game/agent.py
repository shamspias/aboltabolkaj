import random
import numpy as np
from game import SnakeGame


class Agent:
    """
    Q-Learning Agent for the Snake game.
    """

    def __init__(self, lr=0.1, gamma=0.9, epsilon=1.0,
                 epsilon_decay=0.995, epsilon_min=0.01):
        """
        Initializes the Q-learning agent.

        Args:
            lr (float): Learning rate.
            gamma (float): Discount factor.
            epsilon (float): Initial exploration rate.
            epsilon_decay (float): Decay rate for epsilon after each step.
            epsilon_min (float): Minimum value for epsilon.
        """
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table = {}  # Dictionary mapping state -> list of Q-values for each action.
        self.n_actions = 3  # Actions: [straight, right turn, left turn].

    def get_state(self, game: SnakeGame):
        """
        Returns the current state as a tuple of 11 binary features:

            1. Danger straight
            2. Danger right
            3. Danger left
            4. Moving left
            5. Moving right
            6. Moving up
            7. Moving down
            8. Food left
            9. Food right
            10. Food up
            11. Food down

        Args:
            game (SnakeGame): The game instance.

        Returns:
            tuple: The state representation.
        """
        head = game.head
        block_size = game.block_size

        # Determine current moving direction.
        dir_l = game.direction == 'LEFT'
        dir_r = game.direction == 'RIGHT'
        dir_u = game.direction == 'UP'
        dir_d = game.direction == 'DOWN'

        # Calculate points in the relative directions.
        if game.direction == 'RIGHT':
            point_straight = [head[0] + block_size, head[1]]
            point_right = [head[0], head[1] + block_size]
            point_left = [head[0], head[1] - block_size]
        elif game.direction == 'LEFT':
            point_straight = [head[0] - block_size, head[1]]
            point_right = [head[0], head[1] - block_size]
            point_left = [head[0], head[1] + block_size]
        elif game.direction == 'UP':
            point_straight = [head[0], head[1] - block_size]
            point_right = [head[0] + block_size, head[1]]
            point_left = [head[0] - block_size, head[1]]
        elif game.direction == 'DOWN':
            point_straight = [head[0], head[1] + block_size]
            point_right = [head[0] - block_size, head[1]]
            point_left = [head[0] + block_size, head[1]]

        # Danger detection.
        danger_straight = game._is_collision(point_straight)
        danger_right = game._is_collision(point_right)
        danger_left = game._is_collision(point_left)

        # Food location relative to head.
        food = game.food
        food_left = food[0] < head[0]
        food_right = food[0] > head[0]
        food_up = food[1] < head[1]
        food_down = food[1] > head[1]

        state = (
            int(danger_straight),
            int(danger_right),
            int(danger_left),
            int(dir_l),
            int(dir_r),
            int(dir_u),
            int(dir_d),
            int(food_left),
            int(food_right),
            int(food_up),
            int(food_down)
        )
        return state

    def get_action(self, state):
        """
        Returns an action based on the current state using an epsilon-greedy strategy.

        Args:
            state (tuple): The current state.

        Returns:
            int: The chosen action (0, 1, or 2).
        """
        # Initialize Q-values for an unseen state.
        if state not in self.q_table:
            self.q_table[state] = [0] * self.n_actions

        # Exploration vs. exploitation.
        if random.random() < self.epsilon:
            action = random.randint(0, self.n_actions - 1)
        else:
            action = int(np.argmax(self.q_table[state]))
        return action

    def train_short_memory(self, state, action, reward, next_state, done):
        """
        Updates the Q-table for a single step using the Q-learning formula.

        Args:
            state (tuple): Previous state.
            action (int): Action taken.
            reward (int): Reward received.
            next_state (tuple): State after taking the action.
            done (bool): True if the game ended.
        """
        if state not in self.q_table:
            self.q_table[state] = [0] * self.n_actions
        if next_state not in self.q_table:
            self.q_table[next_state] = [0] * self.n_actions

        predict = self.q_table[state][action]
        target = reward
        if not done:
            target = reward + self.gamma * max(self.q_table[next_state])
        self.q_table[state][action] = predict + self.lr * (target - predict)

        # Decay epsilon to reduce exploration over time.
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_model(self, file_name="qtable.npy"):
        """
        Saves the Q-table to a file.

        Args:
            file_name (str): Filename for the saved model.
        """
        np.save(file_name, self.q_table)

    def load_model(self, file_name="qtable.npy"):
        """
        Loads the Q-table from a file.

        Args:
            file_name (str): Filename from which to load the model.
        """
        self.q_table = np.load(file_name, allow_pickle=True).item()
