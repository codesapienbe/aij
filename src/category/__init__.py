import cv2
from cvzone.HandTrackingModule import HandDetector
from pynput.keyboard import Controller
from screeninfo import get_monitors


class Label:
    def __init__(self, x, y, w, h, v, s):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.v = v
        self.s = s

    def draw(self, img):
        cv2.putText(img, self.v, (self.x + 25, self.y + 40),
                    cv2.FONT_HERSHEY_PLAIN, self.s, (255, 255, 255), self.s)

    def resize(self, w, h, img):
        cv2.putText(img, self.v, (self.x + w, self.y + h),
                    cv2.FONT_HERSHEY_PLAIN, self.s, (255, 255, 255), self.s)

    def color(self, rgb, img):
        cv2.putText(img, self.v, (self.x + 25, self.y + 40),
                    cv2.FONT_HERSHEY_PLAIN, self.s, rgb, self.s)

    def text(self, value, img):
        cv2.putText(img, value, (self.x + 25, self.y + 40),
                    cv2.FONT_HERSHEY_PLAIN, self.s, (255, 255, 255), self.s)

    def shrink(self, value, limit, img):
        cv2.putText(img, (self.v[:limit + 1][-1] + value), (self.x + 25, self.y + 50), cv2.FONT_HERSHEY_PLAIN, 2,
                    (255, 255, 255),
                    2)


class Rectangle:

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, img):
        self.background((255, 255, 255), img)
        self.border((255, 255, 255), img)

    def background(self, rgb, img):
        cv2.rectangle(img, (self.x, self.y), (self.x + self.w,
                    self.y + self.h), rgb, cv2.FILLED)

    def border(self, rgb, img):
        cv2.rectangle(img, (self.x, self.y),
                    (self.x + self.w, self.y + self.h), rgb, 3)


class Button:

    def __init__(self, pos, width, height, value):
        self.pos = pos
        self.width = width
        self.height = height
        self.value = value

    def click(self, img, x, y):
        if self.pos[0] < x < self.pos[0] + self.width and self.pos[1] < y < self.pos[1] + self.height:
            self.border((255, 255, 255), img)
            self.text(self.value, img)
            return True

        else:
            return False

    def draw(self, img):
        self.border((255, 255, 255), img)
        self.text(self.value, img)

    def background(self, rgb, img):
        # for the background calculator
        cv2.rectangle(
            img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height), rgb, cv2.FILLED)

    def border(self, rgb, img):
        # for the border calculator
        cv2.rectangle(
            img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height), rgb, 3)

    def text(self, value, img):
        self.value = value
        cv2.putText(img, self.value, (self.pos[0] + 25, self.pos[1] + 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255),
                    3)

    def text_hover(self, value, img):
        self.value = value
        cv2.putText(img, self.value, (self.pos[0] + 25, self.pos[1] + 50), cv2.FONT_HERSHEY_PLAIN, 6, (255, 255, 255),
                    3)

    def move(self, pos, img):
        self.pos = pos
        self.border((255, 255, 255), img)
        self.text(self.value, img)


def main():
    primary_monitor = {}
    for m in get_monitors():
        print("Connected monitors {}".format(m))
        if m.is_primary:
            primary_monitor = m
            break

    cap = cv2.VideoCapture(0)
    cap.set(3, primary_monitor.width)
    cap.set(4, primary_monitor.height)

    button_values = [
        ["Q", "A", "Z", "1"],
        ["W", "S", "X", "2"],
        ["E", "D", "C", "3"],
        ["R", "F", "V", "4"],
        ["T", "G", "B", "5"],
        ["Y", "H", "N", "6"],
        ["U", "J", "M", "7"],
        ["I", "K", ",", "8"],
        ["O", "L", ".", "9"],
        ["P", ";", "/", "0"],
    ]

    button_values_vertical = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]
    ]

    keyboard = Controller()

    detector = HandDetector(detectionCon=0.8, maxHands=1)
    button_components = []

    for x in range(10):
        for y in range(4):
            pos_x = x * 70 + 350  # starting from 350 pixel in the width
            pos_y = y * 70 + 100  # starting from 100 pixel in the height
            button_components.append(
                Button((pos_x, pos_y), 70, 70, button_values[x][y]))
        # to store the whole equation from the calculator
        global equation
        equation = ""
    # to avoid duplicated value inside calculator in event writing
    delay_counter = 0

    while cap.isOpened():
        success, img = cap.read()
        img = cv2.flip(img, 1)
        # detection hand
        hand, img = detector.findHands(img, flipType=False)

        cv2.rectangle(img, (350, 30), (350 + 280, 100), (255, 255, 255), 2)

        equation_label = Label(350, 40, 200, 40, equation, 3)
        equation_label.draw(img)

        for button in button_components:
            button.draw(img)

        if len(hand) == 1:
            landmarks = hand[0]["lmList"]
            distance, _, img = detector.findDistance(
                landmarks[8][:2], landmarks[12][:2], img)
            x, y = landmarks[8][:2]

            if distance < 70:
                for button in button_components:
                    if button.click(img, x, y) and delay_counter == 0:
                        button.background((255, 255, 255), img)
                        keyboard.press(button.value)
                        equation += button.value
                        delay_counter = 1

        # avoid duplicates
        if delay_counter != 0:
            delay_counter += 1
            # i did not add value into display calculator
            # after passing 10 frames
            if delay_counter > 10:
                delay_counter = 0

        cv2.imshow("image", img)

        key = cv2.waitKey(1)
        if (key == ord("c")):  # to clear the display calculator
            equation = ""
        if key == ord('q'):  # to stop the program
            cv2.destroyAllWindows()
            cap.release()
            exit(-1)


if __name__ == "__main__":
    main()
