from flask import Flask, Response
import cv2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def gen_frames():
    # Try to open the video capture with the default backend
    camera = cv2.VideoCapture(0 + cv2.CAP_V4L2)
    
    # Check if the camera was successfully opened
    if not camera.isOpened():
        raise RuntimeError("Could not open video source")

    try:
        while True:
            success, frame = camera.read()  # read the camera frame
            if not success:
                break  # if frame reading was not successful, exit the loop
            
            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue  # if frame compression failed, skip the frame

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concatenate frame one by one and show result
    finally:
        camera.release()  # make sure to release the camera

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='video/mjpeg')


if __name__ == '__main__':
    try:
        # Running the Flask app
        app.run(host='0.0.0.0', port=31000, threaded=True)
    except KeyboardInterrupt:
        print("Shutting down the server...")
    except Exception as e:
        print(f"An error occurred: {e}")

