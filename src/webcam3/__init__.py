import cv2
from cvzone.HandTrackingModule import HandDetector
from nltk import decorator
from pynput.keyboard import Controller
from screeninfo import get_monitors

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


class Keyboard():
    """
    Keyboard class: contains the keys and values, draws them
    """
    
    KEYBOARD_START_POS = (60, 20)
    KEYBOARD_KEY_SIZE = (80, 70)
    
    def __init__(self, pos = KEYBOARD_START_POS, size = KEYBOARD_KEY_SIZE):
        
        self.controller = Controller()    
        self.visible = True
        self.physical = True
        self.pos = pos
        self.size = size
        
        self.keys = [
            ["a", "o", "1"],
            ["b", "p", "2"],
            ["c", "r", "3"],
            ["d", "s", "4"],
            ["e", "t", "5"],
            ["f", "u", "6"],
            ["g", "v", "7"],
            ["h", "w", "8"],
            ["i", "x", "9"],
            ["j", "y", "0"],
            ["l", "z", "."],
            ["m", "/", ","],
        ]
        
        self.values = []
        
        self.current = ""
        self.prev = ""
        self.next = ""
        
        self.fill()
        
    def is_visible(self):
        return self.visible
    
    def is_physical(self):
        return self.physical
    
    def set_visible(self, visible):
        self.visible = visible
    
    def set_physical(self, physical):
        self.physical = physical
        
    def fill(self):
    
        button_components = []
        
        # assign the buttons to the keyboard
        # length of the first array refers to the number of rows
        # length of the second array refers to the number of columns
        rows = len(self.keys)
        cols = len(self.keys[0])
        for x in range(rows):
            for y in range(cols):
                pos_x = x * self.size[0] + self.pos[0]
                pos_y = y * self.size[1] + 100 + self.pos[1]
                button_components.append(
                    Button(
                        (pos_x, pos_y), self.size[0], self.size[1], self.keys[x][y]
                    )
                )
                
                
        self.values = button_components
        
    def clear(self):
        self.values = []
        self.current = ""
        self.prev = ""
        self.next = ""
        
    def move(self, pos):
        self.pos = pos
        
    def resize(self, size):
        self.size = size
        

class NewsAPISearch():
    """
    This class provides functions to search for news
    @param: query
    @return: Search results as a list
    """
    def __init__(self, query):
        self.query = query
    

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


zoomed_text_color = (0, 255, 0)
standard_text_color = (255, 255, 255)
color = standard_text_color

direction = 0
font_size = 12
box_size = 50
is_news_sliding = True
is_news_playing = True


MAX_NUMBER_OF_HANDS_TO_DETECT = 2

def generate_loading_animation(img):
    """
    Generate the loading animation with an overlay on the image
    """
    overlay = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)
    
    cv2.rectangle(
        overlay,
        (0, 0),
        (img.shape[1], img.shape[0]),
        (0, 0, 0),
        -1
    )
    
    img = cv2.addWeighted(overlay, 0.5, img, 0.5, 0)
    return img

def main():
        
    # do not wait for the directories to be created
    thread_download_logo = threading.Thread(target=download_logo)
    thread_download_news_csv = threading.Thread(target=download_news_csv)
    thread_download_logo.start()
    thread_download_news_csv.start()
    
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

    # initialize the video capture
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, SCREEN_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, SCREEN_FPS)

    # get the top headlines from the newsapi.org API
    titles = news_df['title'].str.cat(sep=' ') + ' ... |'
    weather = f"{weather_df['temp_c'][0]}c"
    
    keyboard = Keyboard()

    # initialize the hand detector
    detector = HandDetector(detectionCon=0.8, maxHands=MAX_NUMBER_OF_HANDS_TO_DETECT)
            
    # to avoid duplicated value inside keyboard in event writing
    delay_counter = 0

    while cap.isOpened():

        _, img = cap.read()
        img = cv2.flip(img, 1)
        # detection hand
        hand, img = detector.findHands(img, flipType=False)

        cv2.rectangle(img, (350, 30), (350 + 280, 100), (255, 255, 255), 2)

        equation_label = Label(350, 40, 400, 40, keyboard.current, 3)
        equation_label.draw(img)

        for button in keyboard.values:
            button.draw(img)

        if len(hand) == 1:
            
            landmarks = hand[0]["lmList"]
            distance, _, img = detector.findDistance(
                landmarks[8][:2], landmarks[12][:2], img)
            x, y = landmarks[8][:2]

            if distance < 70:
                for button in keyboard.values:
                    if button.click(img, x, y) and delay_counter == 0:
                        button.background((255, 255, 255), img)
                        # keyboard.press(button.value)
                        keyboard.current += button.value
                        delay_counter = 1

        elif len(hand) == 2:
            # if one hand is open and the other is closed then write with the opened hand
            left_hand = hand[0]["lmList"]
            right_hand = hand[1]["lmList"]
            
            lh = left_hand[8][1] < left_hand[9][1]
            rh = right_hand[8][1] < right_hand[9][1]
            
            if lh and not rh:
                distance, _, img = detector.findDistance(
                left_hand[8][:2], left_hand[12][:2], img)
                x, y = left_hand[8][:2]

                if distance < 70:
                    for button in keyboard.values:
                        if button.click(img, x, y) and delay_counter == 0:
                            button.background((255, 255, 255), img)
                            # keyboard.press(button.value)
                            keyboard.current += button.value
                            delay_counter = 1
                            
            elif rh and not lh:
                distance, _, img = detector.findDistance(
                right_hand[8][:2], right_hand[12][:2], img)
                x, y = right_hand[8][:2]
                
                if distance < 70:
                    for button in keyboard.values:
                        if button.click(img, x, y) and delay_counter == 0:
                            button.background((255, 255, 255), img)
                            # keyboard.press(button.value)
                            keyboard.current += button.value
                            delay_counter = 1
                            
            # if both hands are closed then make the keyboard invisible
            elif lh and rh:
                keyboard.visible = False
                img = generate_loading_animation(img)
                delay_counter = 1
            
            # if both hands are opened then show the keyboard
            elif not lh and not rh:
                keyboard.visible = True
                delay_counter = 1
            
        # avoid duplicates
        if delay_counter != 0:
            delay_counter += 1
            # i did not add value into display calculator
            # after passing 10 frames
            if delay_counter > 10:
                delay_counter = 0

        if keyboard.is_visible():
            keyboard.fill()
        else:
            keyboard.clear()

        if is_news_sliding and direction == 0:
            titles = titles[1:] + titles[0]
        elif is_news_sliding and direction == 1:
            titles = titles[-1] + titles[:-1]
        elif direction == 2:
            pass

        # draw the text
        draw_text(img, 2, img.shape[0] - 10, titles, color)

        # draw the weather on the image if the weather is available
        if weather_df['temp_c'][0] != 0:
            # set the position of the weather to the right top corner
            draw_text(img, img.shape[1] - 250, 30, weather, color)

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
            image_height, image_width, _ = img.shape
            # calculate the x and y coordinates of the logo
            x = image_width - logo_width - 10
            y = image_height - logo_height - 30
            # draw the logo on the main image
            img[y:y + logo_height, x:x + logo_width] = logo_resized
        else:
            draw_text(img, 0, 20, 'AIJ', color)

        cv2.imshow("image", img)

        # wait for escape key
        key = cv2.waitKey(1)
        
        # if the key is escape then break
        if key == 27:
            break

    cv2.destroyAllWindows()
    cap.release()
    
    # kill all threads
    thread_download_logo.join()
    thread_download_news_csv.join()


if __name__ == "__main__":
    main()
