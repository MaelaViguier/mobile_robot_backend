import os
import json

MAX_MOT = 100
MAX_MOT_TAILLE = 20
MAX_DICO_TAILLE = 50

class Dictionnaire:
    def __init__(self, mots, taille, nom):
        self.mots = mots
        self.taille = taille
        self.nom = nom


def sauvegarder_dictionnaires(liste_dico):
    for dico in liste_dico:
        with open(f"{dico.nom}.json", "w") as file:
            json.dump({"mots": dico.mots, "taille": dico.taille}, file)


def charger_dictionnaires():
    liste_dico = []
    noms_dictionnaires = [
        "AvancerFR", "ReculerFR", "GaucheFR", "DroiteFR", "NegFR",
        "FrontEN", "BackEN", "LeftEN", "RightEN", "NegEN"
    ]

    for nom in noms_dictionnaires:
        mots = []
        taille = 0
        filename = f"{nom}.json"

        if os.path.exists("dico/"+filename):
            with open("dico/"+filename, "r") as file:
                data = json.load(file)
                mots = data["mots"]
                taille = data["taille"]

        liste_dico.append(Dictionnaire(mots, taille, nom))

    return liste_dico


def dans_le_dico(mot, dico):
    return mot in dico


def liste_mot(phrase):
    mots = [mot.lower() for mot in phrase.split()]
    return mots


def analyse_distance(mot):
    if mot.isdigit():
        return int(mot)
    return -1


def analyse_obstacle(mot):
    return mot.lower() == "obstacle"


def verifie_dico_liste(liste_dico, liste_de_mot, langue):
    parcour = []
    n = 0
    neg = False

    for mot in liste_de_mot:
        if langue == "FR":
            if mot in ["et", "puis"]:
                neg = False
            elif dans_le_dico(mot, liste_dico[4].mots):
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
                        if dans_le_dico(mot, dico.mots):
                            if dico.nom == "AvancerFR":
                                parcour.append("A")
                            elif dico.nom == "ReculerFR":
                                parcour.append("R")
                            elif dico.nom == "GaucheFR":
                                parcour.append("G")
                            elif dico.nom == "DroiteFR":
                                parcour.append("D")
                            n += 1
                            break

        elif langue == "EN":
            if mot in ["and", "then"]:
                neg = False
            elif dans_le_dico(mot, liste_dico[9].mots):
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
                        if dans_le_dico(mot, dico.mots):
                            if dico.nom == "FrontEN":
                                parcour.append("A")
                            elif dico.nom == "BackEN":
                                parcour.append("R")
                            elif dico.nom == "LeftEN":
                                parcour.append("G")
                            elif dico.nom == "RightEN":
                                parcour.append("D")
                            n += 1
                            break

    return parcour


def ajouter_mot_dico(liste_dico, langue):
    for i, dico in enumerate(liste_dico):
        print(f"{i + 1}. {dico.nom}")

    while True:
        if langue == "FR" :
            choix_dictionnaire = int(
                input("Choisissez le dictionnaire où ajouter le mot (entrez le numéro, pour quitter tapez -1) : "))
            if choix_dictionnaire == -1:
                return

            if 1 <= choix_dictionnaire <= len(liste_dico):
                print(f"Dictionnaire choisi pour ajout : {liste_dico[choix_dictionnaire - 1].nom}")
                nouveau_mot = input("Entrez un nouveau mot à ajouter aux dictionnaires : ")

                if liste_dico[choix_dictionnaire - 1].taille < MAX_DICO_TAILLE:
                    liste_dico[choix_dictionnaire - 1].mots.append(nouveau_mot)
                    liste_dico[choix_dictionnaire - 1].taille += 1
                    print(f"Mot ajouté au dictionnaire {liste_dico[choix_dictionnaire - 1].nom}")
                    sauvegarder_dictionnaires(liste_dico)
                else:
                    print(
                        f"Le dictionnaire {liste_dico[choix_dictionnaire - 1].nom} est plein, impossible d'ajouter le mot.")
            else:
                print("Choix de dictionnaire invalide.")
        if langue == "EN":
            choix_dictionnaire = int(
                input("Choose the dictionary to add the word to (enter the number, to exit type -1):"))
            if choix_dictionnaire == -1:
                return

            if 1 <= choix_dictionnaire <= len(liste_dico):
                print(f"Dictionary chosen for addition : {liste_dico[choix_dictionnaire - 1].nom}")
                nouveau_mot = input("Enter a new word to add to the dictionaries : ")

                if liste_dico[choix_dictionnaire - 1].taille < MAX_DICO_TAILLE:
                    liste_dico[choix_dictionnaire - 1].mots.append(nouveau_mot)
                    liste_dico[choix_dictionnaire - 1].taille += 1
                    print(f"Word added to dictionary {liste_dico[choix_dictionnaire - 1].nom}")
                    sauvegarder_dictionnaires(liste_dico)
                else:
                    print(f"The dictionary {liste_dico[choix_dictionnaire - 1].nom} is full, cannot add the word.")
            else:
                print("Invalid dictionary choice.")


def supprimer_mot_dico(liste_dico, langue):
    for i, dico in enumerate(liste_dico):
        print(f"{i + 1}. {dico.nom}")
    while True:
        if langue == "FR" :
            choix_dictionnaire = int(
                input("Choisissez le dictionnaire où supprimer un mot (entrez le numéro, pour quitter tapez -1) : "))
            if choix_dictionnaire == -1:
                return

            if 1 <= choix_dictionnaire <= len(liste_dico):
                if liste_dico[choix_dictionnaire - 1].taille == 0:
                    print(f"Le dictionnaire {liste_dico[choix_dictionnaire - 1].nom} est vide, aucun mot à supprimer.")
                    return

                print(f"Contenu du dictionnaire {liste_dico[choix_dictionnaire - 1].nom} :")
                for i, mot in enumerate(liste_dico[choix_dictionnaire - 1].mots):
                    print(f"{i + 1}. {mot}")

                while True:
                    choix_mot = int(input("Choisissez le mot à supprimer (entrez le numéro, pour quitter tapez -1) : "))
                    if choix_mot == -1:
                        return

                    if 1 <= choix_mot <= len(liste_dico[choix_dictionnaire - 1].mots):
                        mot_supprime = liste_dico[choix_dictionnaire - 1].mots.pop(choix_mot - 1)
                        liste_dico[choix_dictionnaire - 1].taille -= 1
                        print(f"Mot \"{mot_supprime}\" supprimé du dictionnaire {liste_dico[choix_dictionnaire - 1].nom}")
                        sauvegarder_dictionnaires(liste_dico)
                        break
                    else:
                        print("Choix de mot invalide.")
            else:
                print("Choix de dictionnaire invalide.")
        if langue == "EN":
            choix_dictionnaire = int(input("Choose the dictionary to delete a word from (enter the number, to exit type -1) : "))
            if choix_dictionnaire == -1:
                return

            if 1 <= choix_dictionnaire <= len(liste_dico):
                if liste_dico[choix_dictionnaire - 1].taille == 0:
                    print(f"The dictionary {liste_dico[choix_dictionnaire - 1].nom} is empty, no words to delete.")
                    return

                print(f"Dictionary content {liste_dico[choix_dictionnaire - 1].nom} :")
                for i, mot in enumerate(liste_dico[choix_dictionnaire - 1].mots):
                    print(f"{i + 1}. {mot}")

                while True:
                    choix_mot = int(input("Choose the word to delete (enter the number, to exit type -1) : "))
                    if choix_mot == -1:
                        return

                    if 1 <= choix_mot <= len(liste_dico[choix_dictionnaire - 1].mots):
                        mot_supprime = liste_dico[choix_dictionnaire - 1].mots.pop(choix_mot - 1)
                        liste_dico[choix_dictionnaire - 1].taille -= 1
                        print(f"Word \"{mot_supprime}\" removed from dictionary {liste_dico[choix_dictionnaire - 1].nom}")
                        sauvegarder_dictionnaires(liste_dico)
                        break
                    else:
                        print("Invalid word choice.")
            else:
                print("Invalid dictionary choice.")


def afficher_contenu_dictionnaire(liste_dico, langue):
    if langue == "FR":
        print("Liste des dictionnaires disponibles :")
        for i, dico in enumerate(liste_dico):
            print(f"{i + 1}. {dico.nom}")

        while True:
            choix_dictionnaire = int(input("Choisissez le dictionnaire dont vous voulez afficher le contenu (entrez le numéro, pour quitter tapez -1) : "))
            if choix_dictionnaire == -1:
                return
            if 1 <= choix_dictionnaire <= len(liste_dico):
                dico_selectionne = liste_dico[choix_dictionnaire - 1]
                print(f"Contenu du dictionnaire {dico_selectionne.nom} :")
                if dico_selectionne.taille == 0:
                    print("Le dictionnaire est vide.")
                else:
                    for mot in dico_selectionne.mots:
                        print(mot)
                input("Appuyez sur Entrée pour continuer...")
                return  # Sortir après l'affichage du contenu du dictionnaire sélectionné
            else:
                print("Choix de dictionnaire invalide.")

    elif langue == "EN":
        print("List of available dictionaries :")
        for i, dico in enumerate(liste_dico):
            print(f"{i + 1}. {dico.nom}")

        while True:
            choix_dictionnaire = int(input("Choose the dictionary whose contents you want to display (enter the number, to exit type -1):"))
            if choix_dictionnaire == -1:
                return
            if 1 <= choix_dictionnaire <= len(liste_dico):
                dico_selected = liste_dico[choix_dictionnaire - 1]
                print(f"Dictionary content {dico_selected.nom} :")
                if dico_selected.taille == 0:
                    print("The dictionary is empty.")
                else:
                    for mot in dico_selected.mots:
                        print(mot)
                input("Press Enter to continue...")
                return  # Exit after displaying the content of the selected dictionary
            else:
                print("Invalid dictionary choice.")


def conversion_text_commande(langue):
    textes_menu_fr = {
        0: "Bienvenue dans le programme de traitement des commandes textuelles.",
        1: "Entrer une commande",
        2: "Ajouter un mot aux dictionnaires",
        3: "Supprimer un mot des dictionnaires",
        4: "Afficher le contenu d'un dictionnaire",
        5: "Quitter"
    }
    textes_menu_en = {
        0: "Welcome to the text command processing program.",
        1: "Enter a command",
        2: "Add a word to dictionaries",
        3: "Remove a word from dictionaries",
        4: "Display the content of a dictionary",
        5: "Quit"
    }

    liste_dico = charger_dictionnaires()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        if langue == "FR":
            textes_menu = textes_menu_fr
            for i in range(0, 6):
                print(f"{i}. {textes_menu[i]}")
            choix_menu = int(input("Que souhaitez-vous faire ? "))
            if choix_menu == 1:
                phrase = input("Entrez votre commande textuelle : ")
                mots = liste_mot(phrase)
                parcour = verifie_dico_liste(liste_dico, mots, langue)
                print("Parcours généré :", parcour)
                input("Appuyez sur Entrée pour continuer...")
            elif choix_menu == 2:
                ajouter_mot_dico(liste_dico, langue)
            elif choix_menu == 3:
                supprimer_mot_dico(liste_dico, langue)
            elif choix_menu == 4:
                afficher_contenu_dictionnaire(liste_dico,langue)
            elif choix_menu == 5:
                print("Merci d'avoir utilisé le programme. À bientôt !")
                break
            else:
                print("Choix invalide. Veuillez sélectionner une option valide.")

        elif langue == "EN":
            textes_menu = textes_menu_en
            for i in range(0, 6):
                print(f"{i}. {textes_menu[i]}")
            choix_menu = int(input("What do you want to do ? "))
            if choix_menu == 1:
                phrase = input("Enter your text command : ")
                mots = liste_mot(phrase)
                parcour = verifie_dico_liste(liste_dico, mots, langue)
                print("Generated route :", parcour)
                input("Press Enter to continue ...")
            elif choix_menu == 2:
                ajouter_mot_dico(liste_dico, langue)
            elif choix_menu == 3:
                supprimer_mot_dico(liste_dico, langue)
            elif choix_menu == 4:
                afficher_contenu_dictionnaire(liste_dico, langue)
            elif choix_menu == 5:
                print("Thank you for using the program. See you soon !")
                break
            else:
                print("Invalid choice. Please select a valid option.")



if __name__ == "__main__":
    print("Welcome to the text order processing program.")
    print("Please select the language :")
    print("1. Français")
    print("2. English")
    choix_langue = int(input("Choose language (1 or 2) : "))
    langue = "FR" if choix_langue == 1 else "EN"

    conversion_text_commande(langue)