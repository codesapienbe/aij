import cv2
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_objectron = mp.solutions.objectron

def main():

    # For webcam input:
    cap = cv2.VideoCapture(0)

    with mp_objectron.Objectron(static_image_mode=False,
                                max_num_objects=5,
                                min_detection_confidence=0.5,
                                min_tracking_confidence=0.75,
                                model_name='Cup') as objectron:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                # If loading a video, use 'break' instead of 'continue'.
                continue

            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = objectron.process(image)

            # Draw the box landmarks on the image.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.detected_objects:
                for detected_object in results.detected_objects:
                    mp_drawing.draw_landmarks(
                        image, detected_object.landmarks_2d, mp_objectron.BOX_CONNECTIONS)
                    mp_drawing.draw_axis(image, detected_object.rotation,
                                        detected_object.translation)
            # Flip the image horizontally for a selfie-view display.
            cv2.imshow('Objectron', cv2.flip(image, 1))

            
            # if escape or q is pressed, break the loop
            if (cv2.waitKey(5) & 0xFF == 27) or (cv2.waitKey(5) & 0xFF == ord('q')):
                break
        

    cap.release()
    cv2.destroyAllWindows()
    
    
if __name__ == '__main__':
    main()
