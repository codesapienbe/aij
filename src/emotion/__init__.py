import cv2
import numpy as np
from keras.models import load_model

# Load the trained model
model = load_model('model.h5')

# Define the emotion labels
emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

# Define a function to detect the face in a frame
def detect_face(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Load the Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    # Detect faces in the grayscale image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    # If no faces are detected, return None
    if len(faces) == 0:
        return None, None
    # If multiple faces are detected, use the largest one
    largest_face = faces[0]
    for face in faces:
        if face[2] * face[3] > largest_face[2] * largest_face[3]:
            largest_face = face
    # Extract the face region from the frame
    x, y, w, h = largest_face
    face_roi = gray[y:y+h, x:x+w]
    # Resize the face region to 48x48 pixels
    face_roi = cv2.resize(face_roi, (48, 48))
    # Return the face region and the coordinates of the face
    return face_roi, largest_face

# Define a function to predict the emotion in a face
def predict_emotion(face):
    # Reshape the face to match the input shape of the model
    face = face.reshape(1, 48, 48, 1)
    # Normalize the pixel values to be between 0 and 1
    face = face / 255.0
    # Predict the emotion label using the trained model
    predictions = model.predict(face)
    # Return the predicted emotion label
    return emotions[np.argmax(predictions)]

# Open a video stream
cap = cv2.VideoCapture(0)

while True:
    # Read a frame from the video stream
    ret, frame = cap.read()
    # Detect the face in the frame
    face, coords = detect_face(frame)
    # If a face is detected, predict the emotion label and draw a rectangle around the face
    if face is not None:
        emotion = predict_emotion(face)
        x, y, w, h = coords
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, emotion, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    # Display the frame
    cv2.imshow('Face Emotion Recognition', frame)
    # Wait for a key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video stream and close all windows
cap.release()
cv2.destroyAllWindows()