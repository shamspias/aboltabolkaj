import pygame
import random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE, SNAKE_SPEED


class SnakeGame:
    """
    Class representing the Snake game environment.
    """

    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
                 block_size=BLOCK_SIZE, speed=SNAKE_SPEED):
        """
        Initializes the game.

        Args:
            width (int): Width of the game window.
            height (int): Height of the game window.
            block_size (int): Size of one block in the grid.
            speed (int): Game speed (frames per second).
        """
        self.width = width
        self.height = height
        self.block_size = block_size
        self.speed = speed

        # Initialize pygame display and clock.
        self.display = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake AI')
        self.clock = pygame.time.Clock()

        # Initialize game state.
        self.reset()

    def reset(self):
        """
        Resets the game state to the starting position.
        """
        self.direction = 'RIGHT'
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
        Places food in a random location not occupied by the snake.
        """
        x = random.randrange(0, self.width, self.block_size)
        y = random.randrange(0, self.height, self.block_size)
        self.food = [x, y]
        # Ensure food is not placed on the snake.
        if self.food in self.snake:
            self._place_food()

    def play_step(self, action):
        """
        Executes one step of the game.

        Args:
            action (int): Action to take (0: straight, 1: right turn, 2: left turn).

        Returns:
            tuple: (reward (int), game_over (bool), score (int))
        """
        # Process pygame events.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Move the snake based on the action.
        self._move(action)  # update self.head
        self.snake.insert(0, self.head[:])

        reward = 0
        game_over = False

        # Check for collisions.
        if self._is_collision():
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # Check if food is eaten.
        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
        else:
            # Remove the tail if no food eaten.
            self.snake.pop()

        self._update_ui()
        self.clock.tick(self.speed)
        return reward, game_over, self.score

    def _is_collision(self, point=None):
        """
        Checks if the given point (or the snake's head if None) collides with the boundary or itself.

        Args:
            point (list): [x, y] coordinates to check. Defaults to the snake's head.

        Returns:
            bool: True if collision occurs, False otherwise.
        """
        if point is None:
            point = self.head

        # Check boundary collision.
        if (point[0] < 0 or point[0] >= self.width or
                point[1] < 0 or point[1] >= self.height):
            return True

        # Check self-collision.
        if point in self.snake[1:]:
            return True

        return False

    def _move(self, action):
        """
        Updates the snake's direction and head position based on the given action.

        Args:
            action (int): Action to take (0: straight, 1: right turn, 2: left turn).
        """
        # Define directions in clockwise order.
        clock_wise = ['RIGHT', 'DOWN', 'LEFT', 'UP']
        idx = clock_wise.index(self.direction)

        if action == 1:  # Right turn: (clockwise)
            new_idx = (idx + 1) % 4
        elif action == 2:  # Left turn: (counter-clockwise)
            new_idx = (idx - 1) % 4
        else:  # No change (straight).
            new_idx = idx

        self.direction = clock_wise[new_idx]

        x, y = self.head
        if self.direction == 'RIGHT':
            x += self.block_size
        elif self.direction == 'LEFT':
            x -= self.block_size
        elif self.direction == 'DOWN':
            y += self.block_size
        elif self.direction == 'UP':
            y -= self.block_size

        self.head = [x, y]

    def _update_ui(self):
        """
        Updates the user interface (drawing the snake, food, and score).
        """
        # Fill background.
        self.display.fill((0, 0, 0))
        # Draw snake.
        for pt in self.snake:
            pygame.draw.rect(self.display, (0, 255, 0),
                             pygame.Rect(pt[0], pt[1], self.block_size, self.block_size))
        # Draw food.
        pygame.draw.rect(self.display, (255, 0, 0),
                         pygame.Rect(self.food[0], self.food[1], self.block_size, self.block_size))
        # Draw score.
        font = pygame.font.SysFont('arial', 25)
        text = font.render("Score: " + str(self.score), True, (255, 255, 255))
        self.display.blit(text, [0, 0])
        pygame.display.flip()
