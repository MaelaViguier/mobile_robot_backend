import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

# Charger l'image
image = cv.imread("images/IMG_5405.jpeg")

# Verification que l'image a été correctement chargée
if image is None:
    print("Impossible de charger l'image.")
    exit()

# Convertir l'image BGR en HSV
hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)

# Définir les plages de couleur bleu, l'orange et jaune en HSV
lower_blue = np.array([100, 100, 0])
upper_blue = np.array([140, 255, 255])

lower_orange = np.array([5, 50, 50])
upper_orange = np.array([10, 255, 255])

lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([30, 255, 255])

# Créer les masques pour chaque couleur
mask_blue = cv.inRange(hsv, lower_blue, upper_blue)
mask_orange = cv.inRange(hsv, lower_orange, upper_orange)
mask_yellow = cv.inRange(hsv, lower_yellow, upper_yellow)

# Combinez les masques pour obtenir un masque final
combi_mask = cv.bitwise_or(mask_blue, cv.bitwise_or(mask_orange, mask_yellow))

# Appliquer des opérations morphologiques pour combler les trous
noyau = np.ones((10, 10), np.uint8)
final_mask = cv.morphologyEx(combi_mask, cv.MORPH_CLOSE, noyau)

# Appliquer le masque Bitwise-AND à l'image originale
res = cv.bitwise_and(image, image, mask=final_mask)

# Trouver les contours pour chaque masque séparément
contours_blue, _ = cv.findContours(mask_blue, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
contours_orange, _ = cv.findContours(mask_orange, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
contours_yellow, _ = cv.findContours(mask_yellow, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

# Rassembler les contours au même endroit
contours = contours_blue + contours_orange + contours_yellow 

# Parcourir chaque contour pour identifier les balles et obtenir leur couleur, superficie et position
for contour in contours:
    # Calculer l'aire du contour
    area = cv.contourArea(contour)
    
    # Ignorer les contours trop petits
    if area > 150:  # Vous pouvez ajuster cette valeur selon vos besoins

        # Calculer le centre du cercle
        moments = cv.moments(contour)
        center = (int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"]))
            
        # Déterminer la couleur de la balle en fonction de la position de son centre
        color = None
        if mask_blue[center[1], center[0]] == 255:
            color = "Bleu"
        elif mask_orange[center[1], center[0]] == 255:
            color = "Orange"
        elif mask_yellow[center[1], center[0]] == 255:
            color = "Jaune"
            
        # Afficher les informations sur la balle détectée
        print("Balle de couleur:", color)
        print("Superficie:", area, "pixels")
        print("Position du centre:", center)
        print("----------------------")


# Dessiner les contours détectés sur l'image originale
cv.drawContours(image, contours, -1, (0, 255, 0), 2)

# Afficher l'image originale
plt.figure()
plt.imshow(cv.cvtColor(image, cv.COLOR_BGR2RGB))
plt.title('Image Originale')
plt.axis('off')
plt.show()

# Afficher le masque
plt.figure()
plt.imshow(final_mask)
plt.title('Masque')
plt.axis('off')  # Désactiver les axes
plt.show()

# Afficher le résultat du masque
plt.figure()
plt.imshow(res)
plt.title('Résultat du Masque')
plt.axis('off')  # Désactiver les axes
plt.show()

