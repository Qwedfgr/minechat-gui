import argparse
import logging
import os

import dotenv


def get_args():
    dotenv.load_dotenv()

    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter_class)
    parser.add_argument('--host', type=str, default=os.getenv('HOST'), help='set host')
    parser.add_argument('--port_reader', type=int, default=os.getenv('PORT_READER'), help='set port reader')
    parser.add_argument('--port_writer', type=int, default=os.getenv('PORT_WRITER'), help='set port writer')
    parser.add_argument('--history', type=str, default=os.getenv('HISTORY'), help='set path to history file')
    parser.add_argument('--nickname', type=str, default=os.getenv('NICKNAME'), help='set your nickname')
    parser.add_argument('--token', type=str, default=os.getenv('TOKEN'), help='set your token')
    return parser.parse_args()


def set_logging_config():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s: %(message)s',
        datefmt='%H:%M:%S',
    )
