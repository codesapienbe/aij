import os

import cv2
import pika
import threading

speech_data = []
translation_data = []

# define the RabbitMQ consumer class
class RabbitMQConsumer:

    def __init__(self, host, queue_name):
        self.host = host
        self.queue_name = queue_name
        self.channel = None

    def start_consuming(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = connection.channel()
        self.channel.queue_declare(queue=self.queue_name)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.on_message, auto_ack=True)
        print(f'Started consuming messages from {self.queue_name} queue...')
        self.channel.start_consuming()

    def on_message(self, ch, method, properties, body):
        if self.queue_name == "speech_to_text_stream":
            speech_data.append(body.decode('utf-8'))
            
        elif self.queue_name == "translated_text_stream":
            translation_data.append(body.decode('utf-8'))


# create instance of RabbitMQ consumer class
voice_consumer = RabbitMQConsumer('localhost', 'speech_to_text_stream')

# create an instance of RabbitMQ consumer for the translation
translation_consumer = RabbitMQConsumer('localhost', 'translated_text_stream')

# start the RabbitMQ consumer thread
voice_thread = threading.Thread(target=voice_consumer.start_consuming)
voice_thread.start()

# start the RabbitMQ consumer thread
translation_thread = threading.Thread(target=translation_consumer.start_consuming)
translation_thread.start()

# start the video stream
cap = cv2.VideoCapture(0)

# change the video frame size to 1280x720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)


while True:
    # read a frame from the video stream
    ret, frame = cap.read()

    # check if the frame is valid
    if not ret:
        break

    # display the recognized text
    if len(speech_data) > 0:
        # put the text at the bottom center of the frame and make the font size 12pt and white with border and gray background
        cv2.putText(frame, speech_data[-1], (int(frame.shape[1] / 2) - 100, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
        
    if len(translation_data) > 0:
        # put the text at the bottom center of the frame and make the font size 12pt and white with border and gray background
        cv2.putText(frame, translation_data[-1], (int(frame.shape[1] / 2) - 100, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    # display the video frame
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # if c is pressed, then clear the speech data
    if cv2.waitKey(1) & 0xFF == ord('c'):
        speech_data.clear()

    # if s is pressed, then save the speech data to a text file
    if cv2.waitKey(1) & 0xFF == ord('s'):
        with open('speech.txt', 'w') as f:
            f.write(os.linesep.join(speech_data))

# release the video stream and destroy all windows
cap.release()
cv2.destroyAllWindows()

# stop the RabbitMQ consumer thread
voice_thread.join()
translation_thread.join()
