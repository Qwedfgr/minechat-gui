import argparse
import logging
import os
from contextlib import asynccontextmanager

import aionursery


def get_parent_parser():
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter_class, add_help=False)
    parser.add_argument('--host', type=str, default=os.getenv('HOST'), help='set host')
    parser.add_argument('--reader_port', type=int, default=os.getenv('READER_PORT'), help='set port reader')
    parser.add_argument('--writer_port', type=int, default=os.getenv('WRITER_PORT'), help='set port writer')
    return parser


def set_logging_config():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s: %(message)s',
        datefmt='%H:%M:%S',
    )


@asynccontextmanager
async def create_handy_nursery():
    try:
        async with aionursery.Nursery() as nursery:
            yield nursery
    except aionursery.MultiError as e:
        if len(e.exceptions) == 1:
            raise e.exceptions[0] from None
        raise
