import logging

import dotenv


def get_args(get_arguments_parser):
    dotenv.load_dotenv()
    parser = get_arguments_parser()
    return parser.parse_args()


def set_logging_config():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s: %(message)s',
        datefmt='%H:%M:%S',
    )