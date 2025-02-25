import asyncio
import curses
import os
import time
from itertools import cycle
from random import choice, randint

from curses_tools import draw_frame, get_frame_size, read_controls

TIC_TIMEOUT = 0.1
ROCKET_SPEED = 10


def draw(canvas):
    """Main drawing function that initializes and runs the animation."""
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)

    symbols = ["+", "*", ".", ":", "-"]
    height, width = canvas.getmaxyx()

    # Add the blinking animation coroutines to the list of coroutines
    coroutines = [
        blink(
            canvas=canvas,
            row=randint(1, height - 2),
            column=randint(1, width - 2),
            delay=randint(1, 10),
            symbol=choice(symbols),
        )
        for _ in range(100)
    ]
    # Add the spaceship animation coroutine to the list of coroutines
    coroutines.append(animate_spaceship(canvas, int(height / 2), int(width / 2)))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
                canvas.border()
        if len(coroutines) == 0:
            break
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


async def blink(canvas, row, column, delay, symbol="*"):
    """Display blinking symbol at given coordinates with random delays."""
    for _ in range(delay):
        await asyncio.sleep(0)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), "*")
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), "O")
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), " ")

    row += rows_speed
    column += columns_speed

    symbol = "-" if columns_speed else "|"

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, start_row, start_column):
    """Animate spaceship on the canvas."""

    rocket_frames = get_rocket_frames()
    rocket_height, rocket_width = get_frame_size(rocket_frames[0])
    rows, columns = canvas.getmaxyx()

    while True:
        for rocket_frame in cycle(rocket_frames):
            rows_direction, columns_direction, space_pressed = read_controls(canvas)

            new_row = start_row + (rows_direction * ROCKET_SPEED)
            new_column = start_column + (columns_direction * ROCKET_SPEED)

            start_row = min(max(1, new_row), rows - rocket_height - 1)
            start_column = min(max(1, new_column), columns - rocket_width - 1)

            draw_frame(canvas, start_row, start_column, rocket_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, start_row, start_column, rocket_frame, negative=True)


def get_rocket_frames():
    """Read rocket frames from files in frames directory and return them"""
    frames = []
    directory = "frames"
    for filename in sorted(os.listdir(directory)):
        if filename.startswith("rocket"):
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
                frames.append(file.read())

    return frames


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
