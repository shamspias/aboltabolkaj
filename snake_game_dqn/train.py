import os
import pygame
import matplotlib.pyplot as plt
from agent import Agent
from game import SnakeGame

# Read TRAIN_BEST_SCORE from the environment, if set; otherwise, use a high default.
TRAIN_BEST_SCORE = int(os.environ.get("TRAIN_BEST_SCORE", "10"))


def plot(scores, mean_scores):
    plt.clf()
    plt.title('Training...')
    plt.xlabel('Number of Games')
    plt.ylabel('Score')
    plt.plot(scores, label='Score per Game')
    plt.plot(mean_scores, label='Mean Score')
    plt.legend()
    plt.pause(0.001)


def train():
    pygame.init()
    agent = Agent()
    game = SnakeGame(render=False)
    scores = []
    mean_scores = []
    total_score = 0
    record = 0

    while True:
        game.reset()
        state_old = agent.get_state(game)
        done = False
        score = 0

        while not done:
            action = agent.get_action(state_old)
            reward, done, score = game.play_step(action)
            state_new = agent.get_state(game)
            agent.train_short_memory(state_old, action, reward, state_new, done)
            agent.remember(state_old, action, reward, state_new, done)
            state_old = state_new

        agent.n_games += 1
        agent.train_long_memory()

        if score > record:
            record = score
            agent.model.save("model_dqn.pth")

        print("Game", agent.n_games, "Score", score, "Record:", record)
        scores.append(score)
        total_score += score
        mean_score = total_score / agent.n_games
        mean_scores.append(mean_score)
        plot(scores, mean_scores)

        # Check if we've reached the target best score.
        if record >= TRAIN_BEST_SCORE:
            print(f"Target record of {TRAIN_BEST_SCORE} reached. Stopping training.")
            break

    pygame.quit()


if __name__ == "__main__":
    train()
