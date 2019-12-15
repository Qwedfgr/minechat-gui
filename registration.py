import asyncio
import json
import sys
import tkinter as tk

import gui
import utils


async def draw(registration_queue):
    root = tk.Tk()
    root.title('Регистрация нового пользователя')

    root_frame = tk.Frame(root, width=300)
    root_frame.pack()

    label = tk.Label(height=1, text='Введите ник')
    label.pack()

    username_input = tk.Entry(width=20)
    username_input.pack(pady=5)

    register_button = tk.Button(text='Зарегистрироваться', bd=1)
    register_button.bind(
        '<Button-1>', lambda event: get_username(
            username_input,
            registration_queue
        )
    )
    register_button.pack(pady=10)

    async with utils.create_handy_nursery() as nursery:
        nursery.start_soon(gui.update_tk(root_frame))


def get_username(username_input, registration_queue):
    username = username_input.get()
    registration_queue.put_nowait(username)
    username_input.delete(0, tk.END)


async def handle_connection(host, port_writer, queue):
    while True:
        try:
            reader, writer = await asyncio.open_connection(host=host, port=port_writer)
            user_info = await register(writer, reader, queue)
            token = user_info['account_hash']
            save_to_env(token)
        except Exception as e:
            print(e)


def save_to_env(token):
    with open('.env', 'r') as env_file:
        data = env_file.read()
    old_line = ''
    for line in data.split('\n'):
        if line.startswith('TOKEN='):
            old_line = line
    new_line = f'TOKEN={token}'
    if old_line:
        data = data.replace(old_line, new_line)
    else:
        data += new_line
    with open('.env', 'w') as env_file:
        env_file.write(data)


async def register(writer, reader, queue):
    nickname = await queue.get()
    writer.write(f'\n'.encode())
    await writer.drain()
    await reader.readline()
    writer.write(f'{nickname}\n'.encode())
    await writer.drain()
    await reader.readline()
    user_info = (await reader.readline()).decode()
    return json.loads(user_info)


async def main():
    registration_queue = asyncio.Queue()
    args = utils.get_args()

    async with utils.create_handy_nursery() as nursery:
        nursery.start_soon(
            draw(registration_queue)
        )

        nursery.start_soon(
            handle_connection(args.host, args.port_writer, registration_queue)
        )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, gui.TkAppClosed) as err:
        sys.exit()
