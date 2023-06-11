from datetime import datetime
from glob import glob
import os
import sys
from typing import Optional
import threading
from deepface.basemodels.SFace import cv
import requests
from deepface import DeepFace
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2
import docker

user_profile = os.environ['USERPROFILE']
SEP = os.path.sep
LOGO_URL = "https://raw.githubusercontent.com/codesapienbe/aij-webcam/master/logo.png"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_FPS = 30
SCREEN_START_X = 0
SCREEN_START_Y = 0
SCREEN_MAXIMIZE = True
APP_TITLE = 'AIJ'

start = datetime.now().strftime("%Y%m%d%H%M%S")
start_dt = datetime.now()
config_home = user_profile + SEP + '.aij'
config_abs = config_home + SEP + 'config.json'
image_home = user_profile + SEP + '.aij' + SEP + 'image'
logo_abs = image_home + SEP + 'logo.png'
csv_home = user_profile + SEP + '.aij' + SEP + 'news'
csv_abs = csv_home + SEP + 'news.csv'
audio_home = user_profile + SEP + '.aij' + SEP + 'audio'
screenshot_home = user_profile + SEP + '.aij' + SEP + 'screenshot'
audio_abs = audio_home + SEP + start + '.mp3'
video_home = user_profile + SEP + '.aij' + SEP + 'video'
face_home = user_profile + SEP + '.aij' + SEP + 'face'
news_df = Optional[pd.DataFrame]
weather_df = Optional[pd.DataFrame]

backends = [
    "opencv",
    "ssd",
    "dlib",
    "mtcnn",
    "retinaface",
    "mediapipe"
]

default_backend = backends[0]

models = [
    "VGG-Face",
    "Facenet",
    "Facenet512",
    "OpenFace",
    "DeepFace",
    "DeepID",
    "ArcFace",
    "Dlib",
    "SFace",
]

default_model = models[0]


def pre_init():
    """
    This function is called before the server is initialized
    """

    client = docker.from_env()
    # print all containers
    containers = client.containers.list()

    for container in containers:
        print(
            container.name,
            container.id,
            container.status
        )

    # if there is no docker container running named aij-messaging-server then run the server script 'aijinit'

    if not any(container.name == 'aij-messaging-server' for container in containers):
        os.system('aijinit')


def download_logo():
    """
    Download the logo.png file to userprofile/.aij/images/logo.png
    """

    logo_remote_response = requests.get(
        LOGO_URL, allow_redirects=True, stream=True, timeout=10)

    if logo_remote_response.status_code == 200:
        # save the logo.png file if the response is ok and the file does not exist
        if not os.path.exists(logo_abs):
            with open(logo_abs, 'wb') as logo_file:
                logo_file.write(logo_remote_response.content)


def draw_text(image, x, y, text, color):
    """
    Draw text on the image
    """

    # draw a black rectangle on the image

    cv2.rectangle(
        image,
        (x, y - 25),
        # until the end of screen width
        (x + image.shape[1], y),
        (0, 0, 0),
        -1
    )

    # draw the text on the image
    cv2.putText(
        image,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_size / 12,
        color,
        2,
        cv2.LINE_AA
    )


def draw_box(image, x, y, color):
    """
    Draw a box on the image
    """
    cv2.rectangle(
        image,
        (x, y),
        (x + box_size, y + box_size),
        color,
        2
    )


def draw_button(image, x, y, text, color):
    """
    Draw a button on the image and write text on it
    """

    cv2.rectangle(
        image,
        (x, y),
        (x + box_size, y + box_size),
        color,
        2
    )

    cv2.putText(
        image,
        text,
        (x + 5, y + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_size,
        color,
        2,
        cv2.LINE_AA
    )


def draw_zoomed_text(image, x, y, text, color):
    """
    Draw zoomed text on the image
    """
    cv2.putText(
        image,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_size,
        color,
        2,
        cv2.LINE_AA
    )


def draw_logo(logo_path, img):
    if os.path.exists(logo_path):
        logo = cv2.imread(logo_path)
        # Resize the logo to match the height of the main image and keep the aspect ratio
        # resize the logo to 100px height and keep the aspect ratio
        logo_resized = cv2.resize(
            logo, (48, 48), interpolation=cv2.INTER_AREA)
        # get the height and width of the logo
        logo_height, logo_width, _ = logo_resized.shape
        # calculate the x and y coordinates of the logo
        x = 5
        y = 5
        # draw the logo on the main image
        img[y:y + logo_height, x:x + logo_width] = logo_resized
        return img


def draw_emoji(current_emotion, img):
    emoji_home = user_profile + SEP + '.aij' + SEP + 'emojis'

    # find all emojis
    matching_emoji = [emoji for emoji in os.listdir(emoji_home) if emoji.endswith(
        ".png") and emoji.startswith(current_emotion)]
    emj = cv2.imread(emoji_home + SEP + matching_emoji[0])

    # resize the emj to 64px height and keep the aspect ratio
    emj_resized = cv2.resize(emj, (64, 64), interpolation=cv2.INTER_AREA)

    # get the height and width of the emj
    emj_height, emj_width, _ = emj_resized.shape
    # get the height and width of the main image
    image_height, image_width, _ = img.shape
    # calculate the x and y coordinates of the emj
    x = image_width - emj_width - 5
    y = image_height - emj_height - 5
    # draw the emj on the main image
    img[y:y + emj_height, x:x + emj_width] = emj_resized
    return img


def main():

    # do not wait for the directories to be created
    thread_download_logo = threading.Thread(target=download_logo)
    thread_download_logo.start()

    default_backend = "opencv"
    default_model = "VGG-Face"

    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, SCREEN_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT)
    cam.set(cv2.CAP_PROP_FPS, SCREEN_FPS)

    # Define min window size to be recognized as a face
    MIN_FACE_FRAME_WIDTH = 50
    MIN_FACE_FRAME_HEIGHT = 50
    FRAME_COUNTER = 0
    current_emotion = "neutral"

    while cam.isOpened():

        ret, img = cam.read()
        img = cv2.flip(img, 1)  # Flip vertically
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # increase the frame counter
        FRAME_COUNTER += 1

        try:
            # after each 5 seconds detect faces
            if FRAME_COUNTER >= SCREEN_FPS:
                # reset the frame counter
                FRAME_COUNTER = 0
                # predict the emotion
                emotion = DeepFace.analyze(img_path=img, actions=[
                    'emotion'], detector_backend=default_backend, align=True, silent=True)

                # get the emotion data from the dictionary
                emotion_data = emotion[0]['emotion']
                # convert to dataframe
                emotion_df = pd.DataFrame(emotion_data, index=[0])
                # get the dominant emotion
                emotion_label = emotion_df.idxmax(axis=1)[0]
                # add the emotion to the emotion history
                current_emotion = emotion_label

        except Exception as e:
            # draw error message if no face detected
            pass

        img = draw_emoji(current_emotion, img)
        img = draw_logo(logo_abs, img)

        cv2.imshow('Emotion Recognition', img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cam.release()
            break

    if cam.isOpened():
        cam.release()

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
