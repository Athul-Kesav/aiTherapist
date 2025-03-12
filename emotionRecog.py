import cv2
import time
from deepface import DeepFace

# Open Webcam
cap = cv2.VideoCapture(1)

last_checked = time.time()  # Track last analysis time
dominant_emotion = "Scanning..."  # Default emotion

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    current_time = time.time()
    
    # Run emotion detection every 3 seconds
    if current_time - last_checked >= 3:
        try:
            # Analyze emotion in the current frame
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            
            # Get the dominant emotion
            dominant_emotion = result[0]['dominant_emotion']
            
            # Update last checked time
            #last_checked = current_time
        
        except Exception as e:
            print("Error:", e)
            dominant_emotion = "Unknown"

    # Display Emotion on Screen
    cv2.putText(frame, f"Emotion: {dominant_emotion}", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Show Video Feed
    cv2.imshow("Emotion Detection", frame)
    
    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
