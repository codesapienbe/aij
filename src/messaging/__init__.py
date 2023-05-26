# using Kivy to create a GUI for the publisher and subscriber
import os
import time
from threading import Thread
import pika

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from dotenv import load_dotenv
import docker

load_dotenv()  # take environment variables from .env.


class AIJMessagingServer(App):
    """
    A class to create a GUI for the publisher and subscriber
    """

    def build(self):
        """
        Build the GUI for starting RabbitMQ with only one button and a label
        """
        self.title = 'AIJ News'
        self.icon = 'logo.png'

        # create a layout for the publisher
        self.publisher_layout = BoxLayout(orientation='vertical', padding=10)

        # create a label for the publisher
        self.publisher_label = Label(
            text='RabbitMQ Messaging Server', size_hint=(1, 0.90))

        # create a button for the publisher
        self.publisher_button = Button(text='Start', size_hint=(1, 0.10))

        # change the background color of the button to red
        self.publisher_button.background_color = (1, 0, 0, 1)

        # add the label, text input and button to the publisher layout
        self.publisher_layout.add_widget(self.publisher_label)
        self.publisher_layout.add_widget(self.publisher_button)

        # bind the button click event to the start method
        self.publisher_button.bind(on_press=self.start)

        return self.publisher_layout

    def set_button_bg(self, rgb, *args):
        """
        The method to change the background color of the button
        """
        # change the background color of the button to red
        self.publisher_button.background_color = rgb

    def start(self, instance):
        """
        Initialize the RabbitMQ server
        """
        client = docker.from_env()
        # docker run -d --hostname my-rabbit --name some-rabbit rabbitmq:3
        client.containers.run(
            "rabbitmq:3", 
            name='aij-messaging-server',
            hostname='aij-messaging-server',
            ports={'5672/tcp': 5672},
            environment={'RABBITMQ_DEFAULT_USER': 'admin', 'RABBITMQ_DEFAULT_PASS': 'admin'},
            volumes={
                
            },
            detach=True
        )

        # print all containers
        containers = client.containers.list()

        for container in containers:
            print(
                container.name,
                container.id,
                container.status
            )

        # change the text of the button to 'Stop'
        self.publisher_button.text = 'Stop'

        # bind the button click event to the stop method
        self.publisher_button.bind(on_press=self.stop)

        # change the background color of the button to green
        self.publisher_button.background_color = (0, 1, 0, 1)

        # bind the keyboard key event to the on_keyboard method
        Window.bind(on_keyboard=self.on_keyboard)

    def stop(self, instance):
        """
        Stop the RabbitMQ server
        """
        # stop the container with the name 'aij-messaging-server' and remove it
        client = docker.from_env()
        container = client.containers.get('aij-messaging-server')
        container.stop()

        # change the text of the button to 'Start'
        self.publisher_button.text = 'Start'

        # bind the button click event to the start method
        self.publisher_button.bind(on_press=self.start)

        # change the background color of the button to red
        self.publisher_button.background_color = (1, 0, 0, 1)

    def listen(self):
        # connect to RabbitMQ server and read logs using pika
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        # print all the channel logs
        channel.basic_consume(
            queue='logs', on_message_callback=self.print_logs, auto_ack=True)

        # start listening to the logs
        channel.start_consuming()

    def print_logs(self, ch, method, properties, body):
        """
        The method to print the logs
        """
        # print the logs
        response = body.decode()
        self.publisher_label.text = response

    # add a keyboard key event to stop the RabbitMQ server when the app is closed
    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """
        The method to stop the RabbitMQ server when the app is closed
        The key event is triggered when the escape key is pressed
        """
        if key == 27:
            os.system('rabbitmqctl stop')
            return True


def main():
    # start an instance of AIJMessagingServer class
    msg = AIJMessagingServer()
    msg.run()


if __name__ == '__main__':
    main()
