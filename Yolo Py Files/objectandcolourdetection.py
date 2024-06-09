import cv2
import numpy as np
import urllib.request
from flask import Flask, Response
import threading
import requests
import time

app = Flask(__name__)

modelConfig = ""
modelWeights = ""
classesfile = ""

# Load class names
with open(classesfile, 'rt') as f:
    classes = f.read().rstrip('\n').split('\n')

net = cv2.dnn.readNetFromDarknet(modelConfig, modelWeights)
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

image_url = "<Insert_Stream_IP_Here>/shot.jpg"
latest_frame = None
frame_lock = threading.Lock()

last_request_time = 0
request_interval = 10 

def send_request():
    try:
        print("Person with dominant green color detected!")
        response = requests.get("<Insert_ESP_IP>", timeout=5)
        if response.status_code == 200:
            print(f"Request sent, response: {response.text}")
        else:
            print(f"Error: Unexpected response status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error sending request: {e}")

def detect_color(image, contour):
    mask = np.zeros(image.shape[:2], dtype="uint8")
    cv2.drawContours(mask, [contour], -1, 255, -1)

    mean_color = cv2.mean(image, mask=mask)[:3]
    return mean_color

def capture_frames():
    global latest_frame, last_request_time
    while True:
        try:
            with urllib.request.urlopen(image_url) as url:
                image = np.asarray(bytearray(url.read()), dtype=np.uint8)
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            resized_image = cv2.resize(image, (416, 416))
            blob = cv2.dnn.blobFromImage(resized_image, 1/255.0, (416, 416), swapRB=True, crop=False)
            net.setInput(blob)
            outputs = net.forward(output_layers)

            boxes = []
            confidences = []
            classIDs = []
            colors = []
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    classID = np.argmax(scores)
                    confidence = scores[classID]
                    if confidence > 0.5:
                        center_x = int(detection[0] * 416)
                        center_y = int(detection[1] * 416)
                        w = int(detection[2] * 416)
                        h = int(detection[3] * 416)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        classIDs.append(classID)
                        colors.append((0, 255, 0))

            indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            person_with_green_detected = False
            if len(indices) > 0:
                for i in indices.flatten():
                    if classes[classIDs[i]] == "person":
                        (x, y, w, h) = (boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3])

                        # Detect color
                        roi = resized_image[y:y+h, x:x+w]
                        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)
                        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        if contours:
                            max_contour = max(contours, key=cv2.contourArea)
                            color = detect_color(roi, max_contour)
                            colors[i] = color

                            # Check if the detected color is dominantly green
                            if color[1] > color[0] and color[1] > color[2]:
                                person_with_green_detected = True

                                # Draw bounding box with the detected color
                                cv2.rectangle(resized_image, (x, y), (x + w, y + h), color, 2)
                                text = "{}: {:.4f}".format(classes[classIDs[i]], confidences[i])
                                cv2.putText(resized_image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                current_time = time.time()
                if person_with_green_detected and (current_time - last_request_time > request_interval):
                    send_request()
                    last_request_time = current_time

            with frame_lock:
                latest_frame = resized_image
        except Exception as e:
            print(f"Error: {e}")

def generate():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is not None:
                _, jpeg = cv2.imencode('.jpg', latest_frame)
                frame = jpeg.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/')
def index():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    t = threading.Thread(target=capture_frames)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=4000)
