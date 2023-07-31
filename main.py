import logging
import sys
import time
from collections import Counter

import cv2
import keyboard
import numpy as np
import pyautogui
import pytesseract

# Constants
ROLLS_FILE = "max_roll.txt"
REROLL_TEMPLATE = "assets/reroll.png"
STORE_TEMPLATE = "assets/store.png"
TESSERACT_CONFIG = "--psm 6 -c tessedit_char_whitelist=0123456789"
ROI_X_OFFSET = 385
ROI_Y_OFFSET = 610
ROI_WIDTH = 40
ROI_HEIGHT = 25
GAME_WINDOW_TITLE = "Baldur's Gate II - Enhanced Edition"

# Setup logging with timestamp, log level and message
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)


def get_game_window():
    """
    Function to find and return the game window.
    """
    window = pyautogui.getWindowsWithTitle(GAME_WINDOW_TITLE)[0]
    if window:
        return window
    else:
        logging.error("Could not find the game window. Exiting...")
        sys.exit()


def load_rolls():
    """
    Function to load previous rolls from a file.
    """
    try:
        with open(ROLLS_FILE, "r") as f:
            return [int(f.read())]
    except FileNotFoundError:
        logging.warning("Could not find max_roll.txt. Starting with an empty list.")
        return []


def find_template(image, template):
    """
    Function to find the location of a template within an image.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    return max_loc


def extract_roll(roi):
    """
    Function to extract roll value from a region of interest (ROI).
    """
    roll = pytesseract.image_to_string(roi, config=TESSERACT_CONFIG)
    try:
        return int(roll)
    except ValueError:
        logging.warning("Could not convert roll to an integer. Skipping this roll.")
        return None


def main():
    """
    Main function to automate the game.
    """
    window = get_game_window()
    rolls = load_rolls()

    window_x, window_y = window.left, window.top

    if not window.isActive:
        window.activate()

    time.sleep(1)

    reroll_template = cv2.imread(REROLL_TEMPLATE, 0)
    store_template = cv2.imread(STORE_TEMPLATE, 0)

    screenshot = np.array(pyautogui.screenshot())

    reroll_button_loc = find_template(screenshot, reroll_template)
    reroll_button_x = reroll_button_loc[0] + int(reroll_template.shape[1] / 2)
    reroll_button_y = reroll_button_loc[1] + int(reroll_template.shape[0] / 2)

    store_button_loc = find_template(screenshot, store_template)
    store_button_x = store_button_loc[0] + int(store_template.shape[1] / 2)
    store_button_y = store_button_loc[1] + int(store_template.shape[0] / 2)

    roi_x = window_x + ROI_X_OFFSET
    roi_y = window_y + ROI_Y_OFFSET

    while True:
        # Check if the CTRL + SPACE keys are pressed to exit the loop
        if keyboard.is_pressed("ctrl+space"):
            break

        # Click the re-roll button
        pyautogui.click(reroll_button_x, reroll_button_y)

        # Capture a screenshot for value extraction
        screenshot = np.array(pyautogui.screenshot())
        roi = screenshot[roi_y : roi_y + ROI_HEIGHT, roi_x : roi_x + ROI_WIDTH]

        # Extract roll value
        roll = extract_roll(roi)
        if roll is None:
            continue

        max_roll = max(rolls) if rolls else roll

        logging.info(f"Current max roll: {max_roll}")
        logging.info(f"Current roll: {roll}")

        # If new roll is better, store it
        if roll > max_roll:
            logging.info(f"Found a new max roll: {roll}")
            logging.info("Clicking the store button...")
            pyautogui.click(store_button_x, store_button_y)
            with open(ROLLS_FILE, "w") as f:
                logging.info(f"Writing {roll} to max_roll.txt...")
                f.write(str(roll))

        rolls.append(roll)
        most_common_roll = Counter(rolls).most_common(1)[0][0]
        logging.info(f"Most common roll: {most_common_roll}")

        # Exit if a good roll is found
        if roll >= 100:
            break


if __name__ == "__main__":
    main()
