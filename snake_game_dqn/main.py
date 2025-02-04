import pygame
from agent import Agent
from game import SnakeGame


def run():
    pygame.init()
    game = SnakeGame(render=True)
    agent = Agent()

    # Now that the load method exists, we can do:
    agent.model.load("model_dqn.pth")
    agent.epsilon = 0  # Disable exploration for evaluation

    while True:
        game.reset()
        state = agent.get_state(game)
        while True:
            action = agent.get_action(state)
            reward, done, score = game.play_step(action)
            state = agent.get_state(game)
            if done:
                print("Score:", score)
                break


if __name__ == "__main__":
    run()
