import random
import numpy as np
from game import SnakeGame


class Agent:
    """
    Q-Learning agent for Snake.
    """

    def __init__(self, lr=0.1, gamma=0.9, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01):
        """
        Initialize the agent.

        Args:
            lr (float): Learning rate.
            gamma (float): Discount factor.
            epsilon (float): Exploration rate.
            epsilon_decay (float): Epsilon decay factor.
            epsilon_min (float): Minimum epsilon.
        """
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table = {}  # Maps state tuple to a list of Q-values (one per action)
        self.n_actions = 3

    def get_state(self, game: SnakeGame):
        """
        Compute the state as an 11-dimensional binary tuple:
            0: Danger straight
            1: Danger right
            2: Danger left
            3: Moving left
            4: Moving right
            5: Moving up
            6: Moving down
            7: Food left
            8: Food right
            9: Food up
            10: Food down

        Args:
            game (SnakeGame): The game instance.

        Returns:
            tuple: The state.
        """
        head = game.head
        block_size = game.block_size

        dir_left = game.direction == "LEFT"
        dir_right = game.direction == "RIGHT"
        dir_up = game.direction == "UP"
        dir_down = game.direction == "DOWN"

        if game.direction == "RIGHT":
            point_straight = [head[0] + block_size, head[1]]
            point_right = [head[0], head[1] + block_size]
            point_left = [head[0], head[1] - block_size]
        elif game.direction == "LEFT":
            point_straight = [head[0] - block_size, head[1]]
            point_right = [head[0], head[1] - block_size]
            point_left = [head[0], head[1] + block_size]
        elif game.direction == "UP":
            point_straight = [head[0], head[1] - block_size]
            point_right = [head[0] + block_size, head[1]]
            point_left = [head[0] - block_size, head[1]]
        elif game.direction == "DOWN":
            point_straight = [head[0], head[1] + block_size]
            point_right = [head[0] - block_size, head[1]]
            point_left = [head[0] + block_size, head[1]]

        danger_straight = game._is_collision(point_straight)
        danger_right = game._is_collision(point_right)
        danger_left = game._is_collision(point_left)

        food = game.food
        food_left = food[0] < head[0]
        food_right = food[0] > head[0]
        food_up = food[1] < head[1]
        food_down = food[1] > head[1]

        state = (
            int(danger_straight),
            int(danger_right),
            int(danger_left),
            int(dir_left),
            int(dir_right),
            int(dir_up),
            int(dir_down),
            int(food_left),
            int(food_right),
            int(food_up),
            int(food_down)
        )
        return state

    def get_action(self, state):
        """
        Choose an action using epsilon-greedy.

        Args:
            state (tuple): Current state.

        Returns:
            int: Action (0, 1, or 2).
        """
        if state not in self.q_table:
            self.q_table[state] = [0] * self.n_actions

        if random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        return int(np.argmax(self.q_table[state]))

    def train_short_memory(self, state, action, reward, next_state, done):
        """
        Perform a Q-learning update for one step.

        Args:
            state (tuple): Current state.
            action (int): Action taken.
            reward (float): Reward received.
            next_state (tuple): Next state.
            done (bool): Whether the episode is done.
        """
        if state not in self.q_table:
            self.q_table[state] = [0] * self.n_actions
        if next_state not in self.q_table:
            self.q_table[next_state] = [0] * self.n_actions

        predict = self.q_table[state][action]
        target = reward if done else reward + self.gamma * max(self.q_table[next_state])
        self.q_table[state][action] = predict + self.lr * (target - predict)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_model(self, file_name="qtable_trained.npy"):
        """
        Save the Q-table.
        """
        np.save(file_name, self.q_table)

    def load_model(self, file_name="qtable_trained.npy"):
        """
        Load the Q-table.
        """
        self.q_table = np.load(file_name, allow_pickle=True).item()
