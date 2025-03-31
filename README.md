# Backend Robot Explorateur - Projet Fil Rouge 1A SRI 2023/2024

![Flask](https://img.shields.io/badge/built%20with-flask-red)
![Status](https://img.shields.io/badge/status-terminé-green)

Ce backend a été développé pour servir de lien entre l’interface frontend Angular et le Raspberry Pi embarqué sur le robot explorateur. Il gère la communication bidirectionnelle, le traitement des données issues des capteurs (Lidar, caméra, micro), la commande du robot via HTTP/Socket et l’analyse temps réel.

---

## Objectif

- Assurer la communication temps réel entre le robot (Raspberry Pi), l’interface utilisateur et les capteurs.
- Traiter les entrées capteurs (vidéo, audio, lidar) pour les exploiter dans les modes : commande vocale, suivi de balle, cartographie.

---

## Fonctionnalités principales

- **WebSocket + API REST** : échange d’événements en temps réel (modes actifs, données capteurs).
- **Mode vocal** : traitement audio + dictionnaires pour générer des commandes robot.
- **Mode suiveur de balle** : détection de couleurs + envoi intelligent des commandes.
- **Mode cartographie** : pilotage automatique à l'aide du lidar (avoidance + mapping).
- **Streaming vidéo et lidar** : encodage JPEG et envoi vers l’interface.
- **Communication robot** : envoi/forward des commandes HTTP vers le Raspberry Pi.

---

## Stack technique

- **Langage** : Python
- **Frameworks** : Flask, Flask-SocketIO, Flask-CORS
- **Librairies** :
  - Traitement audio : `speech_recognition`, `gTTS`, `pydub`
  - Traitement image : `OpenCV`, `matplotlib`
  - Communication : `requests`, `socket`, `threading`
  - Web : `werkzeug`, `json`, `numpy`

---

## Statut

Projet **terminé** (2024). Utilisé lors de démonstrations pour valider les compétences transverses du projet.
Ce projet a été utilisé comme plateforme de développement lors du **[HackaTAL 2024](https://hackatal.github.io/2024/)**, un hackathon autour du TAL et des IA génératives appliquées à la conversion audio en commandes.
  
---

## Lancer le projet en local

```bash
# Cloner le repo
$ git clone https://github.com/MaelaViguier/mobile_robot_backend.git
$ cd mobile_robot_backend

# Installer les dépendances
$ pip install opencv_python
$ pip install matplotlib
$ pip install speech_recognition
$ pip install werkzeug
... et toutes les autres

# Lancer le serveur Flask avec WebSocket
$ python3 back_end_interface_robot_explorateur.py

# Le backend sera accessible sur http://localhost:5000
```

---


## 🎨 Demo

<div align="center">
  <img src="https://github.com/Bebel19/interface_robot_explorateur/blob/master/src/assets/image/20240512_195038.jpg?raw=true" alt="Robot explorateur" width="400"/>
  <br/>
  <img src="https://github.com/Bebel19/interface_robot_explorateur/blob/master/src/assets/video/robot_explorateur.gif?raw=true" alt="Robot explorateur GIF" width="800"/>
</div>




---

**Projet universitaire ✨** — UPSSITECH Toulouse
