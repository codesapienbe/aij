import pika
import os
import deepl

import docker
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class TranslationServer:
    def __init__(self, input_queue_name, output_queue_name, rabbitmq_host='localhost'):
        self.rabbitmq_host = rabbitmq_host
        self.input_queue_name = input_queue_name
        self.output_queue_name = output_queue_name
        self.api_key = os.environ.get('DEEPL_AUTH_KEY')

        self.input_channel = None
        self.output_channel = None

        self.connection = None
        self.connect()

    def connect(self):
        parameters = pika.ConnectionParameters(host=self.rabbitmq_host)
        self.connection = pika.BlockingConnection(parameters)

        self.input_channel = self.connection.channel()
        self.input_channel.queue_declare(queue=self.input_queue_name)

        self.output_channel = self.connection.channel()
        self.output_channel.queue_declare(queue=self.output_queue_name)

    def start_consuming(self):
        self.input_channel.basic_consume(queue=self.input_queue_name, on_message_callback=self.on_message,
                                        auto_ack=True)
        self.input_channel.start_consuming()

    def on_message(self, channel, method, properties, body):
        if body is None:
            self.send_message('.' * 10)
        message_text = body.decode('utf-8')
        translated_text = self.translate(message_text)
        self.send_message(translated_text)

    def translate(self, text):
        translator = deepl.Translator(self.api_key)
        translated_text = translator.translate_text(text, source_lang='EN', target_lang='NL').text
        return translated_text

    def send_message(self, message):
        self.output_channel.basic_publish(exchange='', routing_key=self.output_queue_name, body=message)
        print(message)

    def close(self):
        self.input_channel.close()
        self.output_channel.close()

        if self.connection is not None and not self.connection.is_closed:
            self.connection.close()

    def reconnect(self):
        self.close()
        self.connect()


def main():
    translator = TranslationServer('speech_to_text_stream', 'translated_text_stream')
    translator.start_consuming()

if __name__ == '__main__':
    main()
