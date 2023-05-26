from datetime import datetime
from typing import Optional
import os
import threading
import requests

import pandas as pd
import numpy as np

import cv2
import mediapipe as mp

from gtts import gTTS
from pygame import mixer

from newsapi import NewsApiClient

import docker
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# Constants and global variables
api = NewsApiClient(api_key=os.environ['NEWSAPI_ORG'])
user_profile = os.environ['USERPROFILE']
SEP = os.path.sep
LOGO_URL = "https://raw.githubusercontent.com/codesapienbe/aij-webcam/master/logo.png"
CSV_URL = "https://raw.githubusercontent.com/codesapienbe/aij-webcam/master/news.csv"

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_FPS = 60
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
news_df = Optional[pd.DataFrame]
weather_df = Optional[pd.DataFrame]


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


def get_weather():
    """
    Get the weather from the weatherapi.com API
    """
    api_key = os.environ['WEATHERAPI_COM']
    region = os.environ['WEATHERAPI_COM_REGION']
    response = requests.get(
        f'http://api.weatherapi.com/v1/current.json?key={api_key}&q={region}&aqi=no'
    )
    return response.json()


def get_weather_temp_c(weather):
    """
    Get the temperature in Celsius
    """
    return weather['current']['temp_c']


def get_weather_temp_f(weather):
    """
    Get the temperature in Fahrenheit
    """
    return weather['current']['temp_f']


def get_weather_to_df(weather):
    """
    Convert the weather to a dataframe
    """
    # map all the articles to a list
    current = weather['current']

    # create a dataframe
    df = pd.DataFrame(current, columns=['temp_c', 'temp_f', 'condition', 'wind_mph', 'wind_kph', 'wind_degree', 'wind_dir', 'pressure_mb', 'pressure_in',
                      'precip_mm', 'precip_in', 'humidity', 'cloud', 'feelslike_c', 'feelslike_f', 'vis_km', 'vis_miles', 'uv', 'gust_mph', 'gust_kph'])

    return df


def get_top_headlines():
    """
    Get the top headlines from the newsapi.org API
    """
    response = api.get_top_headlines(
        sources='bbc-news, cnn, fox-news, google-news, the-new-york-times, the-wall-street-journal, the-washington-post, time, usa-today, wired'
    )
    return response


def news_to_df(news):
    """
    Convert the news to a dataframe
    """
    # map all the articles to a list
    articles = list(map(lambda x: x['title'], news['articles']))

    # create a dataframe
    df = pd.DataFrame(articles, columns=['title'])

    # add a column for the length of the title
    df['title_length'] = df['title'].apply(lambda x: len(x))

    # add a column for the number of words in the title
    df['title_words'] = df['title'].apply(lambda x: len(x.split(' ')))

    return df


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


def download_news_csv() -> None:
    """
    Download the news.csv file to userprofile/.aij/news/news.csv
    """
    csv_remote_response = requests.get(
        CSV_URL, allow_redirects=True, stream=True, timeout=10)

    if csv_remote_response.status_code == 200:
        # save the news.csv file if the response is ok and the file does not exist
        if not os.path.exists(csv_abs):
            with open(csv_abs, 'wb') as csv_file:
                csv_file.write(csv_remote_response.content)


def make_directories(paths: list):
    """
    Create directories if not exists
    """
    for path in paths:
        if not os.path.exists(path):
            os.mkdir(path)


# do not wait for the directories to be created
thread_download_logo = threading.Thread(target=download_logo)
thread_download_news_csv = threading.Thread(target=download_news_csv)
thread_download_logo.start()
thread_download_news_csv.start()

# make sure the directories are created before proceeding
thread_download_logo.join()
thread_download_news_csv.join()

make_directories([config_home, image_home, csv_home,
                 audio_home, screenshot_home, video_home])

# if the internet connection is not available then use the local news.csv file
network_status = os.system('ping -n 1 www.google.com')
if network_status == 0:
    # get the top headlines from the newsapi.org API
    news = get_top_headlines()
    # convert the news to a dataframe
    news_df = news_to_df(news)

    # get the weather from the weatherapi.com API
    weather = get_weather()
    # convert the weather to a dataframe
    weather_df = get_weather_to_df(weather)

else:
    news_df = pd.read_csv(csv_abs)
    weather_df = pd.DataFrame()
    weather_df['temp_c'] = [0]
    weather_df['temp_f'] = [0]
    weather_df['condition'] = ['']


titles = news_df['title'].str.cat(sep=' ') + ' ... |'
weather = f"{weather_df['temp_c'][0]}c"

# Using OpenCV to display the image
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, SCREEN_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, SCREEN_FPS)

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

zoomed_text_color = (0, 255, 0)
standard_text_color = (255, 255, 255)
color = standard_text_color

direction = 0
font_size = 12
box_size = 50
is_news_sliding = True
is_news_playing = True


def generate_audio_from_news():
    """
    Convert text to speech and play it
    """
    # initialize tts, create mp3 and play
    tts = gTTS(text=titles, lang='en')

    # save the audio file if not exists
    if not os.path.exists(audio_abs):
        tts.save(audio_abs)

    print(
        f'News: {titles}\n\n'
        f'Generating the audio file: {audio_abs}\n\n'
    )


def play_news_from_audio():
    """
    Play the news
    """
    print(
        f'News: {titles}\n\n'
        f'Playing the audio file: {audio_abs}\n\n'
    )
    mixer.init(
        # high quality audio
        frequency=44100,
        # 16 bits per sample
        size=-16,
        # 2 channels (stereo)
        channels=2,
        # strong buffer to prevent audio stuttering
        buffer=4096 * 2,
    )
    mixer.music.load(audio_abs)
    mixer.music.play()


def pause_news_from_audio():
    """
    Pause the news
    """
    mixer.music.pause()


def stop_news_from_audio():
    """
    Stop the news
    """
    mixer.music.stop()


def resume_news_from_audio():
    """
    Resume the news
    """
    mixer.music.unpause()


def rewind_news_from_audio():
    """
    Rewind the news
    """
    mixer.music.rewind()


def forward_news_from_audio():
    """
    Forward the news
    """
    mixer.music.forward()


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


thread_generate_audio_from_news = threading.Thread(
    target=generate_audio_from_news)
thread_play_news_from_audio = threading.Thread(target=play_news_from_audio)

# make sure the audio file is generated before playing it
thread_generate_audio_from_news.start()
thread_generate_audio_from_news.join()
thread_play_news_from_audio.start()

# For webcam input:
with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.65,
        min_tracking_confidence=0.65) as hands:

    while cap.isOpened():

        success, image = cap.read()

        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        image = cv2.flip(image, 1)

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image)

        # # Draw the hand annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

                # if left hand is raised then move the text to the left
                if hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x < 0.2 and len(results.multi_hand_landmarks) == 1:
                    for i in range(30):
                        # move the text to the left
                        pass
                    direction = 0
                    font_size = 12
                    color = standard_text_color
                    box_size = 50
                    is_news_sliding = True

                # if right hand is raised then move the text to the right
                elif hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x > 0.8 and len(results.multi_hand_landmarks) == 1:
                    for i in range(30):
                        # move the text to the left
                        pass
                    direction = 1
                    font_size = 12
                    color = standard_text_color
                    box_size = 50
                    is_news_sliding = True

                # if both hands are raised and all fingers are up then increase the font size to 36pt and change the color
                elif 0.2 < hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x < 0.8 and len(results.multi_hand_landmarks) == 2 and hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].y and hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].y:
                    for i in range(30):
                        # move the text to the left
                        pass
                    font_size = 36
                    color = zoomed_text_color
                    box_size = 100
                    is_news_sliding = False

                # if both hands are raised and all fingers are closed then stop the news
                if 0.2 < hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x < 0.8 and len(results.multi_hand_landmarks) == 2 and hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].y and hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].y:
                    for i in range(30):
                        # move the text to the left
                        pass
                    # stop sliding the news
                    # stop the news
                    is_news_sliding = False
                    is_news_playing = False
                    direction = 2
                    font_size = 12
                    color = standard_text_color
                    box_size = 50

                # if both hands are raised, thumb and index finger are open then increase the font size to 36pt and change the color
                if 0.2 < hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x < 0.8 and len(results.multi_hand_landmarks) == 2 and hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].y and hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].y and hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].y:
                    # rewind the news
                    direction = 0
                    font_size = 12
                    color = standard_text_color
                    box_size = 50
                    is_news_sliding = True
                    is_news_playing = True

        else:
            # if no hands are detected then move the text to the left
            font_size = 12
            color = standard_text_color
            box_size = 50

        if is_news_playing:
            resume_news_from_audio()
        else:
            pause_news_from_audio()

        if is_news_sliding and direction == 0:
            titles = titles[1:] + titles[0]
        elif is_news_sliding and direction == 1:
            titles = titles[-1] + titles[:-1]
        elif direction == 2:
            pass

        # draw the text
        draw_text(image, 2, image.shape[0] - 10, titles, color)

        # draw the weather on the image if the weather is available
        if weather_df['temp_c'][0] != 0:
            # set the position of the weather to the right top corner
            draw_text(image, image.shape[1] - 250, 30, weather, color)

        # if there is a logo then draw it
        if os.path.exists(logo_abs):
            logo = cv2.imread(logo_abs)
            # Resize the logo to match the height of the main image and keep the aspect ratio
            # resize the logo to 100px height and keep the aspect ratio
            logo_resized = cv2.resize(
                logo, (100, 100), interpolation=cv2.INTER_AREA)
            # get the height and width of the logo
            logo_height, logo_width, _ = logo_resized.shape
            # get the height and width of the main image
            image_height, image_width, _ = image.shape
            # calculate the x and y coordinates of the logo
            x = image_width - logo_width - 10
            y = image_height - logo_height - 30
            # draw the logo on the main image
            image[y:y + logo_height, x:x + logo_width] = logo_resized
        else:
            draw_text(image, 0, 20, 'AIJ', color)

        cv2.imshow('AI News', image)

        # wait for the 'q' key to be pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # if 's' is pressed, save the image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        screenshot_abs = screenshot_home + SEP + timestamp + '.png'
        if cv2.waitKey(1) & 0xFF == ord('s'):
            cv2.imwrite(screenshot_abs, image)


# stop the thread that plays the news
thread_play_news_from_audio.join()

# Release the webcam
cap.release()
# Destroy all windows
cv2.destroyAllWindows()
