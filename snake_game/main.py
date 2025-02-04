import os
import pygame
from game import SnakeGame
from agent import Agent


def main():
    """
    Run the game with a trained agent.
    """
    pygame.init()
    game = SnakeGame(render=True)
    agent = Agent()

    if os.path.exists("qtable_trained.npy"):
        agent.load_model("qtable_trained.npy")
        print("Loaded trained Q-table.")
        # Force a greedy policy for evaluation.
        agent.epsilon = agent.epsilon_min
    else:
        print("No trained model found. Running with an untrained agent.")

    while True:
        game.reset()
        state = agent.get_state(game)
        while True:
            action = agent.get_action(state)
            reward, done, score = game.play_step(action)
            state = agent.get_state(game)
            if done:
                print(f"Score: {score}")
                break


if __name__ == "__main__":
    main()
