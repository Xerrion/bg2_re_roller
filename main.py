import logging
import sys
import time

import cv2
import numpy as np
import pyautogui
import pytesseract
from pygetwindow import Win32Window
from pynput import keyboard

# Constants
DEBUG: bool = False
MAX_ROLL_FILE: str = "max_roll.txt"
RE_ROLL_TEMPLATE: str = "assets/reroll.png"
STORE_TEMPLATE: str = "assets/store.png"
TESSERACT_CONFIG: str = "--psm 6 -c tessedit_char_whitelist=0123456789"
ROI_X_OFFSET: int = 385
ROI_Y_OFFSET: int = 615
ROI_WIDTH: int = 35
ROI_HEIGHT: int = 20
GAME_WINDOW_TITLE: str = "Baldur's Gate II - Enhanced Edition"

# Setup logging with timestamp, log level and message
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)

# Variable to store the exit request
exit_requested = False

# The key combination to check
COMBINATION = {keyboard.Key.ctrl_l, keyboard.Key.space}

# The currently active modifiers
current_keys = set()


def on_press(key):
    if key in COMBINATION:
        print("Key pressed: {}".format(key))
        current_keys.add(key)

        if COMBINATION.issubset(current_keys):
            print("Exiting...")
            global exit_requested
            exit_requested = True


def on_release(key):
    try:
        current_keys.remove(key)
    except KeyError:
        pass  # Deal with a key like shift being released


def get_game_window() -> Win32Window:
    """
    Function to find and return the game window.

    :return: The game window.
    """
    window = pyautogui.getWindowsWithTitle(GAME_WINDOW_TITLE)[0]
    if window:
        return window
    else:
        logging.error("Could not find the game window. Exiting...")
        sys.exit()


def load_max_roll() -> int:
    """
    Function to load previous max roll from a file.

    :return: The previous max roll or 0 if the file does not exist.
    """
    try:
        with open(MAX_ROLL_FILE, "r") as f:
            return int(f.read())
    except ValueError:
        logging.error("Could not convert max_roll.txt to an integer. Starting with 0.")
        return 0
    except FileNotFoundError:
        logging.warning("Could not find max_roll.txt. Starting with 0.")
        return 0


def find_template(image, template) -> tuple:
    """
    Function to find the location of a template within an image.

    :param image: The image to search in.
    :param template: The template to search for.
    :return: The x and y coordinates of the template.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    return max_loc


def setup_coordinates(window_x, window_y) -> tuple:
    """
    Function to set up the region of interest (ROI) and the re-roll and store buttons.

    :param window_x: The x coordinate of the game window.
    :param window_y: The y coordinate of the game window.
    :return: The x and y coordinates of the re-roll button, the ROI and the store button.
    """
    # Load templates and screenshot
    re_roll_template = cv2.imread(RE_ROLL_TEMPLATE, 0)
    store_template = cv2.imread(STORE_TEMPLATE, 0)
    capture = pyautogui.screenshot()
    screenshot: np.ndarray = np.array(capture)

    # Find re-roll button and store button
    re_roll_button_loc: tuple = find_template(screenshot, re_roll_template)
    re_roll_button_x: int = re_roll_button_loc[0] + int(re_roll_template.shape[1] / 2)
    re_roll_button_y: int = re_roll_button_loc[1] + int(re_roll_template.shape[0] / 2)
    store_button_loc: tuple = find_template(screenshot, store_template)
    store_button_x: int = store_button_loc[0] + int(store_template.shape[1] / 2)
    store_button_y: int = store_button_loc[1] + int(store_template.shape[0] / 2)

    # Calculate ROI coordinates
    roi_x: int = window_x + ROI_X_OFFSET
    roi_y: int = window_y + ROI_Y_OFFSET

    # Return coordinates
    return re_roll_button_x, re_roll_button_y, roi_x, roi_y, store_button_x, store_button_y


def extract_roll(roi) -> int | None:
    """
    Function to extract roll value from a region of interest (ROI).

    :param roi: The region of interest (ROI) to extract the roll value from.
    :return: The roll value as an integer or None if the roll value could not be extracted.
    """
    try:
        roll = pytesseract.image_to_string(roi, config=TESSERACT_CONFIG)
        return int(roll)
    except pytesseract.TesseractError:
        logging.error("Tesseract failed to extract text from image. Skipping this roll.")
        return None
    except ValueError:
        logging.warning("Could not convert roll to an integer. Skipping this roll.")
        return None


def debug_screenshot(roi, roll):
    """
    Function to show the ROI and roll value for debugging.
    :param roi: The region of interest (ROI) to show.
    :param roll: The roll value to show.
    :return: None
    """
    # Print the ROI for debugging
    print("ROI shape: ", roi.shape)
    print("Roll: ", roll)

    # Show the ROI and roll value
    cv2.imshow("ROI", roi)
    cv2.waitKey(0)


def main():
    """
    Main function to automate the game.
    """
    # Get the game window
    window: Win32Window = get_game_window()

    # Load previous max roll
    max_roll: int = load_max_roll()

    # Get the game window coordinates
    window_x, window_y = window.left, window.top

    # Activate the game window
    if not window.isActive:
        window.activate()

    # Wait for the window to be active
    time.sleep(0.2)

    # Set up the ROI and buttons
    re_roll_button_x, re_roll_button_y, roi_x, roi_y, store_button_x, store_button_y = setup_coordinates(
        window_x, window_y
    )

    # Set up the listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        # Now you would put your main loop here
        while not exit_requested:
            # Capture a screenshot for value extraction
            capture: np.ndarray = np.array(pyautogui.screenshot())
            roi: np.ndarray = capture[roi_y : roi_y + ROI_HEIGHT, roi_x : roi_x + ROI_WIDTH]

            # Extract roll value
            roll = extract_roll(roi)

            time.sleep(1)

            # If roll extraction failed, skip this roll
            if roll is None:
                continue

            logging.info(f"Current roll: {roll}")

            # If new roll is better, store it
            if roll > max_roll:
                # Click the store button
                pyautogui.click(store_button_x, store_button_y, clicks=2, interval=0.1)

                # Write the new max roll to a file
                with open(MAX_ROLL_FILE, "w") as f:
                    logging.info(f"Writing {roll} to max_roll.txt...")
                    f.write(str(roll))

                # Update max roll
                max_roll = roll

            logging.info(f"Current max roll: {max_roll}")

            # Exit if a good roll is found
            if roll >= 100:
                break

            # Click the re-roll button
            pyautogui.click(re_roll_button_x, re_roll_button_y)
        listener.stop()


if __name__ == "__main__":
    main()
