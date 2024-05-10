import threading
import socket
import json
from rplidar import RPLidar
import cv2
from flask import Flask, Response
from flask_cors import CORS
from flask import request, jsonify

app = Flask(__name__)
CORS(app)
# Setup serial connection
try:
    ser = serial.Serial('/dev/ttyUSB1', 9600)
    time.sleep(2)  # Wait for the connection to initialize
except Exception as e:
    print(f"Error opening serial port: {e}")

def send_command_to_arduino(command):
    """Send command to Arduino via serial."""
    if ser.is_open:
        ser.write(command.encode())
        print(f"Sent command to Arduino: {command}")
    else:
        print("Serial port is not open.")

@app.route('/command', methods=['POST'])
def receive_command():
    """Receive command from API and forward to Arduino."""
    command_data = request.json
    command = command_data.get('command')
    if command in ['F', 'B', 'L', 'R', 'S']:
        send_command_to_arduino(command)
        return jsonify({"status": "Command executed"}), 200
    else:
        return jsonify({"error": "Invalid command"}), 400



def gen_frames():
    camera = cv2.VideoCapture(0 + cv2.CAP_V4L2)
    if not camera.isOpened():
        raise RuntimeError("Could not open video source")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        camera.release()

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='video/mjpeg')

def lidar_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '0.0.0.0'
    port = 12345

    server_socket.bind((host, port))
    server_socket.listen(5)
    print('Server is listening...')

    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"Connection from: {addr}")

            lidar = RPLidar('/dev/ttyUSB0')

            try:
                for scan in lidar.iter_scans():
                    data_to_send = json.dumps(scan) + '\n'
                    client_socket.send(data_to_send.encode('ascii'))
            except socket.error as e:
                print(f"Socket error: {e}")
            finally:
                lidar.stop()
                lidar.disconnect()
                client_socket.close()
                print("Connection closed. Waiting for new connection...")
        except Exception as e:
            print(f"An error occurred: {e}")




def run_flask_app():
    app.run(host='0.0.0.0', port=31000, threaded=True)

if __name__ == '__main__':
    # Thread for the LiDAR server
    lidar_thread = threading.Thread(target=lidar_server)
    lidar_thread.start()

    # Thread for the Flask app
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()
