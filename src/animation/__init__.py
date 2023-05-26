import os
import random
import numpy as np
import cv2

import docker

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class Animation:
    """
    This class generates an animation of random shapes on a canvas.
    The animation is displayed in a window and then a text message is added to the last frame.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.shapes = [cv2.circle, cv2.rectangle, cv2.ellipse]
        self.texts = []

    def generate_rectangle(self, pt1=None, pt2=None, color=None, thickness=1):
        """
        This method generates a random rectangle and returns its arguments.
        """
        if pt1 is None:
            pt1 = (random.randint(0, self.width),
                random.randint(0, self.height))

        if pt2 is None:
            pt2 = (random.randint(0, self.width),
                random.randint(0, self.height))

        if color is None:
            color = (random.randint(0, 255), random.randint(
                0, 255), random.randint(0, 255))

        if thickness is None:
            thickness = random.randint(1, 5)

        return pt1, pt2, color, thickness

    def generate_ellipse(self):
        """
        This method generates a random ellipse and returns its arguments.
        """
        center = (random.randint(0, self.width),
                random.randint(0, self.height))
        axes = (random.randint(10, 50), random.randint(10, 50))
        angle = random.randint(0, 360)
        start_angle = random.randint(0, 360)
        end_angle = random.randint(0, 360)
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        thickness = random.randint(1, 5)
        return center, axes, angle, start_angle, end_angle, color, thickness

    def generate_text(self, text: str):
        """
        This method generates a random text message and returns its arguments.
        """
        org = (random.randint(0, self.width),
            random.randint(0, self.height))
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = random.uniform(1, 4)
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        thickness = random.randint(1, 5)
        return text, org, font, font_scale, color, thickness

    def generate_circle(self):
        """
        This method generates a random circle and returns its arguments.
        """
        center = (random.randint(0, self.width),
                random.randint(0, self.height))
        radius = random.randint(10, 50)
        color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        thickness = random.randint(1, 5)
        return center, radius, color, thickness

    def generate_shape(self):
        """
        This method generates a random shape and returns the shape and its arguments.
        """
        shape = random.choice(self.shapes)
        if shape == cv2.circle:
            return shape, self.generate_circle()
        elif shape == cv2.rectangle:
            return shape, self.generate_rectangle()
        elif shape == cv2.ellipse:
            return shape, self.generate_ellipse()

    def generate_animation(self, num_frames: int, text: str):
        """
        This method generates an animation of random shapes on a canvas.
        """
        for _ in range(num_frames):
            shape, args = self.generate_shape()
            shape(self.canvas, *args)
            cv2.imshow('Animation', self.canvas)
            cv2.waitKey(1)

        # clear canvas before adding the text message
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # generate the sliding text animation
        for _ in range(100):
            self.canvas = np.roll(self.canvas, 10, axis=0)
            self.canvas = np.roll(self.canvas, 10, axis=1)
            cv2.putText(self.canvas, *self.generate_text(text), cv2.LINE_AA)
            cv2.imshow('Animation', self.canvas)
            cv2.waitKey(1)

        # create disappearing text animation by adding boxes as black rectangles
        for _ in range(100):
            # draw a rectangle at a random coordinate on the canvas
            # and add it to the list of rectangles
            cv2.rectangle(self.canvas, *self.generate_rectangle(
                pt1=(random.randint(0, self.width),
                    random.randint(0, self.height)),
                color=(0, 0, 0), thickness=-1
            ))
            cv2.waitKey(1)

        cv2.imshow('Animation', self.canvas)
        cv2.waitKey(0)

    def destroy_animation(self):
        """
        This method destroys the animation window.
        """
        cv2.destroyAllWindows()
        
        
def main():
    
    # generate random news headlines and place them randomly on the canvas
    tech_news = """Last week, the US government announced that it would ban the use of TikTok and WeChat in the country.
    The ban will take effect on September 20, 2020.
    Twitter has announced that it will ban political ads on its platform.
    Facebook has announced that it will ban political ads on its platform.
    Google has announced that it will ban political ads on its platform.
    TikTok has now been banned in India.
    The US government has banned TikTok and WeChat in the country."""
    
    animation = Animation(800, 600)
    animation.generate_animation(50, random.choice(tech_news.split('\n')))
    animation.destroy_animation()
    
if __name__ == '__main__':
    main()