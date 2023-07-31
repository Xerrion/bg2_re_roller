import logging
import sys
import time
from collections import Counter

import cv2
import keyboard
import numpy as np
import pyautogui
import pytesseract
from pygetwindow import Win32Window

# Constants
DEBUG: bool = False
MAX_ROLL_FILE: str = "max_roll.txt"
REROLL_TEMPLATE: str = "assets/reroll.png"
STORE_TEMPLATE: str = "assets/store.png"
TESSERACT_CONFIG: str = "--psm 6 -c tessedit_char_whitelist=0123456789"
ROI_X_OFFSET: int = 385
ROI_Y_OFFSET: int = 610
ROI_WIDTH: int = 40
ROI_HEIGHT: int = 25
GAME_WINDOW_TITLE: str = "Baldur's Gate II - Enhanced Edition"

# Setup logging with timestamp, log level and message
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)


def get_game_window() -> Win32Window:
    """
    Function to find and return the game window.
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
    """
    try:
        with open(MAX_ROLL_FILE, "r") as f:
            return int(f.read())
    except FileNotFoundError:
        logging.warning("Could not find max_roll.txt. Starting with 0.")
        return 0


def find_template(image, template) -> tuple:
    """
    Function to find the location of a template within an image.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    return max_loc


def setup_roi_and_buttons(window_x, window_y) -> tuple:
    """
    Function to setup the region of interest (ROI) and the re-roll and store buttons.

    :param window_x:
    :param window_y:
    :return: The x and y coordinates of the re-roll button, the ROI and the store button.
    """
    re_roll_template = cv2.imread(REROLL_TEMPLATE, 0)
    store_template = cv2.imread(STORE_TEMPLATE, 0)
    screenshot: np.ndarray = np.array(pyautogui.screenshot())
    re_roll_button_loc: tuple = find_template(screenshot, re_roll_template)
    re_roll_button_x: int = re_roll_button_loc[0] + int(re_roll_template.shape[1] / 2)
    re_roll_button_y: int = re_roll_button_loc[1] + int(re_roll_template.shape[0] / 2)
    store_button_loc: tuple = find_template(screenshot, store_template)
    store_button_x: int = store_button_loc[0] + int(store_template.shape[1] / 2)
    store_button_y: int = store_button_loc[1] + int(store_template.shape[0] / 2)
    roi_x: int = window_x + ROI_X_OFFSET
    roi_y: int = window_y + ROI_Y_OFFSET

    return re_roll_button_x, re_roll_button_y, roi_x, roi_y, store_button_x, store_button_y


def extract_roll(roi) -> int | None:
    """
    Function to extract roll value from a region of interest (ROI).
    """
    roll = pytesseract.image_to_string(roi, config=TESSERACT_CONFIG)
    try:
        return int(roll)
    except ValueError:
        logging.warning("Could not convert roll to an integer. Skipping this roll.")
        return None


def debug_screenshot(roi, roll):
    # Print the ROI for debugging
    print("ROI shape: ", roi.shape)
    print("Roll: ", roll)
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

    # Setup the ROI and buttons
    re_roll_button_x, re_roll_button_y, roi_x, roi_y, store_button_x, store_button_y = setup_roi_and_buttons(
        window_x, window_y
    )

    while True:
        # Activate the game window again if it is not active
        if not window.isActive:
            window.activate()
            time.sleep(0.2)

        # Check if the CTRL + SPACE keys are pressed to exit the loop
        if keyboard.is_pressed("ctrl+space"):
            break

        # Click the re-roll button
        pyautogui.click(re_roll_button_x, re_roll_button_y)

        # Capture a screenshot for value extraction
        screenshot: np.ndarray = np.array(pyautogui.screenshot())
        roi: np.ndarray = screenshot[roi_y : roi_y + ROI_HEIGHT, roi_x : roi_x + ROI_WIDTH]

        # Extract roll value
        roll = extract_roll(roi)

        if DEBUG:
            # Show the ROI for debugging
            debug_screenshot(roi, roll)

        if roll is None:
            continue

        logging.info(f"Current max roll: {max_roll}")
        logging.info(f"Current roll: {roll}")

        # If new roll is better, store it
        if roll > max_roll:
            # Update max roll
            max_roll = roll

            logging.info(f"Found a new max roll: {roll}")
            logging.info("Clicking the store button...")

            # Click the store button
            pyautogui.click(store_button_x, store_button_y)

            # Write the new max roll to a file
            with open(MAX_ROLL_FILE, "w") as f:
                logging.info(f"Writing {roll} to max_roll.txt...")
                f.write(str(roll))

            # Sleep for a bit to prevent clicking the re-roll button before the store button is clicked
            time.sleep(0.5)

        # Exit if a good roll is found
        if roll >= 100:
            break


if __name__ == "__main__":
    main()
