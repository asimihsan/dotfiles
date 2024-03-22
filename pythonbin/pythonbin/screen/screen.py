import vendor

import pyautogui


def main() -> None:
    # Get the screen size
    screen_width, screen_height = pyautogui.size()
    print(f"Screen width: {screen_width}, Screen height: {screen_height}")

    # Set up a 2.5 second pause after each PyAutoGUI call.
    pyautogui.PAUSE = 2.5

    # pyautogui.screenshot('/tmp/screenshot.png')

    location = pyautogui.locateOnScreen('img_1.png', grayscale=True, confidence=0.3)
    print(location)
    pyautogui.moveTo(location, duration=1.0)

if __name__ == "__main__":
    main()
