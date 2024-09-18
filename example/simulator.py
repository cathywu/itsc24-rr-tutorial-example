import logging
from pprint import pprint
from environment import Environment
import argparse

import config as c


logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=c.PROJECT_NAME)
    parser.add_argument('--run-idm', action='store_true')
    parser.add_argument('--run-custom', action='store_true')
    parser.add_argument('--no-render', action='store_true', default=False)
    parser.add_argument('--plot-gif', action='store_true', default=False)
    args = parser.parse_args()

    logging.info(f"Arugments {vars(args)}")
    logging.info("Starting the simulator...")

    game = Environment(args)
    logging.info("Created Environment Object...")
    game.run()
    logging.info("End of the simulation...")
