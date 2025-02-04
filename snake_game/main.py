import pygame
from game import SnakeGame
from agent import Agent


def main():
    """
    Main function to run the training loop.
    """
    pygame.init()
    game = SnakeGame()
    agent = Agent()

    n_episodes = 1000  # Adjust the number of episodes for training.
    for episode in range(n_episodes):
        game.reset()
        state = agent.get_state(game)
        total_reward = 0

        while True:
            # Get action from agent.
            action = agent.get_action(state)
            # Perform action and get new state and reward.
            reward, done, score = game.play_step(action)
            state_next = agent.get_state(game)
            # Train agent with the recent experience.
            agent.train_short_memory(state, action, reward, state_next, done)
            state = state_next
            total_reward += reward

            if done:
                print(f"Episode {episode + 1}: Score: {score}, Total Reward: {total_reward}, "
                      f"Epsilon: {agent.epsilon:.3f}")
                break

    # Save the Q-table at the end of training.
    agent.save_model()
    pygame.quit()


if __name__ == "__main__":
    main()
