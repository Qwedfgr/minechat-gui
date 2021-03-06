import asyncio
import logging
import sys
from socket import gaierror
from tkinter import messagebox
import argparse
import os

from aiofile import AIOFile
from async_timeout import timeout
import dotenv

import gui
import minechat as mc
import utils

watchdog_logger = logging.getLogger('watchdog_logger')
CONNECTION_TIMEOUT = 10
PING_PONG_TIMEOUT = 15
DELAY_PING_PONG = 15


class InvalidToken(Exception):
    pass


def get_args():
    parent_parser = utils.get_parent_parser()
    parser = argparse.ArgumentParser(parents=[parent_parser])
    parser.add_argument('--history', type=str, default=os.getenv('HISTORY'), help='set path to history file')
    parser.add_argument('--nickname', type=str, default=os.getenv('NICKNAME'), help='set your nickname')
    parser.add_argument('--token', type=str, default=os.getenv('TOKEN'), help='set your token')
    return parser.parse_args()


async def main():
    dotenv.load_dotenv()
    queues = get_queues()
    args = get_args()

    async with utils.create_handy_nursery() as nursery:
        nursery.start_soon(gui.draw(queues['messages_queue'], queues['sending_queue'], queues['status_updates_queue']))
        nursery.start_soon(
            handle_connection(args.host, args.reader_port, args.writer_port, args.history, args.token, queues)
        )
        nursery.start_soon(save_messages(args.history, queues['history_queue']))


async def read_msgs(host, port, history, queues):
    while True:
        async with mc.get_connection(host, port, history, queues) as (reader, _):
            message = await get_message_text(reader)
            queues['messages_queue'].put_nowait(message)
            queues['watchdog_queue'].put_nowait('New message in chat')
            queues['history_queue'].put_nowait(message)


async def get_message_text(reader):
    while True:
        data = await reader.readline()
        message = data.decode()
        return message


async def save_messages(filepath, queue):
    async with AIOFile(filepath, 'a') as my_file:
        while True:
            message = await queue.get()
            await my_file.write(message)


async def send_msgs(reader, writer, queues):
    while True:
        msg = await queues['sending_queue'].get()
        queues['watchdog_queue'].put_nowait('Message sent')
        await mc.submit_message(writer, msg)


async def watch_for_connection(watchdog_queue):
    while True:
        try:
            async with timeout(CONNECTION_TIMEOUT):
                message = await watchdog_queue.get()
                watchdog_logger.info(message)
        except asyncio.TimeoutError:
            watchdog_logger.info(f"{CONNECTION_TIMEOUT} s is elapsed")
            raise ConnectionError


async def handle_connection(host, reader_port, writer_port, history, token, queues):
    while True:
        try:
            async with mc.get_connection(host, writer_port, history, queues) as streams:
                async with timeout(CONNECTION_TIMEOUT):
                    is_authorized, account_info = await mc.authorise(*streams, token)
                    if not is_authorized:
                        messagebox.showerror('Неизвестный токен', 'Проверьте токен или зарегистрируйте заново.')
                        raise InvalidToken
                    event = gui.NicknameReceived(account_info['nickname'])
                    queues['status_updates_queue'].put_nowait(event)

                async with utils.create_handy_nursery() as nursery:
                    nursery.start_soon(mc.restore_history(history, queues['messages_queue']))
                    nursery.start_soon(read_msgs(host, reader_port, history, queues))
                    nursery.start_soon(send_msgs(*streams, queues))
                    nursery.start_soon(watch_for_connection(queues["watchdog_queue"]))
                    nursery.start_soon(ping_pong(*streams, queues["watchdog_queue"]))

        except (ConnectionRefusedError, ConnectionResetError, ConnectionError, asyncio.TimeoutError):
            continue
        else:
            break


def get_queues():
    list_of_queues = ['messages_queue', 'sending_queue', 'status_updates_queue', 'history_queue', 'watchdog_queue']
    queues = {k: asyncio.Queue() for k in list_of_queues}
    return queues


async def ping_pong(reader, writer, watchdog_queue):
    while True:
        try:
            async with timeout(PING_PONG_TIMEOUT):
                writer.write("\n".encode())
                await writer.drain()
                await reader.readline()
            await asyncio.sleep(DELAY_PING_PONG)
            watchdog_queue.put_nowait("Соединение установлено. Пинг сообщение отправлено")

        except gaierror:
            watchdog_queue.put_nowait("socket.gaierror: нет интернет соединения")
            raise ConnectionError()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, gui.TkAppClosed, InvalidToken) as err:
        sys.exit()
