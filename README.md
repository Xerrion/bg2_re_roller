Sure, here's a sample `README.md` for your project:

---

# Auto Clicker for Baldur's Gate II

This project is an automated script for the Baldur's Gate II game. The script automates the process of re-rolling character stats to get the maximum possible roll. It uses various libraries such as `pyautogui` for GUI automation, `cv2` for image processing, and `pytesseract` for optical character recognition.

## Dependencies

The script requires the following Python libraries:

- `pyautogui`
- `cv2`
- `numpy`
- `pytesseract`
- `keyboard`
- `collections`
- `logging`

You can install these dependencies using pip:

```bash
pip install pyautogui opencv-python numpy pytesseract keyboard
```

## How to Run

You can run the script from the command line using Python:

```bash
python main.py
```

Make sure that the game window is open and visible on the screen before running the script.

## How It Works

The script works by taking screenshots of the game window and identifying the "Reroll" and "Store" buttons using a template image. It continuously clicks the "Reroll" button and uses OCR to read the roll value from a specified region of the screen. If the roll is higher than any previous roll, it clicks the "Store" button and saves the new high roll to a file.

You can stop the script at any time by pressing "CTRL + SPACE".

## Configuration

You can configure various aspects of the script by modifying the constants at the top of the `main.py` file. For example, you can change the game window title, the file paths for the button template images, the region of the screen from which to read the roll value, etc.
