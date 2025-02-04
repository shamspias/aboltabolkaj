import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque
from game import SnakeGame

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001


class Linear_QNet(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(Linear_QNet, self).__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, hidden_size)
        self.linear3 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = torch.relu(self.linear1(x))
        x = torch.relu(self.linear2(x))
        x = self.linear3(x)
        return x

    def save(self, file_name='model_dqn.pth'):
        torch.save(self.state_dict(), file_name)

    def load(self, file_name='model_dqn.pth'):
        self.load_state_dict(torch.load(file_name))
        self.eval()


class QTrainer:
    def __init__(self, model, lr, gamma):
        self.lr = lr
        self.gamma = gamma
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        self.criterion = nn.MSELoss()

    def train_step(self, state, action, reward, next_state, done):
        state = torch.tensor(np.array(state), dtype=torch.float)
        next_state = torch.tensor(np.array(next_state), dtype=torch.float)
        action = torch.tensor(np.array(action), dtype=torch.long)
        reward = torch.tensor(np.array(reward), dtype=torch.float)

        if len(state.shape) == 1:
            state = torch.unsqueeze(state, 0)
            next_state = torch.unsqueeze(next_state, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            done = (done,)

        # Predict Q values with current state.
        pred = self.model(state)

        target = pred.clone()
        for idx in range(len(done)):
            Q_new = reward[idx]
            if not done[idx]:
                Q_new = reward[idx] + self.gamma * torch.max(self.model(next_state[idx]))
            target[idx][action[idx].item()] = Q_new

        self.optimizer.zero_grad()
        loss = self.criterion(target, pred)
        loss.backward()
        self.optimizer.step()


class Agent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0  # will be set based on number of games played
        self.gamma = 0.9
        self.memory = deque(maxlen=MAX_MEMORY)  # Experience replay buffer
        self.model = Linear_QNet(11, 128, 3)  # 11 input features, 3 possible actions
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, game: SnakeGame):
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

        state = [
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
        ]
        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        """
        Store an experience in memory.
        """
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        """
        Train using a batch of experiences from memory.
        """
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        if mini_sample:
            states, actions, rewards, next_states, dones = zip(*mini_sample)
            self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        """
        Train on the most recent move.
        """
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        """
        Return an action using an epsilon-greedy strategy.

        Args:
            state (ndarray): The current state.

        Returns:
            int: Chosen action (0, 1, or 2).
        """
        # Decrease epsilon as the number of games increases.
        self.epsilon = max(0, 80 - self.n_games)
        if random.randint(0, 200) < self.epsilon:
            return random.randint(0, 2)
        else:
            state0 = torch.tensor(state, dtype=torch.float).unsqueeze(0)
            prediction = self.model(state0)
            return torch.argmax(prediction).item()
