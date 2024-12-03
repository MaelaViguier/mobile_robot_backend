import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

# Define color ranges in HSV
color_ranges = {
    'bleu': ([100, 100, 0], [140, 255, 255]),  # Blue in French
    'orange': ([5, 50, 50], [15, 255, 255]),
    'jaune': ([20, 100, 100], [30, 255, 255])  # Yellow in French
}

def load_image():
    while True:
        numero = input("Entrez le numéro de l'image à traiter : ")
        image = cv.imread(f"images/IMG_{numero}.jpeg")
        if image is not None:
            return image
        else:
            print("Impossible de charger l'image. Vérifiez le numéro de l'image.")

def get_colors():
    while True:
        couleurs_detecte = input("Entrez les couleurs de balles à détecter (séparées par des espaces, ex: bleu orange jaune) : ").split()
        if all(color in color_ranges for color in couleurs_detecte):
            return couleurs_detecte
        else:
            print("Une ou plusieurs couleurs ne sont pas valides. Couleurs valides : bleu, orange, jaune.")

def main():
    image = load_image()
    couleurs_detecte = get_colors()

    # Convert the image from BGR to HSV
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    # Create masks for selected colors
    final_mask = None
    for color in couleurs_detecte:
        lower, upper = [np.array(x) for x in color_ranges[color]]
        mask = cv.inRange(hsv, lower, upper)
        if final_mask is None:
            final_mask = mask
        else:
            final_mask = cv.bitwise_or(final_mask, mask)

    # Apply morphological operations to clean the mask
    kernel = np.ones((10, 10), np.uint8)
    final_mask = cv.morphologyEx(final_mask, cv.MORPH_CLOSE, kernel)

    # Apply the final mask to the original image
    result = cv.bitwise_and(image, image, mask=final_mask)

    # Find contours in the mask
    contours, _ = cv.findContours(final_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    detected_balls = False
    for contour in contours:
        area = cv.contourArea(contour)
        if area > 150:
            M = cv.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                detected_balls = True
                print(f"Balle de couleur: {color}, Superficie: {area} pixels, Position du centre: ({cX}, {cY})")
                cv.circle(image, (cX, cY), 7, (0, 255, 0), -1)

    if not detected_balls:
        print("Aucune balle détectée.")

    # Display the original image with detected balls highlighted
    plt.figure(figsize=(10, 8))
    plt.imshow(cv.cvtColor(image, cv.COLOR_BGR2RGB))
    plt.title('Image avec balles détectées')
    plt.axis('off')
    plt.show()

if __name__ == "__main__":
    main()
