# Backend Robot Explorateur - First-Year SRI Project 2023/2024

[Français](README.fr.md) | English

![Flask](https://img.shields.io/badge/built%20with-Flask-red)
![Status](https://img.shields.io/badge/status-completed-green)

This backend was developed to connect the Angular frontend interface with the Raspberry Pi embedded on the explorer robot. It manages bidirectional communication, sensor data processing from the Lidar, camera, and microphone, robot control through HTTP/WebSocket communication, and real-time analysis.

---

## Objective

- Ensure real-time communication between the robot, the Raspberry Pi, the user interface, and the sensors.
- Process sensor inputs, including video, audio, and Lidar data, for the voice command, ball tracking, and mapping modes.

---

## Main features

- WebSocket and REST API: real-time event exchange, including active modes and sensor data.
- Voice command mode: audio processing and command dictionaries to generate robot commands.
- Ball tracking mode: color detection and intelligent command generation.
- Mapping mode: automatic navigation using Lidar data for obstacle avoidance and mapping.
- Video and Lidar streaming: JPEG encoding and transmission to the interface.
- Robot communication: sending and forwarding HTTP commands to the Raspberry Pi.

---

## Technical stack

- Language: Python
- Frameworks: Flask, Flask-SocketIO, Flask-CORS
- Libraries:
  - Audio processing: `speech_recognition`, `gTTS`, `pydub`
  - Image processing: `OpenCV`, `matplotlib`
  - Communication: `requests`, `socket`, `threading`
  - Web and data handling: `werkzeug`, `json`, `numpy`

---

## Status

Project completed in 2024. It was used during demonstrations to validate the cross-disciplinary skills developed during the project.

This project was also used as a development platform during [HackaTAL 2024](https://hackatal.github.io/2024/), a hackathon focused on Natural Language Processing and generative AI applied to converting audio into robot commands.

---

## Run the project locally

```bash
# Clone the repository
git clone https://github.com/MaelaViguier/mobile_robot_backend.git
cd mobile_robot_backend

# Install the dependencies
pip install opencv_python
pip install matplotlib
pip install speech_recognition
pip install werkzeug
# Install the remaining required dependencies

# Start the Flask server with WebSocket support
python3 back_end_interface_robot_explorateur.py

# The backend will be available at http://localhost:5000
