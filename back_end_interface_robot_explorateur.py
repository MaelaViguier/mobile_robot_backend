#backend server
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
#Utils
import json
import numpy as np
import os
from werkzeug.utils import secure_filename
from tempfile import mkstemp
#Traitement des images
import cv2 as cv
#Traitement du son :
import torch
import whisper

#Utilisation du GPU si possible
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("GPU est disponible. Utilisation du GPU...")
else:
    device = torch.device("cpu")
    print("GPU n'est pas disponible. Retour au CPU...")

#Chargement du model Whisper
model = whisper.load_model("medium", device=device)

#Initialisation du serveur
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r'/*': {'origins': '*'}})
socketio = SocketIO(app, cors_allowed_origins="*")


# Definition des dynamiques des couleurs détéctables
color_ranges = {
    'bleu': ([100, 100, 0], [140, 255, 255]),
    'orange': ([5, 50, 50], [15, 255, 255]),
    'jaune': ([20, 100, 100], [30, 255, 255]),
    'blanc': ([0, 0, 120], [160, 240, 255]),
    'vert clair': ([40, 40, 50], [80, 255, 255]),   # Vert Clair
    'or foncé': ([20, 150, 50], [40, 255, 150])
}
#Initalisation des données de détection
ball_data = []
#Initialisation des couleurs détectables
active_colors = []
#Initialisation des extentions audio compatibles :
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}


# Fonction qui recupere les couleurs à détecter
def get_colors():
    print(active_colors)
    return active_colors
#Lien de modification des couleurs détectables via requette HTTP
@app.route('/update_active_colors', methods=['POST'])
def update_active_colors():
    global color_ranges, active_colors
    print(active_colors)
    data = request.json
    if 'colors' in data:
        # Filter color_ranges to include only those colors that are sent from the frontend
        active_colors = {color: color_ranges[color] for color in data['colors'] if color in color_ranges}
        return jsonify({"status": "Active colors updated successfully", "activeColors": list(active_colors.keys())}), 200
    return jsonify({"error": "Invalid request"}), 400

# Fonction pour traiter une image
def process_frame(frame):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    ball_data = []
    for color in get_colors():
        lower, upper = [np.array(x) for x in color_ranges[color]]
        mask = cv.inRange(hsv, lower, upper)
        # Opérations morphologiques :
        kernel = np.ones((5, 5), np.uint8)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv.contourArea(contour)
            perimeter = cv.arcLength(contour, True)
            if perimeter == 0:
                continue  # Divison par 0 impossible
            roundness = (4 * np.pi * area) / (perimeter ** 2)
            if area > 500 and roundness > 0.5:
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
                        ball_data, processed_frame = process_frame(frame)
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


#Traitement du son (transcription)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' in request.files:
        audio_file = request.files['audio']
        if audio_file and allowed_file(audio_file.filename):
            filename = secure_filename(audio_file.filename)
            return "Fichier reçu", 200
    return "Aucun fichier reçu ou type de fichier non autorisé", 400

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        if 'file' in request.files:
            audio_file = request.files['file']
            fd, path = mkstemp()
            try:
                with os.fdopen(fd, 'wb') as tmp:
                    audio_file.save(tmp)
                # Charger, traiter et transcrire l'audio
                audio = whisper.load_audio(path)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio).to(model.device)
                options = whisper.DecodingOptions()
                result = whisper.decode(model, mel, options)
                return jsonify({"transcription": result.text}), 200
            finally:
                os.unlink(path)  # Assurez-vous que le fichier est supprimé après utilisation
    except Exception as e:
        print(f"Erreur lors de la transcription: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

    return jsonify({"error": "Aucun fichier reçu"}), 400

@app.after_request
def after_request(response):
    print("Headers:", response.headers)
    return response

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0')
