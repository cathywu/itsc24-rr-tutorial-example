from pprint import pprint
from environment import *
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='1.041/1.200 CP1')
    parser.add_argument('--run-idm', action='store_true')
    parser.add_argument('--run-custom', action='store_true')
    parser.add_argument('--no-render', action='store_true', default=False)
    args = parser.parse_args()

    pprint(vars(args))
    print("[INFO] Starting the simulator...")

    game = Environment(args)
    print("[INFO] Created Environment Object...")
    game.run()
    print("[INFO] End of the simulation...")
