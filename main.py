import asyncio
import gui
import time
import utils
import argparse
import os
import sys

from aiofile import AIOFile
from concurrent.futures import TimeoutError
from datetime import datetime
from socket import gaierror


def get_arguments_parser():
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter_class)
    parser.add_argument('--host', type=str, default=os.getenv('HOST'), help='set host')
    parser.add_argument('--port_reader', type=int, default=os.getenv('PORT_READER'), help='set port reader')
    parser.add_argument('--port_writer', type=int, default=os.getenv('PORT_WRITER'), help='set port writer')
    parser.add_argument('--history', type=str, default=os.getenv('HISTORY'), help='set path to history file')
    parser.add_argument('--nickname', type=str, default=os.getenv('NICKNAME'), help='set your nickname')
    parser.add_argument('--token', type=str, default=os.getenv('TOKEN'), help='set your token')
    return parser


async def main():
    args = utils.get_args(get_arguments_parser)
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    await asyncio.gather(
            restore_history(args.history, messages_queue),
            read_msgs(args.host, args.port_reader, messages_queue, history_queue),
            save_messages(args.history, history_queue),
            send_msgs(args.host, args.port_writer, args.token, args.nickname, sending_queue),
            gui.draw(messages_queue, sending_queue, status_updates_queue))


async def generate_msgs(queue):
    while True:
        queue.put_nowait(f'Ping {time.time()}')
        await asyncio.sleep(1)


async def read_msgs(host, port, queue, history_queue):
    attempt = 0
    while True:
        try:
            reader, writer = await asyncio.open_connection(host=host, port=port)
            if attempt:
                print(await write_message_to_file(args.history, 'Установлено соединение\n'))
                attempt = 0
            message = await get_message_text(reader)
            queue.put_nowait(message)
            history_queue.put_nowait(message)
            #print(await write_message_to_file(args.history, message))

        except (ConnectionRefusedError, ConnectionResetError, gaierror, TimeoutError):
            attempt += 1
            if attempt <= 3:
                error_message = 'Нет соединения. Повторная попытка\n'
                await write_message_to_file(args.history, error_message)
            else:
                error_message = 'Нет соединения. Повторная попытка через 3 сек.\n'
                #print(await write_message_to_file(args.history, error_message))
                await asyncio.sleep(3)
                continue
        finally:
            writer.close()


async def get_message_text(reader):
    data = await asyncio.wait_for(reader.readline(), timeout=5)
    message = data.decode()
    return message


async def write_message_to_file(file, message):
    async with AIOFile(file, 'a') as my_file:
        print(message)
        await my_file.write(message)
    return message


async def save_messages(filepath, queue):
    while True:
        await write_message_to_file(filepath, await queue.get())


async def send_msgs(host, port, token, nickname, queue):
    while True:
        msg = await queue.get()
        print(msg)
        try:
            if not nickname:
                nickname = input('Укажите ваш ник для регистрации: ')
            nickname = nickname.replace('\n', ' ')
            reader, writer = await asyncio.open_connection(host=host, port=port)
            is_authorized = False
            if token:
                is_authorized = await authorise(writer, reader, token, nickname)
                if not is_authorized:
                    print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
            if not is_authorized:
                await register(writer, reader, nickname)
            await submit_message(writer, msg)
        finally:
            writer.close()


async def submit_message(writer, message):
    message = message.replace('\n', ' ')
    writer.write(f'{message}\n\n'.encode())
    await writer.drain()


async def restore_history(filename, queue):
    async with AIOFile(filename, 'r') as afp:
        messages = await afp.read()
        queue.put_nowait(messages.strip())


async def authorise(writer, reader, token, nickname):
    writer.write(f'{token}\n'.encode())
    await reader.readline()
    answer = (await reader.readline()).decode()
    await reader.readline()
    return answer != 'null\n'


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, gui.TkAppClosed) as err:
        sys.exit()
