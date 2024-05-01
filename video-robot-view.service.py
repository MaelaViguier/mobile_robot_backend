from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
import cv2 as cv
import numpy as np
import requests
import json
from flask_cors import CORS


app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r'/*': {'origins': '*'}})
socketio = SocketIO(app, cors_allowed_origins="*")


# Define color ranges in HSV
color_ranges = {
    'bleu': ([100, 100, 0], [140, 255, 255]),  # Blue in French
    'orange': ([5, 50, 50], [15, 255, 255]),
    'jaune': ([20, 100, 100], [30, 255, 255])  # Yellow in French
}
ball_data = []
# Function to handle color selection
def get_colors():
    return {'jaune'}  # Always return 'jaune' color

# Function to process frame and emit ball data via WebSocket
def process_frame(frame, valid_colors):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    ball_data = []
    for color in valid_colors:
        lower, upper = [np.array(x) for x in color_ranges[color]]
        mask = cv.inRange(hsv, lower, upper)
        # Apply morphological operations to clean the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv.contourArea(contour)
            if area > 100:
                M = cv.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    ball_data.append({
                        "color": color,
                        "area": area,
                        "position": (cX, cY)
                    })
                    cv.circle(frame, (cX, cY), 7, (0, 255, 0), -1)
    print(ball_data)
    return ball_data, frame

# Route to handle video stream processing and WebSocket communication
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Route to handle video stream processing and WebSocket communication
@socketio.on('request_frame')
def handle_frame_request():
    valid_colors = get_colors()
    url = "http://obvault.duckdns.org:31000/video_feed"
    stream = requests.get(url, stream=True)
    boundary = b'--frame'
    buffer = b''
    try:
        for chunk in stream.iter_content(chunk_size=1024):
            buffer += chunk
            a = buffer.find(boundary, len(boundary))
            b = buffer.find(boundary, a + len(boundary))
            if a != -1 and b != -1:
                jpg = buffer[a + len(boundary):b]
                start = jpg.find(b'\xff\xd8')
                end = jpg.find(b'\xff\xd9')
                if start != -1 and end != -1:
                    jpg = jpg[start:end+2]
                    frame = cv.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv.IMREAD_COLOR)
                    if frame is not None:
                        global ball_data
                        ball_data, processed_frame = process_frame(frame, valid_colors)
                        # Ensure emit is called within the context of SocketIO
                        socketio.emit('ball_data', json.dumps(ball_data))
                        # Stream processed frame to client
                        ret, jpeg = cv.imencode('.jpg', processed_frame)
                        frame_bytes = jpeg.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                buffer = buffer[b:]
    except Exception as e:
        print(f"An error occurred: {e}")

@app.route('/video_feed')
def video_feed():
    return Response(handle_frame_request(), content_type='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_detections', methods=['GET'])
def get_detections():
    return jsonify(ball_data)


@socketio.on('request_data')
def handle_request_data():
    # Process and get your data
    emit('ball_data', ball_data, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0')
