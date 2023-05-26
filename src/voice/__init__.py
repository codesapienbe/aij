import pika
import speech_recognition as sr
import os, sys
import docker
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class VoiceToTextServer:
    def __init__(self, source_lang='en-US'):
        self.source_lang = source_lang
        self.timer = 0
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='speech_to_text_stream')
        self.r = sr.Recognizer()
        self.r.dynamic_energy_threshold = True

    def start(self):
        # start listening to mic stream
        with sr.Microphone() as source:
            self.r.adjust_for_ambient_noise(source)
            audio = self.r.listen(source, timeout=30, phrase_time_limit=5)

            try:
                recognized_text = self.r.recognize_whisper_api(
                    audio_data=audio, 
                    model="whisper-1",
                    api_key=os.getenv('WHISPER_API_KEY')
                )
                self.channel.basic_publish(
                    exchange='', routing_key='speech_to_text_stream', body=recognized_text)
                print(recognized_text)

            except sr.UnknownValueError as e:
                self.reconnect()

            except sr.RequestError as e:
                self.reconnect()

        self.start()

    def reconnect(self):
        
        # if self.connection.is_open:
        #     self.connection.close()
        # # reconnect to RabbitMQ
        # self.connection = pika.BlockingConnection(
        #     pika.ConnectionParameters('localhost'))
        # self.channel = self.connection.channel()
        self.channel.queue_declare(queue='speech_to_text_stream')
        self.channel.basic_publish(
            exchange='', routing_key='speech_to_text_stream', body='.')

    def close(self):
        print("Closing the connection to RabbitMQ...")
        if self.connection.is_open:
            self.connection.close()


def main():
    recognizer = VoiceToTextServer()
    recognizer.start()
    recognizer.close()


if __name__ == '__main__':
    main()
