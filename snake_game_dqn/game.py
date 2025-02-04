import os
import pygame
import random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE, SNAKE_SPEED


class SnakeGame:
    """
    Snake game environment.
    """

    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, block_size=BLOCK_SIZE, speed=SNAKE_SPEED, render=True):
        """
        Initialize the game.

        Args:
            width (int): Window width.
            height (int): Window height.
            block_size (int): Size of one grid cell.
            speed (int): Frames per second (when rendering).
            render (bool): Whether to show a window.
        """
        self.width = width
        self.height = height
        self.block_size = block_size
        self.speed = speed
        self.render = render
        # FAST_SIM mode: if enabled (via env var), skip delays even if rendering.
        self.fast_sim = os.environ.get("FAST_SIM", "0").lower() in ("1", "true", "yes")

        if self.render:
            self.display = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Snake DQN")
        else:
            self.display = None

        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        """
        Reset the game to the initial state.
        """
        self.direction = "RIGHT"
        self.head = [self.width // 2, self.height // 2]
        self.snake = [
            self.head[:],
            [self.head[0] - self.block_size, self.head[1]],
            [self.head[0] - 2 * self.block_size, self.head[1]]
        ]
        self.score = 0
        self._place_food()

    def _place_food(self):
        """
        Place food at a random position not occupied by the snake.
        """
        x = random.randrange(0, self.width, self.block_size)
        y = random.randrange(0, self.height, self.block_size)
        self.food = [x, y]
        if self.food in self.snake:
            self._place_food()

    def play_step(self, action):
        """
        Execute one game step.

        Args:
            action (int): Action (0: straight, 1: turn right, 2: turn left)

        Returns:
            tuple: (reward, game_over, score)
        """
        # Process events if rendering.
        if self.render:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

        # Reward shaping: measure Manhattan distance from head to food.
        current_distance = abs(self.head[0] - self.food[0]) + abs(self.head[1] - self.food[1])

        self._move(action)
        self.snake.insert(0, self.head[:])

        reward = 0
        game_over = False

        if self._is_collision():
            game_over = True
            reward = -10
            return reward, game_over, self.score

        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
        else:
            new_distance = abs(self.head[0] - self.food[0]) + abs(self.head[1] - self.food[1])
            reward = 1 if new_distance < current_distance else -1
            self.snake.pop()

        self._update_ui()

        if self.render and not self.fast_sim:
            self.clock.tick(self.speed)
        return reward, game_over, self.score

    def _is_collision(self, point=None):
        """
        Check for collision with walls or self.

        Args:
            point (list): [x, y] to check. Defaults to the head.

        Returns:
            bool: True if a collision occurs.
        """
        if point is None:
            point = self.head
        if point[0] < 0 or point[0] >= self.width or point[1] < 0 or point[1] >= self.height:
            return True
        if point in self.snake[1:]:
            return True
        return False

    def _move(self, action):
        """
        Update the snake's direction and head position based on the action.

        Args:
            action (int): 0: straight, 1: right turn, 2: left turn.
        """
        clock_wise = ["RIGHT", "DOWN", "LEFT", "UP"]
        idx = clock_wise.index(self.direction)

        if action == 1:  # Turn right.
            new_idx = (idx + 1) % 4
        elif action == 2:  # Turn left.
            new_idx = (idx - 1) % 4
        else:  # Straight.
            new_idx = idx

        self.direction = clock_wise[new_idx]

        x, y = self.head
        if self.direction == "RIGHT":
            x += self.block_size
        elif self.direction == "LEFT":
            x -= self.block_size
        elif self.direction == "DOWN":
            y += self.block_size
        elif self.direction == "UP":
            y -= self.block_size

        self.head = [x, y]

    def _update_ui(self):
        """
        Update the game display.
        """
        if self.render:
            self.display.fill((0, 0, 0))
            for pt in self.snake:
                pygame.draw.rect(self.display, (0, 255, 0),
                                 pygame.Rect(pt[0], pt[1], self.block_size, self.block_size))
            pygame.draw.rect(self.display, (255, 0, 0),
                             pygame.Rect(self.food[0], self.food[1], self.block_size, self.block_size))
            font = pygame.font.SysFont("arial", 25)
            text = font.render("Score: " + str(self.score), True, (255, 255, 255))
            self.display.blit(text, [0, 0])
            pygame.display.flip()
