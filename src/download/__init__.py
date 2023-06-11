import json
import logging as log
import time
from threading import Timer, Thread
import logging as log
import os, sys
import time
import pika
from datetime import datetime

# using Kivy to create a GUI for the publisher and subscriber
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import docker

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class VideoPublisher:
    """
    A class to publish news articles to a RabbitMQ queue using the NewsAPI
    @param api_key: the api key to access the NewsAPI
    @param host: the host name of the RabbitMQ server
    @param queue_name: the name of the queue to publish the news articles
    """

    def __init__(self, host='localhost', queue_name='video_stream'):
        self.host = host
        self.queue_name = queue_name
        # set up a connection to RabbitMQ
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()
        self.sources = [
            'https://www.youtube.com/watch?v=8Db3rluT76w&pp=ygULZnVubnkgbmV3cyA%3D',
        ]

    def publish(self):
        """
        Publish the news articles to the RabbitMQ queue one by one and save the news to the database
        """
        try:
            for _source in self.sources:
                
                _video_cmd = f'youtube-dl "{_source}"'
                
                os.system(_video_cmd)

                _body = json.dumps(
                    {
                        'id': _source.split("/")[-1],
                        'src': _source,
                        'at': time.time(),
                        'on': datetime.now(),
                        'by': 'AIJ'
                    }
                ).encode('utf-8')

                self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=_body)

                log.info(
                    f"Published a news article to the queue: {_source}")

                # wait for 1 second before publishing the next article
                time.sleep(1)

        except Exception as api_exception:
            log.error(
                f"Could not request results from NewsAPI; {api_exception}")

        # do not close the connection until the message is delivered
        if self.connection.is_open:
            self.connection.close()

        # call the function again after 100 seconds because there are max. 100 results per page
        Timer(60 * 5, self.publish).start()

    def destroy(self):
        """
        Destroy the connection to the RabbitMQ server
        """
        self.connection.close()


class VideoSubscriber:
    """
    This class implements a RabbitMQ consumer.
    """

    def __init__(self, host='localhost', queue_name='video_stream', callback=None):
        """
        This method initializes the consumer.
        """
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue_name)
        self.callback = callback
        self.queue_name = queue_name

    def subscribe(self):
        """
        This method starts consuming messages from the RabbitMQ queue.
        """
        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=self.callback, auto_ack=True)
        self.channel.start_consuming()

    def destroy(self):
        """
        This method closes the connection to the RabbitMQ server.
        """
        if self.connection.is_open:
            self.connection.close()


class AIJKivy(App):
    """
    A class to create a GUI for the publisher and subscriber
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # create an instance of the VideoPublisher class
        self.publisher = VideoPublisher(
            host='localhost',
            queue_name='video_stream'
        )

        # create an instance of the VideoSubscriber class
        self.subscriber = VideoSubscriber(
            host='localhost',
            queue_name='video_stream',
            callback=self.print_news
        )

        self.title = 'AIJ News'
        self.icon = 'logo.png'

        # create a layout for the publisher
        self.publisher_layout = BoxLayout(orientation='vertical', padding=10)
        self.publisher_label = Label(text='Publisher', size_hint=(1, 0.90))
        self.publisher_button = Button(text='Publish', size_hint=(1, 0.10))

        # create a layout for the subscriber
        self.subscriber_layout = BoxLayout(orientation='vertical', padding=10)
        self.subscriber_label = Label(text='Subscriber', size_hint=(1, 0.90))
        self.subscriber_button = Button(text='Subscribe', size_hint=(1, 0.10))

        # create a layout for the main window
        self.main_layout = BoxLayout(orientation='horizontal', padding=10)

    def build(self):
        """
        Build the GUI for the publisher and subscriber
        """

        # add the label, text input and button to the publisher layout
        self.publisher_layout.add_widget(self.publisher_label)
        self.publisher_layout.add_widget(self.publisher_button)
        # bind the button to the publish method
        self.publisher_button.bind(on_press=self.publish)

        # add the label, text input and button to the subscriber layout
        self.subscriber_layout.add_widget(self.subscriber_label)
        self.subscriber_layout.add_widget(self.subscriber_button)
        # bind the button to the subscribe method
        self.subscriber_button.bind(on_press=self.subscribe)

        # add the publisher and subscriber layouts to the main layout
        self.main_layout.add_widget(self.publisher_layout)
        self.main_layout.add_widget(self.subscriber_layout)

        return self.main_layout

    def publish(self, *args):
        """
        The method to publish the news articles to the RabbitMQ queue
        """

        # starts a thread to publish the news articles to the RabbitMQ queue
        news_publisher_thread = Thread(target=self.publisher.publish)

        # start the thread
        news_publisher_thread.start()

    def subscribe(self, *args):
        """
        The method to subscribe to the RabbitMQ queue and receive the news articles
        """

        # starts a thread to subscribe to the RabbitMQ queue and receive the news articles
        news_subscriber_thread = Thread(target=self.subscriber.subscribe)

        # start the thread
        news_subscriber_thread.start()

    def print_news(self, ch, method, properties, body):
        """
        This method is called when a message is received from the RabbitMQ queue.
        """
        response = body.decode('utf-8')
        print(
            f'-------------------------\n'
            f'{response}'
            f'-------------------------\n'
        )
        time.sleep(1)

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

def main():
    """
    The main function to run the server and publish the news articles to the RabbitMQ queue
    """
    print('Server is being initialized...')

    # initialize the server if it is not already initialized
    pre_init()
    
    # create an instance of the AIJKivy class
    app = AIJKivy()
    app.run()

    print('Server is now running...')


if __name__ == '__main__':
    main()
