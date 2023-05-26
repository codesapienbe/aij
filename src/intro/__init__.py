import cv2
import os
import random
import numpy as np
import threading
from pygame import mixer

# import ffmpeg and extract audio from the video
import ffmpeg

user_profile = os.environ['USERPROFILE']
SEP = os.path.sep

class AnimationThread(threading.Thread):
    """
    This class represents a thread that generates an animation video
    """

    def __init__(self):
        """
        This method is called when the object is created
        """
        threading.Thread.__init__(self)
        # Path to the album directory containing all the images
        self.album_path = user_profile + SEP + '.aij' + SEP + 'image' + SEP + 'intro'
        self.audio_path = user_profile + SEP + '.aij' + SEP + 'audio'
        self.audio_intro_abs = self.audio_path + SEP + 'intro.mp3'
        self.audio_next_abs = self.audio_path + SEP + 'next.mp3'
        self.news_path = user_profile + SEP + '.aij' + SEP + 'news'

        # Load all the images
        self.images = []
        for file in os.listdir(self.album_path):
            if file.endswith('.jpg') or file.endswith('.png') or file.endswith('.jpeg'):
                img = cv2.imread(os.path.join(self.album_path, file))
                self.images.append(img)

        mixer.init()

        # Load the audio with name 'intro.mp3'
        self.audio_intro = mixer.Sound(self.audio_intro_abs)
        self.audio_next = mixer.Sound(self.audio_next_abs)

        self.audio_intro.set_volume(0.7)
        self.audio_next.set_volume(0.7)

        # Load the news
        self.news = []

        # Shuffle the images
        random.shuffle(self.images)

        # Define the animation parameters
        self.animation_width = 1920
        self.animation_height = 1080
        self.fps = 60
        self.duration = 10  # in seconds

        # Create the video writer object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter('animation.mp4', fourcc, self.fps,
                                            (self.animation_width, self.animation_height))

    def run(self):
        """
        This method is called when the thread is started
        @param: None
        @return: None
        """
        # Define the initial position of the first image
        x = 0
        y = 0

        # Generate the animation frames
        num_frames = self.fps * self.duration
        for i in range(num_frames):
            # Create a blank frame
            frame = np.zeros(
                (self.animation_height, self.animation_width, 3), dtype=np.uint8)

            # Choose a random image and resize it to 1920x1080 pixels (Full HD).
            # Make sure the aspect ratio is maintained while resizing
            img = self.images[i % len(self.images)]
            img = cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_AREA)

            # Update the image position
            x += random.randint(-50, 50)
            y += random.randint(-50, 50)
            x = max(0, min(x, self.animation_width - img.shape[1]))
            y = max(0, min(y, self.animation_height - img.shape[0]))

            # Check if the image dimensions exceed the frame dimensions
            if img.shape[0] > self.animation_height:
                img = img[:self.animation_height, :, :]
            if img.shape[1] > self.animation_width:
                img = img[:, :self.animation_width, :]

            # Draw the image on the frame
            img_height, img_width, _ = img.shape
            frame[y:y + img_height, x:x + img_width] = img

            # Write the frame to the video writer
            self.video_writer.write(frame)

        # Release the video writer
        self.video_writer.release()

        
        ffmpeg.input('animation.mp4').output('animation_with_audio.mp4').run()

        # Print the path of the animation video
        print('Animation video generated at ' + os.path.abspath('animation_with_audio.mp4'))


def main():
    """
    This function is the entry point of the program
    @param: None
    @return: None
    """
    # Create and start the animation thread
    animation_thread = AnimationThread()
    animation_thread.start()

    # Do some other work here
    print('Doing some other work here...')

    # Wait for the animation thread to finish
    animation_thread.join()

    # Destroy all windows
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
