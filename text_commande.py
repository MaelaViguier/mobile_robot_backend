import os
import json
import time
import datetime

MAX_MOT = 100
MAX_MOT_TAILLE = 20
MAX_DICO_TAILLE = 50

def crea_fichlog() :
    aujourd_hui = datetime.date.today()
    maintenant = datetime.datetime.now()
    heure = maintenant.time()
    formatte = heure.strftime("%H:%M:%S")
    fic = open(f"{aujourd_hui}.txt","w")
    fic.write(f"FICHIER LOG DU {aujourd_hui} A {formatte} : \n\n")
    fic.close
    return fic

def ecrir_log(text) :
    maintenant = datetime.datetime.now()
    formatte = maintenant.strftime("%Y-%m-%d %H:%M:%S")
    fic.write(f"{formatte} : {text}\n")


class Dictionnaire:
    def __init__(self, mots, taille, nom):
        self.mots = mots
        self.taille = taille
        self.nom = nom

def send_command(command):
    """ Send commands to the serial port. """
    #ser.write(command.encode())
    print(f"Sent command: {command}")

def sauvegarder_dictionnaires(liste_dico, nom_fichier):
    data_to_save = {}
    for dico in liste_dico:
        data_to_save[dico.nom] = {"mots": dico.mots, "taille": dico.taille}

    with open(nom_fichier, "w") as file:
        json.dump(data_to_save, file)


def charger_dictionnaires():
    liste_dico = []

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

    for mots, taille, nom in dictionnaires:
        liste_dico.append(Dictionnaire(list(mots), taille, nom))

    noms_dictionnaires = [
        "AvancerFR", "ReculerFR", "GaucheFR", "DroiteFR", "NegFR",
        "FrontEN", "BackEN", "LeftEN", "RightEN", "NegEN"
    ]

    for nom in noms_dictionnaires:
        filename = f"{nom}.json"

        if os.path.exists(filename):
            with open(filename, "r") as file:
                data = json.load(file)
                mots = data["mots"]
                taille = data["taille"]
                liste_dico.append(Dictionnaire(list(mots), taille, nom))

    return liste_dico

def charger_dictionnaires_depuis_fichier(nom_fichier):
    liste_dico = []

    with open(nom_fichier, "r") as f:
        json_data = f.read()
        data = json.loads(json_data)

        for nom_dico, info_dico in data.items():
            mots = info_dico["mots"]
            taille = info_dico["taille"]
            dico = Dictionnaire(mots, taille, nom_dico)
            liste_dico.append(dico)
    print(data)
    return liste_dico

def dans_le_dico(mot, dico):
    return mot in dico.mots


def liste_mot(phrase):
    mots = [mot.lower() for mot in phrase.split()]
    return mots


def analyse_distance(mot):
    if mot.isdigit():
        return int(mot)
    return -1


def analyse_obstacle(mot):
    return mot.lower() == "obstacle"

def envoie_info(parcour):
    for caractere in parcour:
        if caractere.isupper():
            duree_envoie = 2
        elif caractere.islower():
            duree_envoie = 1
        else:
            continue

        debut = time.time()
        while time.time() - debut < duree_envoie:
            send_command(caractere.upper())
        send_command("stop")

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

        if langue == "FR":
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
        elif langue == "EN":
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

    envoie_info(parcour)
    return parcour


def secure_input(entr):
    while True:
        sort = input(entr)
        if sort.isdigit():
            return int(sort)
        else:
            print("Veuillez entrer un numéro entier valide.")
            ecrir_log("ConversionTextCommande : Securité saisie : ERREUR saisie INCORRECT .......")
def ajouter_mot_dico(liste_dico, langue):
    while True:
        if langue == "FR":
            dictionnaires_fr = [dico for dico in liste_dico if dico.nom.endswith("FR")]
            if not dictionnaires_fr:
                print("Aucun dictionnaire français disponible.")
                ecrir_log("ConversionTextCommande : Ajouter un mot : ERREUR aucun Dico disponible .......")
                return

            print("Liste des dictionnaires français disponibles :")
            for i, dico in enumerate(dictionnaires_fr):
                print(f"{i + 1}. {dico.nom}")
            ecrir_log("ConversionTextCommande : Ajouter un mot : Affichage des Dico")
            choix_dictionnaire = secure_input("Choisissez le dictionnaire où ajouter un mot (entrez le numéro, pour quitter tapez 0) : ")
            if choix_dictionnaire == 0:
                ecrir_log("ConversionTextCommande : Ajouter un mot : Sortie de Ajouter un mot.")
                return

            if 1 <= choix_dictionnaire <= len(dictionnaires_fr):
                dico_selectionne = dictionnaires_fr[choix_dictionnaire - 1]
                print(f"Dictionnaire choisi pour ajout : {dico_selectionne.nom}")

                nouveau_mot = input("Entrez un nouveau mot à ajouter aux dictionnaires : ")

                if len(nouveau_mot.strip()) == 0:
                    print("Le mot ne peut pas être vide.")
                    ecrir_log("ConversionTextCommande : Ajouter un mot : ERREUR mot VIDE .......")
                    continue

                if dico_selectionne.taille < MAX_DICO_TAILLE:
                    dico_selectionne.mots.append(nouveau_mot)
                    dico_selectionne.taille += 1
                    print(f"Mot ajouté au dictionnaire {dico_selectionne.nom}")
                    sauvegarder_dictionnaires(liste_dico, "dictionnaires_globaux.json")
                    ecrir_log(f"ConversionTextCommande : Ajouter un mot : Mot ajouté au Dico : {dico_selectionne.nom}")
                else:
                    print(f"Le dictionnaire {dico_selectionne.nom} est plein, impossible d'ajouter le mot.")
                    ecrir_log(f"ConversionTextCommande : Ajouter un mot : Le dictionnaire {dico_selectionne.nom} est plein, impossible d'ajouter le mot.")
            else:
                print("Choix de dictionnaire invalide.")
                ecrir_log("ConversionTextCommande : Ajouter un mot : ERREUR choix du Dico INVALIDE .......")
        elif langue == "EN":
            dictionnaires_en = [dico for dico in liste_dico if dico.nom.endswith("EN")]
            if not dictionnaires_en:
                print("No English dictionaries available.")
                ecrir_log("ConversionTextCommande : Ajouter un mot : ERREUR aucun Dico disponible .......")
                return

            print("List of available English dictionaries :")
            for i, dico in enumerate(dictionnaires_en):
                print(f"{i + 1}. {dico.nom}")
            ecrir_log("ConversionTextCommande : Ajouter un mot : Affichage des Dico")
            choix_dictionnaire = secure_input("Choose the dictionary to add a word from (enter the number, to exit type 0) : ")
            if choix_dictionnaire == 0:
                ecrir_log("ConversionTextCommande : Ajouter un mot : Sortie de Ajouter un mot.")
                return

            if 1 <= choix_dictionnaire <= len(dictionnaires_en):
                dico_selected = dictionnaires_en[choix_dictionnaire - 1]
                print(f"Dictionary chosen for addition : {dico_selected.nom}")

                nouveau_mot = input("Enter a new word to add to the dictionaries : ")

                if len(nouveau_mot.strip()) == 0:
                    print("The word cannot be empty.")
                    ecrir_log("ConversionTextCommande : Ajouter un mot : ERREUR mot VIDE .......")
                    continue

                if dico_selected.taille < MAX_DICO_TAILLE:
                    dico_selected.mots.append(nouveau_mot)
                    dico_selected.taille += 1
                    print(f"Word added to dictionary {dico_selected.nom}")
                    sauvegarder_dictionnaires(liste_dico, "dictionnaires_globaux.json")
                    ecrir_log(f"ConversionTextCommande : Ajouter un mot : Mot ajouté au Dico : {dico_selected.nom}")
                else:
                    print(f"The dictionary {dico_selected.nom} is full, cannot add the word.")
                    ecrir_log(f"ConversionTextCommande : Ajouter un mot : ERREUR Le dictionnaire {dico_selected.nom} est plein, impossible d'ajouter le mot.")
            else:
                print("Invalid dictionary choice.")
                ecrir_log("ConversionTextCommande : Ajouter un mot : ERREUR choix du Dico INVALIDE .......")
def supprimer_mot_dico(liste_dico, langue):
    while True:
        if langue == "FR":
            dictionnaires_fr = [dico for dico in liste_dico if dico.nom.endswith("FR")]
            if not dictionnaires_fr:
                print("Aucun dictionnaire français disponible.")
                ecrir_log("ConversionTextCommande : Supprimer un mot : ERREUR aucun Dico disponible .......")
                return

            print("Liste des dictionnaires français disponibles :")
            for i, dico in enumerate(dictionnaires_fr):
                print(f"{i + 1}. {dico.nom}")
            ecrir_log("ConversionTextCommande : Supprimer un mot : Affichage des Dico")
            choix_dictionnaire = secure_input("Choisissez le dictionnaire où supprimer un mot (entrez le numéro, pour quitter tapez 0) : ")
            if choix_dictionnaire == 0:
                ecrir_log("ConversionTextCommande : Supprimer un mot : Sortie de la Suppression de mot")
                return

            if 1 <= choix_dictionnaire <= len(dictionnaires_fr):
                dico_selectionne = dictionnaires_fr[choix_dictionnaire - 1]
                if dico_selectionne.taille == 0:
                    print(f"Le dictionnaire {dico_selectionne.nom} est vide, aucun mot à supprimer.")
                    ecrir_log(f"ConversionTextCommande : Supprimer un mot : ERREUR Le dictionnaire {dico_selectionne.nom} est vide, aucun mot à supprimer .......")
                    continue

                print(f"Contenu du dictionnaire {dico_selectionne.nom} :")
                for i, mot in enumerate(dico_selectionne.mots):
                    print(f"{i + 1}. {mot}")
                ecrir_log("ConversionTextCommande : Supprimer un mot : Affichage du contenu des Dico.")
                while True:
                    choix_mot = secure_input("Choisissez le mot à supprimer (entrez le numéro, pour quitter tapez 0) : ")
                    if choix_mot == 0:
                        ecrir_log("ConversionTextCommande : Supprimer un mot : Sortie de la suppression des mots.")
                        return

                    if 1 <= choix_mot <= len(dico_selectionne.mots):
                        mot_supprime = dico_selectionne.mots.pop(choix_mot - 1)
                        dico_selectionne.taille -= 1
                        print(f"Mot \"{mot_supprime}\" supprimé du dictionnaire {dico_selectionne.nom}")
                        sauvegarder_dictionnaires(liste_dico, "dictionnaires_globaux.json")
                        ecrir_log(f"ConversionTextCommande : Supprimer un mot : Mot \"{mot_supprime}\" supprimé du dictionnaire {dico_selectionne.nom}")
                        break
                    else:
                        print("Choix de mot invalide.")
                        ecrir_log("ConversionTextCommande : Supprimer un mot : ERREUR choix du mot INVALIDE .........")
            else:
                print("Choix de dictionnaire invalide.")
                ecrir_log("ConversionTextCommande : Supprimer un mot : ERREUR choix du Dico INVALIDE .........")
        elif langue == "EN":
            dictionnaires_en = [dico for dico in liste_dico if dico.nom.endswith("EN")]
            if not dictionnaires_en:
                print("No English dictionaries available.")
                ecrir_log("ConversionTextCommande : Supprimer un mot : ERREUR aucun Dico disponible .......")
                return

            print("List of available English dictionaries :")
            for i, dico in enumerate(dictionnaires_en):
                print(f"{i + 1}. {dico.nom}")
            ecrir_log("ConversionTextCommande : Supprimer un mot : Affichage des Dico")
            choix_dictionnaire = secure_input("Choose the dictionary to delete a word from (enter the number, to exit type 0) : ")
            if choix_dictionnaire == 0:
                ecrir_log("ConversionTextCommande : Supprimer un mot : Sortie de la Suppression de mot")
                return

            if 1 <= choix_dictionnaire <= len(dictionnaires_en):
                dico_selected = dictionnaires_en[choix_dictionnaire - 1]
                if dico_selected.taille == 0:
                    print(f"The dictionary {dico_selected.nom} is empty, no words to delete.")
                    ecrir_log(f"ConversionTextCommande : Supprimer un mot : ERREUR Le dictionnaire {dico_selected.nom} est vide, aucun mot à supprimer .......")
                    continue

                print(f"Dictionary content {dico_selected.nom} :")
                for i, mot in enumerate(dico_selected.mots):
                    print(f"{i + 1}. {mot}")
                ecrir_log("ConversionTextCommande : Supprimer un mot : Affichage du contenu des Dico.")
                while True:
                    choix_mot = secure_input("Choose the word to delete (enter the number, to exit type 0) : ")
                    if choix_mot == 0:
                        ecrir_log("ConversionTextCommande : Supprimer un mot : Sortie de la suppression des mots.")
                        return

                    if 1 <= choix_mot <= len(dico_selected.mots):
                        mot_supprime = dico_selected.mots.pop(choix_mot - 1)
                        dico_selected.taille -= 1
                        print(f"Word \"{mot_supprime}\" removed from dictionary {dico_selected.nom}")
                        sauvegarder_dictionnaires(liste_dico, "dictionnaires_globaux.json")
                        ecrir_log(f"ConversionTextCommande : Supprimer un mot : Mot \"{mot_supprime}\" supprimé du dictionnaire {dico_selected.nom}")
                        break
                    else:
                        print("Invalid word choice.")
                        ecrir_log("ConversionTextCommande : Supprimer un mot : ERREUR choix du mot INVALIDE .........")
            else:
                print("Invalid dictionary choice.")
                ecrir_log("ConversionTextCommande : Supprimer un mot : ERREUR choix du Dico INVALIDE .........")


def afficher_contenu_dictionnaire(liste_dico, langue):

    if langue == "FR":
        dictionnaires_fr = [dico for dico in liste_dico if dico.nom.endswith("FR")]
        if not dictionnaires_fr:
            print("Aucun dictionnaire français disponible.")
            ecrir_log("ConversionTextCommande : Affichage Dico : ERREUR pas de Dico disponible .........")
            return

        print("Liste des dictionnaires français disponibles :")
        for i, dico in enumerate(dictionnaires_fr):
            print(f"{i + 1}. {dico.nom}")
        ecrir_log("ConversionTextCommande : Affichage Dico : Affichage de la liste des Dico.")
        while True:
            choix_dictionnaire = int(input("Choisissez le dictionnaire dont vous voulez afficher le contenu (entrez le numéro, pour quitter tapez 0) : "))
            if choix_dictionnaire == 0:
                ecrir_log("ConversionTextCommande : Affichage Dico : Sortie de l'affichage des Dico")
                return
            if 1 <= choix_dictionnaire <= len(dictionnaires_fr):
                dico_selectionne = dictionnaires_fr[choix_dictionnaire - 1]
                print(f"Contenu du dictionnaire {dico_selectionne.nom} :")
                ecrir_log(f"ConversionTextCommande : Affichage Dico : Affichage de : {dico_selectionne.nom}")
                if dico_selectionne.taille == 0:
                    print("Le dictionnaire est vide.")
                    ecrir_log("ConversionTextCommande : Affichage Dico : Dico VIDE")
                else:
                    for mot in dico_selectionne.mots:
                        print(mot)
                input("Appuyez sur Entrée pour continuer...")
                return
            else:
                print("Choix de dictionnaire invalide.")
                ecrir_log("ConversionTextCommande : Affichage Dico : ERREUR choix Dico INVALIDE .........")

    elif langue == "EN":
        dictionnaires_en = [dico for dico in liste_dico if dico.nom.endswith("EN")]
        if not dictionnaires_en:
            print("No English dictionaries available.")
            ecrir_log(f"ConversionTextCommande : Affichage Dico : ERREUR pas de Dico disponible .........")
            return

        print("List of available English dictionaries :")
        for i, dico in enumerate(dictionnaires_en):
            print(f"{i + 1}. {dico.nom}")
        ecrir_log("ConversionTextCommande : Affichage Dico : Affichage de la liste des Dico.")
        while True:
            choix_dictionnaire = int(input("Choose the dictionary whose contents you want to display (enter the number, to exit type 0):"))
            if choix_dictionnaire == 0:
                ecrir_log("ConversionTextCommande : Affichage Dico : Sortie de l'affichage des Dico")
                return

            if 1 <= choix_dictionnaire <= len(dictionnaires_en):
                dico_selectionne = dictionnaires_en[choix_dictionnaire - 1]
                print(f"Dictionary content {dico_selectionne.nom} :")
                ecrir_log(f"ConversionTextCommande : Affichage Dico : Affichage de : {dico_selectionne.nom}")
                if dico_selectionne.taille == 0:
                    print("The dictionary is empty.")
                    ecrir_log("ConversionTextCommande : Affichage Dico : Dico VIDE")
                else:
                    for mot in dico_selectionne.mots:
                        print(mot)
                input("Press Enter to continue...")
                return
            else:
                print("Invalid dictionary choice.")
                ecrir_log("ConversionTextCommande : Affichage Dico : ERREUR choix Dico INVALIDE .........")


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

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        if langue == "FR":
            textes_menu = textes_menu_fr
            while True:
                for i in range(0, 6):
                    print(f"{i}. {textes_menu[i]}")
                choix_menu = input("\nQue souhaitez-vous faire ? ")

                if choix_menu.isdigit():
                    choix_menu = int(choix_menu)
                    if 1 <= choix_menu <= len(textes_menu):
                        break
                    else:
                        print("Choix invalide. Veuillez saisir un numéro correspondant à une option du menu.\n")
                        ecrir_log("ConversionTextCommande : ERREUR choix dans le menu, saisie INCORRECT ............")
                else:
                    print("Entrée invalide. S'il vous plait, entrez un nombre valide.\n")
            if choix_menu == 1:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Entrer une commande")
                phrase = input("Entrez votre commande textuelle : ")
                ecrir_log(f"ConversionTextCommande : Entrer une commande : Phrase entrée : {phrase}")
                mots = liste_mot(phrase)
                parcour = verifie_dico_liste(liste_dico, mots, langue)
                print("Parcours généré :", parcour)
                ecrir_log(f"ConversionTextCommande : Entrer une commande : Parcours généré : {parcour}")
                input("Appuyez sur Entrée pour continuer...")
            elif choix_menu == 2:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Ajouter un mot")
                ajouter_mot_dico(liste_dico, langue)
            elif choix_menu == 3:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Supprimer un mot")
                supprimer_mot_dico(liste_dico, langue)
            elif choix_menu == 4:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Affichage du Dico")
                afficher_contenu_dictionnaire(liste_dico, langue)
            elif choix_menu == 5:
                print("\nMerci d'avoir utilisé le programme. À bientôt !")
                ecrir_log("ConversionTextCommande : Choix dans le menu : Sortie du menu")
                break
            else:
                print("Choix invalide. Veuillez sélectionner une option valide.\n")
                ecrir_log("ConversionTextCommande : ERREUR choix dans le menu, saisie INCORRECT ............")
        elif langue == "EN":
            textes_menu = textes_menu_en
            while True:
                for i in range(0, 6):
                    print(f"{i}. {textes_menu[i]}")
                choix_menu = input("\nWhat do you want to do ? ")

                if choix_menu.isdigit():
                    choix_menu = int(choix_menu)
                    if 1 <= choix_menu <= len(textes_menu):
                        break
                    else:
                        print("Invalid choice. Please enter a number corresponding to a menu option.\n")
                        ecrir_log("ConversionTextCommande : ERREUR choix dans le menu, saisie INCORRECT ............")
                else:
                    print("Invalid input. Please enter a valid number.\n")
                    ecrir_log("ConversionTextCommande : ERREUR choix dans le menu, saisie INCORRECT ............")
            if choix_menu == 1:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Entrer une commande")
                phrase = input("Enter your text command : ")
                mots = liste_mot(phrase)
                parcour = verifie_dico_liste(liste_dico, mots, langue)
                print("Generated route :", parcour)
                input("Press Enter to continue ...")
            elif choix_menu == 2:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Ajouter un mot")
                ajouter_mot_dico(liste_dico, langue)
            elif choix_menu == 3:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Supprimer un mot")
                supprimer_mot_dico(liste_dico, langue)
            elif choix_menu == 4:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Affichage du Dico")
                afficher_contenu_dictionnaire(liste_dico, langue)
            elif choix_menu == 5:
                ecrir_log("ConversionTextCommande : Choix dans le menu : Sortie du menu")
                print("\nThank you for using the program. See you soon !")
                break
            else:
                print("Invalid choice. Please select a valid option.\n")
                ecrir_log("ConversionTextCommande : ERREUR choix dans le menu, saisie INCORRECT ............")


if __name__ == "__main__":
    print("Welcome to the text order processing program.\n")
    langue = None

    while True:
        print("Please select the language :")
        print("1. Français")
        print("2. English")
        choix_langue = input("Choose language (1 or 2) : ")
        fic = crea_fichlog()
        if choix_langue == '1':
            langue = "FR"
            ecrir_log("ConversionTextCommande : Choix de la langue : FRANCAIS")
            break
        elif choix_langue == '2':
            langue = "EN"
            ecrir_log("ConversionTextCommande : Choix de la langue : ANGLAIS")
            break
        else:
            print("Invalid input. Please enter '1' for Français or '2' for English.")
            ecrir_log("ConversionTextCommande : ERREUR de la saisie de la langue ......")
    print(f"You have selected {langue} language.")
    if os.path.exists("dictionnaires_globaux.json") and os.path.isfile("dictionnaires_globaux.json") :
        liste_dico = charger_dictionnaires_depuis_fichier("dictionnaires_globaux.json")
        ecrir_log("ConversionTextCommande : Dico JSON déjà existant, actualisation du Dico JSON")
    else :
        liste_dico = charger_dictionnaires()
        ecrir_log("ConversionTextCommande : Dico JSON manquant, créastion du Dico")
    conversion_text_commande(langue)