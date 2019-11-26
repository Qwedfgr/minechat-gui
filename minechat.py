import asyncio
import json
from contextlib import asynccontextmanager
from socket import gaierror

from aiofile import AIOFile

import gui


@asynccontextmanager
async def get_connection(host, port, queues):
    status_updates_queue = queues['status_updates_queue']
    reader, writer = await open_connection(host, port, queues)
    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    try:
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
        yield (reader, writer)
    finally:
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)
        writer.close()


async def open_connection(host, port, queues):
    attempt = 0
    while True:
        try:
            reader, writer = await asyncio.open_connection(host=host, port=port)
            queues['status_updates_queue'].put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            if attempt:
                print(await write_message_to_file(args.history, 'Установлено соединение\n'))
                attempt = 0
            return reader, writer
        except (ConnectionRefusedError, ConnectionResetError, gaierror, TimeoutError):
            attempt += 1
            if attempt <= 3:
                error_message = 'Нет соединения. Повторная попытка\n'
                await write_message_to_file(args.history, error_message)
            else:
                error_message = 'Нет соединения. Повторная попытка через 3 сек.\n'
                # print(await write_message_to_file(args.history, error_message))
                await asyncio.sleep(3)
                continue


async def submit_message(writer, message):
    message = message.replace('\n', ' ')
    writer.write(f'{message}\n\n'.encode())
    await writer.drain()


async def restore_history(filename, queue):
    async with AIOFile(filename, 'r') as afp:
        messages = await afp.read()
        queue.put_nowait(messages.strip())


async def authorise(reader, writer, token):
    writer.write(f'{token}\n'.encode())
    await reader.readline()
    answer = (await reader.readline()).decode()
    await reader.readline()
    return answer != 'null\n', json.loads(answer)


async def write_message_to_file(file, message):
    async with AIOFile(file, 'a') as my_file:
        await my_file.write(message)
    return message
