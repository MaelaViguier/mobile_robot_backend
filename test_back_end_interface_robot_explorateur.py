# backend server
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import socket
import threading
# Utils
import json
import numpy as np
import os
from werkzeug.utils import secure_filename
from tempfile import mkstemp
import time
# Traitement des images
import cv2 as cv
# Traitement du son :
import torch

import whisper
# Lidar
import matplotlib.pyplot as plt


# Classe dictionnaire pour la conversion  texte commande
class Dictionnaire:
    def __init__(self, mots, taille, nom):
        self.mots = mots
        self.taille = taille
        self.nom = nom


# Mesure du temps de démarage
tic = time.time()
# ip du robot :
host = '192.168.80.122'
# Modes disponibles :
modes = [
    {'label': 'Pilotage Manuel', 'active': True},
    {'label': 'Suiveur de Balle', 'active': False},
    {'label': 'Commande Vocale', 'active': False},
    {'label': 'Cartographie', 'active': False}
]

# Initalisation du resultat de la transcription
result = ''
# Initialisation de la variable qui indique la bonne connection au robot
robot_connected = False
#initalisations des donées du lidar :
angles = []
distances = []
# Utilisation du GPU si possible
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("GPU est disponible. Utilisation du GPU...")
else:
    device = torch.device("cpu")
    print("GPU n'est pas disponible. Retour au CPU...")

# Chargement du model Whisper
model = whisper.load_model("medium", device=device)

# Initialisation du serveur
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Definition des dynamiques des couleurs détéctables
color_ranges = {
    'bleu': ([100, 100, 0], [140, 255, 255]),
    'orange': ([5, 50, 50], [15, 255, 255]),
    'jaune': ([20, 100, 100], [30, 255, 255]),
    'blanc': ([0, 0, 120], [160, 240, 255]),
    'vert clair': ([40, 40, 50], [80, 255, 255]),
    'or': ([0, 0, 64], [178, 156, 255])
}
# Initalisation des données de détection
ball_data = []
# Initialisation des couleurs détectables
active_colors = []
# Initialisation des extentions audio compatibles :
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}
# Fin mesure temps démarage
toc = time.time()
print(toc - tic, 'sec Elapsed')


# Status de connexion
@app.route('/robot_status')
def robot_status():
    return jsonify({'connected': robot_connected})


@socketio.on('change_mode')
def handle_change_mode(data):
    global modes
    requested_mode_label = data['label']

    # Set all modes to inactive, then activate the requested mode
    for mode in modes:
        mode['active'] = (mode['label'] == requested_mode_label)
    # Emit the updated list of modes to all clients
    emit('modes_updated', modes, broadcast=True)
    print(f"Mode changed to {requested_mode_label}")


@app.route('/current_mode')
def get_current_mode():
    print("Asked for current mode")
    return jsonify(next((mode for mode in modes if mode['active']), None))


@app.route('/available_modes')
def get_available_modes():
    print("Asked for available modes")
    return jsonify(modes)


# Fonction LIDAR map
def gen_map_frames():
    global robot_connected
    global angles, distances
    # Connect to the socket server (which sends LIDAR data)
    global host  # Adjust to your server's IP address
    port = 12345  # Port on which your server sends LIDAR data
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    robot_connected = True
    print('Lidar client connected')
    # Setup the plot
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    line, = ax.plot([], [], 'b.')  # Initial empty plot

    # Set plot properties
    ax.set_theta_zero_location('N')  # North at the top
    ax.set_theta_direction(-1)  # Clockwise
    ax.set_ylim(0, 4000)  # Set the radius limit
    ax.set_title("Lidar Scan", va='bottom')  # Set the title of the plot

    # Hide the borders
    ax.spines['polar'].set_visible(False)  # Hide the outer circle border

    # Optionally hide grid and ticks if desired
    #ax.grid(False)  # Turn off the grid
    #ax.set_xticklabels([])  # Hide the angle ticks
    #ax.set_yticklabels([])  # Hide the radius ticks

    buffer = ''
    try:
        while True:
            lidarData = client_socket.recv(4096).decode('ascii')
            if not lidarData:
                break
            buffer += lidarData
            while '\n' in buffer:
                line_data, buffer = buffer.split('\n', 1)
                if line_data:
                    scan = json.loads(line_data)
                    angles = np.radians(np.array([item[1] for item in scan]))
                    distances = np.array([item[2] for item in scan])
                    line.set_data(angles, distances)
                    fig.canvas.draw()
                    img = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
                    img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
                    ret, jpeg = cv.imencode('.jpg', img)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    finally:
        plt.close(fig)
        client_socket.close()



@app.route('/map_feed')
def map_feed():
    return Response(gen_map_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Fonction qui recupere les couleurs à détecter
def get_colors():
    return active_colors


# Lien de modification des couleurs détectables via requette HTTP
@app.route('/update_active_colors', methods=['POST'])
def update_active_colors():
    global color_ranges, active_colors
    data = request.json
    if 'colors' in data:
        # Filter color_ranges to include only those colors that are sent from the frontend
        active_colors = {color: color_ranges[color] for color in data['colors'] if color in color_ranges}
        mode_suiveur_balle()
        return jsonify(
            {"status": "Active colors updated successfully", "activeColors": list(active_colors.keys())}), 200
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
            if area > 100 and roundness > 0.3:
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
    return ball_data, frame


# Route to handle video stream processing and WebSocket communication

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Emit the current status of the robot connection when a new client connects
    emit('status_update', {'connected': robot_connected})


@socketio.on('check_status')
def handle_check_status():
    emit('status_update', {'connected': robot_connected})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    emit('status_update', {'connected': robot_connected})


# Route to handle video stream processing and WebSocket communication
@socketio.on('request_frame')
def handle_frame_request():
    global host
    valid_colors = get_colors()
    global robot_connected
    url = "http://" + host + ":31000/video_feed"
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
                    jpg = jpg[start:end + 2]
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
                robot_connected = True
    except Exception as e:
        print(f"An error occurred: {e}")
        robot_connected = False


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


# Traitement du son (transcription)

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
    global language
    global result
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
                _, probs = model.detect_language(mel)
                language = max(probs, key=probs.get)  # Language as a string
                print(f"Detected language: {language}")
                options = whisper.DecodingOptions()
                result = whisper.decode(model, mel, options)
                os.unlink(path)  # Assurez-vous que le fichier est supprimé après utilisation
                mode_commande_vocale(result.text, language)
                print('fin de la commande vocale')
                return jsonify({"transcription": result.text}), 200
            finally:
                if os.path.exists(path):
                    os.unlink(path)
    except Exception as e:
        print(f"Erreur lors de la transcription: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

    return jsonify({"error": "Aucun fichier reçu"}), 400


@app.after_request
def after_request(response):
    print("Headers:", response.headers)
    return response


# Define the route for command sending

@app.route('/send_command', methods=['POST'])
def send_command():
    try:
        data = request.json
        command = data['command']
        print("Commande recue depuis l'interface : " + command)
        # URL where the Raspberry Pi Flask server is listening
        rasp_url = 'http://192.168.80.122:31000/command'

        # Forward the command to the Raspberry Pi
        response = requests.post(rasp_url, json={'command': command})
        if response.status_code == 200:
            print("Commande envoyée au robot : " + command)
            return jsonify({"status": "success", "message": "Command forwarded to Raspberry Pi",
                            "pi_response": response.json()}), 200
        else:
            return jsonify(
                {"status": "error", "message": "Failed to forward command to Raspberry Pi"}), response.status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Comportement des modes
def send_command_to_raspberry(command):
    """
    Sends a specified command to the Raspberry Pi via the chosen communication method.

    Args:
    command (str): The command to send to the Raspberry Pi.
    """
    rasp_url = 'http://192.168.80.122:31000/command'
    print(f"Sending command: {command}")
    # Sendthe command to the Raspberry Pi
    response = requests.post(rasp_url, json={'command': command})
    if response.status_code == 200:
        print("Commande envoyée au robot : " + command)
        return jsonify({"status": "success", "message": "Command forwarded to Raspberry Pi",
                        "pi_response": response.json()}), 200
    else:
        return jsonify(
            {"status": "error", "message": "Failed to forward command to Raspberry Pi"}), response.status_code


# Mode suiveur de balle :
def mode_suiveur_balle():
    global active_colors
    global ball_data
    old_command = 'S'
    print("Mode: Suiveur de Balle is active.")
    while modes[1]["active"]:
        if not active_colors:
            print("No active colors for tracking.")
            continue

        if not ball_data:
            #print("No balls detected.")
            if old_command != 'S':  # If not already stopped, stop the robot
                send_command_to_raspberry('S')
                old_command = 'S'
                time.sleep(0.5)
            continue

        # Ensure there is at least one ball detected and it has 'size' key
        if ball_data and all('area' in ball for ball in ball_data):
            closest_ball = max(ball_data, key=lambda b: b['area'])
            center_x, center_y = 320, 240  # 640x480 resolution
            ball_x, ball_y = closest_ball['position']

            command = determine_command_to_center_ball(ball_x, center_x)
            if command != old_command:
                send_command_to_raspberry(command)
                time.sleep(0.1)
                send_command_to_raspberry('S')
                time.sleep(0.3)
                old_command = command

            command = determine_command_to_set_distance_ball(ball_y,center_y)
            if command != old_command:
                send_command_to_raspberry(command)
                time.sleep(0.1)
                send_command_to_raspberry('S')
                time.sleep(0.5)
                old_command = command
        else:
            print("Ball data is incomplete or missing size key.")
            print(ball_data)
            if old_command != 'S':
                send_command_to_raspberry('S')
                old_command = 'S'


def determine_command_to_center_ball(ball_x, center_x):
    command = 'S'  # Default to stop
    if ball_x < center_x - 110:  # Ball is on the left
        command = 'L'
    elif ball_x > center_x + 110:  # Ball is on the right
        command = 'R'

    print("Determined command : " + command + " from ", ball_data)
    return command


def determine_command_to_set_distance_ball(ball_y, center_y):
    command = 'S'  # Default to stop
    if ball_y < center_y + 100 :  # Ball is on the top
        command = 'F'
    elif ball_y > center_y + 360:  # Ball is on the bottom
        command = 'B'


    print("Determined command : " + command + " from ", ball_data)
    return command



# Mode commande vocale

def charger_dictionnaires():
    filename = "dictionnaires_globaux.json"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            dictionnaires = json.load(file)
            dictionnaires = [
                ({"avancer", "avance"}, 2, "AvancerFR"),
                ({"reculer", "recule"}, 2, "ReculerFR"),
                ({"gauche"}, 1, "GaucheFR"),
                ({"droite"}, 1, "DroiteFR"),
                ({"ne", "n'"}, 2, "NegFR"),
                ({"forward"}, 1, "FrontEN"),
                ({"back"}, 1, "BackEN"),
                ({"left"}, 1, "LeftEN"),
                ({"right"}, 1, "RightEN"),
                ({"don't", "do not"}, 2, "NegEN")
            ]
            print(dictionnaires)
        return dictionnaires
    else:
        print("File not found.")
        return None


def verifie_dico_liste(liste_dico, liste_de_mot, langue):
    parcour = []
    n = 0
    neg = False

    action_correspond = {
        "AvancerFR": "F",
        "ReculerFR": "B",
        "GaucheFR": "L",
        "DroiteFR": "R",
        "FrontEN": "F",
        "BackEN": "B",
        "LeftEN": "L",
        "RightEN": "R"
    }

    for i, mot in enumerate(liste_de_mot):
        if i < len(liste_de_mot) - 1:
            if mot.isdigit() and liste_de_mot[i + 1].isalpha():
                nombre = int(mot)
                unite = liste_de_mot[i + 1].lower()
                if unite == "m":
                    parcour.pop()
                    parcour.extend([action] * nombre)
                elif unite == "cm":
                    parcour.pop()
                    parcour.extend([action.lower()] * nombre)
                continue

        if langue == 'fr':
            if mot in ["et", "puis"]:
                neg = False
            elif dans_le_dico(mot, liste_dico[4]):
                neg = True

            if not neg:
                if analyse_obstacle(mot):
                    parcour.append("O")
                    n += 1
                else:
                    distance = analyse_distance(mot)
                    if distance > 1:
                        res = parcour[-1]
                        parcour.extend([res] * (distance - 1))

                    for dico in liste_dico[:4]:
                        if dans_le_dico(mot, dico):
                            action = action_correspond.get(dico.nom, "")
                            if action:
                                parcour.append(action)
                                n += 1
                            break
        elif langue == 'fr':
            if mot in ["and", "then"]:
                neg = False
            elif dans_le_dico(mot, liste_dico[9]):
                neg = True

            if not neg:
                if analyse_obstacle(mot):
                    parcour.append("O")
                    n += 1
                else:
                    distance = analyse_distance(mot)
                    if distance > 1:
                        res = parcour[-1]
                        parcour.extend([res] * (distance - 1))

                    for dico in liste_dico[5:]:
                        if dans_le_dico(mot, dico):
                            action = action_correspond.get(dico.nom, "")
                            if action:
                                parcour.append(action)
                                n += 1
                            break

    print("Parcours généré :", parcour)
    envoie_info(parcour)
    return parcour




def envoie_info(parcour):
    for caractere in parcour:
        if caractere.isupper():
            duree_envoie = 1
        elif caractere.islower():
            duree_envoie = 0.01
        else:
            continue

        if caractere != '':
            print('durée : ', duree_envoie)
            send_command_to_raspberry(caractere.upper())
            time.sleep(duree_envoie)
        send_command_to_raspberry('S')
        time.sleep(0.1)
    # On s'arrete à la fin de parcours
    send_command_to_raspberry('S')

def analyse_obstacle(mot):
    return mot.lower() == "obstacle"


def analyse_distance(mot):
    if mot.isdigit():
        return int(mot)
    return -1


def dans_le_dico(mot, dico):
    return mot in dico.mots


def liste_mot(phrase):
    mots = [mot.lower() for mot in phrase.split()]
    return mots


def mode_commande_vocale(phrase, langue):
    print("On est dans le mode commande vocale")
    print("Transcription vocale : ", phrase)
    mots = liste_mot(phrase)
    verifie_dico_liste(charger_dictionnaires(), mots, langue)

# MOde cartographie :
@app.route('/start_mapping', methods=['POST'])
def start_mapping():
    modes[3]["active"] = True  # Activer le mode cartographie
    cartographie_thread = threading.Thread(target=mode_cartographie)
    cartographie_thread.start()
    return jsonify({"status": "mapping started"})


def mode_cartographie():
    global angles, distances

    while modes[3]["active"]:
        if angles.size == 0 or distances.size == 0:
            print("No LIDAR data available yet.")
            time.sleep(0.1)
            continue

        # Paramètres de seuil (en millimètres)
        front_distance_threshold = 300.0  # distance désirée de l'obstacle devant en mm
        tolerance = 50.0  # tolérance en mm

        # Détection de l'obstacle devant
        front_angles = (angles > -np.pi / 6) & (angles < np.pi / 6)  # ±30 degrés devant
        front_distances = distances[front_angles]

        if len(front_distances) > 0 and min(front_distances) < front_distance_threshold:
            send_command_to_raspberry('S')
            # Trouver la direction avec l'obstacle le plus éloigné
            left_angles = (angles > np.pi / 6) & (angles < np.pi / 2)  # 30° à 90° gauche
            right_angles = (angles < -np.pi / 6) & (angles > -np.pi / 2)  # 30° à 90° droite

            left_distances = distances[left_angles]
            right_distances = distances[right_angles]

            avg_left_distance = np.mean(left_distances) if len(left_distances) > 0 else 0
            avg_right_distance = np.mean(right_distances) if len(right_distances) > 0 else 0

            if avg_left_distance > avg_right_distance:
                send_command_to_raspberry('L')
            else:
                send_command_to_raspberry('R')
        else:
            send_command_to_raspberry('F')

        time.sleep(0.1)  # Pause pour éviter une boucle trop rapide

# Main :
if __name__ == "__main__":
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True, host='0.0.0.0')
