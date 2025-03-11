import asyncio
import curses
import os
import time
from itertools import cycle
from random import choice, randint

from curses_tools import draw_frame, get_frame_size, read_controls
from obstacles import Obstacle
from physics import update_speed

TIC_TIMEOUT = 0.1


def draw(canvas):
    """Main drawing function that initializes and runs the animation."""
    global coroutines, obstacles

    curses.curs_set(False)
    canvas.nodelay(True)

    symbols = ["+", "*", ".", ":", "-"]
    height, width = canvas.getmaxyx()
    obstacles = []

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
    # Add the garbage fly animation coroutine to the list of coroutines
    coroutines.append(fill_in_garbage(canvas))
    # Add the spaceship animation coroutine to the list of coroutines
    coroutines.append(animate_spaceship(canvas, int(height / 2), int(width / 2)))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
        canvas.border()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


async def blink(canvas, row, column, delay, symbol="*"):
    """Display blinking symbol at given coordinates with random delays."""
    for _ in range(delay):
        await asyncio.sleep(0)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)
        canvas.addstr(row, column, symbol)
        await sleep(3)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)
        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fire(
    canvas,
    start_row,
    start_column,
    row_correction=0,
    column_correction=0,
    rows_speed=-2,
    columns_speed=0,
):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row + row_correction, start_column + column_correction

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

        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                return


async def fill_in_garbage(canvas):
    """
    Continuously generate and add garbage (trash) objects to the canvas.
    """

    _, width = canvas.getmaxyx()
    garbage_frames = read_frames("trash")
    while True:
        trash = fly_garbage(
            canvas,
            randint(2, width - 2),
            choice(garbage_frames),
        )
        await asyncio.sleep(0)
        coroutines.append(trash)
        await asyncio.sleep(0)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """
    Animate garbage, flying from top to bottom.
    Column position will stay same, as specified on start.
    """
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    obstacle_width, obstacle_height = get_frame_size(garbage_frame)
    obstacle = Obstacle(0, column, obstacle_width, obstacle_height)
    obstacles.append(obstacle)

    row = 0
    try:
        while row < rows_number:
            draw_frame(canvas, row, column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed
            obstacle.row = row
    finally:
        obstacles.remove(obstacle)


async def animate_spaceship(canvas, start_row, start_column):
    """Animate spaceship on the canvas."""

    rocket_frames = read_frames("rocket")
    rocket_height, rocket_width = get_frame_size(rocket_frames[0])
    rows, columns = canvas.getmaxyx()
    row_speed, column_speed = (0, 0)

    while True:
        for rocket_frame in cycle(rocket_frames):
            for _ in range(2):
                rows_direction, columns_direction, space_pressed = read_controls(canvas)
                row_speed, column_speed = update_speed(
                    row_speed, column_speed, rows_direction, columns_direction
                )

                new_row = start_row + rows_direction + row_speed
                new_column = start_column + columns_direction + column_speed

                start_row = min(max(1, new_row), rows - rocket_height - 1)
                start_column = min(max(1, new_column), columns - rocket_width - 1)

                if space_pressed:
                    coroutines.append(
                        fire(canvas, start_row, start_column, column_correction=2)
                    )

                draw_frame(canvas, start_row, start_column, rocket_frame)
                await asyncio.sleep(0)
                draw_frame(canvas, start_row, start_column, rocket_frame, negative=True)


def read_frames(frame_type: str) -> list:
    """
    Read frames from files in the frames directory and return them as a list.

    Args:
        frame_type (str): Type of frames to read. Can be either 'rocket' or 'trash'.

    Returns:
        list: A list of strings, where each string represents the content of a frame file.
    """
    frames = []
    directory = "frames"
    for filename in sorted(os.listdir(directory)):
        if filename.startswith(frame_type):
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
                frames.append(file.read())

    return frames


async def sleep(tics=1):
    """Pause the execution of a coroutine for a specified number of tics"""
    for _ in range(tics):
        await asyncio.sleep(0)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
