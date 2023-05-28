from sys import argv
import cv2
import mediapipe as mp
from math import hypot
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import numpy as np

# If there is an argument in the command line pass it to the function set DEBUG to False
DEBUG = argv[1] == "--debug" if len(argv) > 1 else False

cap = cv2.VideoCapture(0)  # Checks for camera
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Sets the width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Sets the height
cap.set(cv2.CAP_PROP_FPS, 30)  # Sets the fps

mp_hands = mp.solutions.hands  # detects hand/finger
hands = mp_hands.Hands()  # complete the initialization configuration of hands
mpDraw = mp.solutions.drawing_utils

# To access speaker through the library pycaw
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volbar = 400
volper = 0

# volume range
volMin, volMax = volume.GetVolumeRange()[:2]

# while the capture device is open run the loop
while cap.isOpened():

    success, frame = cap.read()  # If camera works capture an image
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
    # flip the image
    frame = cv2.flip(frame, 1)

    # Collection of gesture information
    results = hands.process(frame)  # completes the image processing.

    lmList = []  # empty list
    if results.multi_hand_landmarks:  # list of all hands detected.
        
        # By accessing the list, we can get the information of each hand's corresponding flag bit
        for hand_landmarks in results.multi_hand_landmarks:
            
            # adding counter and returning it
            for id, lm in enumerate(hand_landmarks.landmark):
                # Get finger joint points
                h, w, _ = frame.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                # adding to the empty list 'lmList'
                lmList.append([id, cx, cy])
            
            if DEBUG:
                print(lmList)        
                mpDraw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    if lmList != []:
        
        # if the index finger and middle finger are in the middle left of the screen
        # increase the volume
        # getting the value at a point as x, y
        x1, y1 = lmList[4][1], lmList[4][2]  # thumb
        x2, y2 = lmList[8][1], lmList[8][2]  # index finger

        if x1 < frame.shape[1] // 2 and x2 < frame.shape[1] // 2 and y1 < frame.shape[0] // 2 and y2 < frame.shape[0] // 2:

            # creating circle at the tips of thumb and index finger
            # image #fingers #radius #rgb
            cv2.circle(frame, (x1, y1), 13, (255, 0, 0), cv2.FILLED)
            # image #fingers #radius #rgb
            cv2.circle(frame, (x2, y2), 13, (255, 0, 0), cv2.FILLED)
            # create a line b/w tips of index finger and thumb
            cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

            length = hypot(x2 - x1, y2 - y1)  
            # distance b/w tips using hypotenuse
            # from numpy we find our length by converting hand range in terms of volume range ie b/w -63.5 to 0
            vol = np.interp(length, [30, 350], [volMin, volMax])
            volbar = np.interp(length, [30, 350], [400, 150])
            volper = np.interp(length, [30, 350], [0, 100])

            volume.SetMasterVolumeLevel(vol, None)

    # Hand range 30 - 350
    # Volume range -63.5 - 0.0
    # creating volume bar for volume level
    # vid ,initial position ,ending position ,rgb ,thickness
    cv2.rectangle(frame, (50, 150), (85, 400), (0, 0, 255), 4)
    cv2.rectangle(frame, (50, int(volbar)), (85, 400),
                (0, 0, 255), cv2.FILLED)
    cv2.putText(frame, f"{int(volper)}%", (10, 40),
                cv2.FONT_ITALIC, 1, (0, 255, 98), 3)
    # tell the volume percentage ,location,font of text,length,rgb color,thickness

    cv2.imshow('Image', frame)  # Show the video
    if cv2.waitKey(1) & 0xff == ord('q'):  # By using spacebar delay will stop
        break

cap.release()  # stop cam
cv2.destroyAllWindows()  # close window
