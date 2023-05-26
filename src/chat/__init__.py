import time
import pika
import os
import openai
import docker

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# TODO: Implement this feature later
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

class AIAssistant:
    """
    AI Assistant class that uses OpenAI's GPT-3 API to generate responses.
    """

    def __init__(self, api_key):
        """
        Initializes the AI Assistant.
        :param api_key: The OpenAI API key.
        """
        self.api_key = api_key
        self.start_sequence = "\nAIJ:"
        self.restart_sequence = "\nHuman: "
        self.model = "text-davinci-003"
        self.temperature = 1
        self.max_tokens = 4000
        self.top_p = 1
        self.frequency_penalty = 0.62
        self.presence_penalty = 0.6
        self.stop = [" Human:", " AI:"]

        openai.api_key = self.api_key

    def generate_response(self, prompt):
        """
        Generates a response using OpenAI's GPT-3 API.
        :param prompt: The prompt to use for the AI to generate a response.
        :return: The generated response.
        """
        response = openai.Completion.create(
            model=self.model,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop
        )
        return response.choices[0].titles


class NewsConsumer:
    """
    News Consumer class that consumes news from a RabbitMQ queue.
    """

    def __init__(self, host, ai_assistant):
        """
        Initializes the News Consumer.
        """
        self.ai_assistant = ai_assistant
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='news_stream')

    def consume(self):
        """
        Consumes news from the RabbitMQ queue.
        """
        self.channel.basic_consume(
            queue='news_stream', on_message_callback=self.callback)
        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        """
        Callback function that is called when a message is received from the RabbitMQ queue.
        :param ch: The channel.
        :param method: The method.
        :param properties: The properties.
        :param body: The body of the message.
        """
        prompt = body.decode('utf-8').strip() + \
            self.ai_assistant.restart_sequence
        response = self.ai_assistant.generate_response(prompt)
        print(response)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def close(self):
        """
        Closes the connection.
        """
        if self.connection.is_open:
            self.connection.close()


def main():
    
    api_key = os.environ.get("OPENAI_API_KEY")
    ai_assistant = AIAssistant(api_key)
    consumer = NewsConsumer('localhost', ai_assistant)

    try:
        consumer.consume()
    except KeyboardInterrupt:
        consumer.close()


if __name__ == '__main__':
    main()
