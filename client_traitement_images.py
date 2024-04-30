import cv2 as cv
import numpy as np
import requests

# Define color ranges in HSV
color_ranges = {
    'bleu': ([100, 100, 0], [140, 255, 255]),  # Blue in French
    'orange': ([5, 50, 50], [15, 255, 255]),
    'jaune': ([20, 100, 100], [30, 255, 255])  # Yellow in French
}

# Define functions to handle color selection and image processing
def get_colors():
    print("Couleurs valides : bleu, orange, jaune.")
    couleurs_detecte = input("Entrez les couleurs de balles à détecter (séparées par des espaces) : ").split()
    valid_colors = {color for color in couleurs_detecte if color in color_ranges}
    if not valid_colors:
        print("Aucune couleur valide n'a été entrée.")
        exit()
    return valid_colors

def process_frame(frame, valid_colors):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    final_mask = None
    for color in valid_colors:
        lower, upper = [np.array(x) for x in color_ranges[color]]
        mask = cv.inRange(hsv, lower, upper)
        final_mask = mask if final_mask is None else cv.bitwise_or(final_mask, mask)

    if final_mask is not None:
        # Apply morphological operations to clean the mask
        kernel = np.ones((5, 5), np.uint8)
        final_mask = cv.morphologyEx(final_mask, cv.MORPH_CLOSE, kernel)
        result = cv.bitwise_and(frame, frame, mask=final_mask)
        contours, _ = cv.findContours(final_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        detected_balls = False
        for contour in contours:
            area = cv.contourArea(contour)
            if area > 100:
                M = cv.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    detected_balls = True
                    print(f"Balle de couleur: {color}, Superficie: {area} pixels, Position du centre: ({cX}, {cY})")
                    cv.circle(frame, (cX, cY), 7, (0, 255, 0), -1)
        if not detected_balls:
            print("Aucune balle détectée.")
        cv.imshow('Processed Video Stream', frame)
        cv.waitKey(1)

def main():
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
                        process_frame(frame, valid_colors)
                buffer = buffer[b:]
    except KeyboardInterrupt:
        print("Stream manually interrupted.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cv.destroyAllWindows()

if __name__ == "__main__":
    main()
