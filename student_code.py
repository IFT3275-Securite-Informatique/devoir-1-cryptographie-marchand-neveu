import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import random
import math
from textblob import TextBlob
from pattern.fr import lexicon

def load_text_ids():
    # L'URL de la page contenant la liste des livres en français
    url = "https://www.gutenberg.org/browse/languages/fr"

    # Envoyer une requête GET pour récupérer le contenu de la page
    response = requests.get(url)

    # Vérifier si la requête a réussi
    if response.status_code == 200:
        # Analyser le contenu de la page HTML avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Trouver tous les liens qui contiennent "/ebooks/"
        links = soup.find_all('a', href=True)

        # Extraire les IDs des livres à partir des liens
        book_ids = []
        for link in links:
            href = link['href']
            if href.startswith("/ebooks/"):
                # Extraire l'ID après "/ebooks/"
                book_id = href.split("/ebooks/")[1]
                book_ids.append(book_id)
        print("Nombre de textes à récupérer : ")
        print(len(book_ids))
        return book_ids
    else:
        print(f"Erreur lors de la récupération de la page : {response.status_code}")
        return None

def load_texts(books_ids):
    number_text_train = 50
    books_ids = books_ids[:number_text_train]

    # Dictionnaire pour compter les occurrences des caracteres (lettres et paires de lettres)
    carac_counts = defaultdict(int)

    total_symbol = 0
    i=0
    caracteres = ['z', 't', 'S', 'v', 'a', 'À', 'd', '•', 'u', 'o', 'G', '!', 'D', '_', ')', 'M', 's', 'E', 'I', 'R', 'F', '7', '\ufeff', '8', 'ï', 'A', 'y', '3', 'p', 'û', '‘', '/', '«', ',', 'c', '[', '#', 'V', ' ', 'Z', '2', '5', 'l', 'î', 'Ê', 'Â', 'q', 'B', '\r', '…', "'", 'Î', ']', 'g', '“', 'h', '-', 'x', '?', 'P', 'i', '0', 'è', 'É', '—', 'L', 'ë', 'é', '”', 'j', 'H', 'K', 'ç', ';', 'º', '%', 'k', ':', 'â', 'Q', '$', 'ê', 'X', 'f', 'Y', '(', 'N', 'J', 'ô', '°', '4', 'à', 'Ç', '9', '»', '’', 'W', '1', '.', 'O', 'e', 'b', 'm', 'r', '\n', 'T', 'È', '*', 'w', 'U', 'ù', 'n', 'C', '™', '6']
    bicaracteres = ['e ', 's ', 't ', 'es', ' d', '\r\n', 'en', 'qu', ' l', 're', ' p', 'de', 'le', 'nt', 'on', ' c', ', ', ' e', 'ou', ' q', ' s', 'n ', 'ue', 'an', 'te', ' a', 'ai', 'se', 'it', 'me', 'is', 'oi', 'r ', 'er', ' m', 'ce', 'ne', 'et', 'in', 'ns', ' n', 'ur', 'i ', 'a ', 'eu', 'co', 'tr', 'la', 'ar', 'ie', 'ui', 'us', 'ut', 'il', ' t', 'pa', 'au', 'el', 'ti', 'st', 'un', 'em', 'ra', 'e,', 'so', 'or', 'l ', ' f', 'll', 'nd', ' j', 'si', 'ir', 'e\r', 'ss', 'u ', 'po', 'ro', 'ri', 'pr', 's,', 'ma', ' v', ' i', 'di', ' r', 'vo', 'pe', 'to', 'ch', '. ', 've', 'nc', 'om', ' o', 'je', 'no', 'rt', 'à ', 'lu', "'e", 'mo', 'ta', 'as', 'at', 'io', 's\r', 'sa', "u'", 'av', 'os', ' à', ' u', "l'", "'a", 'rs', 'pl', 'é ', '; ', 'ho', 'té', 'ét', 'fa', 'da', 'li', 'su', 't\r', 'ée', 'ré', 'dé', 'ec', 'nn', 'mm', "'i", 'ca', 'uv', '\n\r', 'id', ' b', 'ni', 'bl']

    full_text = ""

    for book_id in books_ids:
        # Construire l'URL du livre
        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        
        # Envoyer une requête GET pour récupérer le texte du livre
        response = requests.get(url)
        
        if response.status_code == 200:
            # Ajouter le texte récupéré à full_text
            text = response.text
            full_text += text
            # Parcourir le texte pour compter les lettres et les bigrammes
            while i < len(text):
            # Vérifie les paires de caractères
                if i + 1 < len(text):
                    pair = text[i] + text[i + 1]
                    if pair in bicaracteres:
                        carac_counts[pair] += 1
                        total_symbol +=1
                        i += 2  # Sauter les deux caractères utilisés
                        continue

                # Vérifie le caractère seul
                if text[i] in caracteres:
                    carac_counts[text[i]] += 1
                    total_symbol +=1

                else:
                    # Conserve le caractère tel quel si non trouvé
                    total_symbol +=1
                i += 1
        else:
            print(f"Erreur lors de la récupération du livre {book_id}.")
    return carac_counts, total_symbol

# Fonction pour calculer la fréquence des symboles dans une chaîne chiffrée
def freq_symbol_C(C):
    len_c = len(C)

    freq_symbol_c = defaultdict(int)
    n_symbols = len_c//8
    
    for i in range(0, len_c - 7, 8):
        freq_symbol_c[C[i:i+8]] += 1
    
    for cle in freq_symbol_c:
        freq_symbol_c[cle] /= n_symbols
        
    return freq_symbol_c

# Applique la substitution au texte chiffré binaire
def appliquer_substitution_binaire(texte_binaire, substitution):
    texte_dechiffre = ""
    for i in range(0, len(texte_binaire), 8):
        octet = texte_binaire[i:i+8]  # Extrait un octet (8 bits)
        lettre = substitution.get(octet, octet)  # Remplace l'octet par la lettre correspondante
        texte_dechiffre += lettre  # Ajoute la lettre déchiffrée au texte final
    return texte_dechiffre

# Comparer le texte déchiffré aux mots connus du dictionnaire français
def comparer_texte_avec_dictionnaire(texte_dechiffre):
    mots = texte_dechiffre.split()  # Découpe le texte en mots
    mots_a_verifier = mots[:150]  # Sélectionner les 150 premiers mots
    mots_valides = [
        mot for mot in mots_a_verifier 
        if len(mot) > 2 and mot.lower() in lexicon  # Ignore les mots de 1 ou 2 lettres
    ]  
    proportion_valides = len(mots_valides) / len(mots_a_verifier) if mots_a_verifier else 0  # Calcul de la proportion
    return proportion_valides, mots_valides  # Retourne la proportion et les mots valides

# Génère plusieurs permutations initiales pour optimiser le décryptage
def generer_permutations_initiales_optimisees(texte_chiffre, frequence_chiffre, frequence_francais, nombre_initialisations=10):
    lettres_chiffrees = list(frequence_chiffre.keys())
    meilleure_permutation = None
    meilleur_score = 0
    mots_valides = []

    for _ in range(nombre_initialisations):
        # Générer une permutation basée sur les fréquences
        permutation = sorted(frequence_francais, key=lambda x: frequence_francais[x], reverse=True)
        random.shuffle(permutation[0:int(0.2 * len(permutation))])  # Ajouter un peu de hasard

        substitution = dict(zip(lettres_chiffrees, permutation))
        texte_dechiffre = appliquer_substitution_binaire(texte_chiffre, substitution)

        score, mots_valides_temp = comparer_texte_avec_dictionnaire(texte_dechiffre)

        if score > meilleur_score:
            meilleure_permutation = permutation
            meilleur_score = score
            mots_valides = mots_valides_temp  # Conserver les mots valides

    return meilleure_permutation, meilleur_score, mots_valides


# Applique le recuit simulé pour rechercher la meilleure permutation de décryptage
def recuit_simule_hybride(texte_chiffre, frequence_chiffre, frequence_francais, temperature=1500, cooling_rate=0.95, iterations=50, parallel_instances=100):
    # Initialiser les instances parallèles avec des permutations uniques
    instances = [generer_permutations_initiales_optimisees(texte_chiffre, frequence_chiffre, frequence_francais) for _ in range(parallel_instances)]
    
    best_overall_permutation = None
    best_overall_score = 0
    mots_valides_final = None  # Variable pour stocker les mots valides de la meilleure permutation
    
    for i in range(iterations):
        for j, (permutation, best_score, mots_valides) in enumerate(instances):
            # Appliquer la permutation actuelle
            substitution = dict(zip(list(frequence_chiffre.keys()), permutation))
            texte_dechiffre = appliquer_substitution_binaire(texte_chiffre, substitution)
            score, mots_valides = comparer_texte_avec_dictionnaire(texte_dechiffre)

            # Si un meilleur score est trouvé, on met à jour la permutation et les mots valides associés
            if score > best_score:
                best_score = score
                instances[j] = (permutation[:], best_score, mots_valides)  # Conserver les mots valides pour cette permutation

            # Mutation adaptative
            if temperature > 0 and random.random() < math.exp((score - best_score) / temperature):
                idx1, idx2 = random.sample(range(len(permutation)), 2)
                permutation[idx1], permutation[idx2] = permutation[idx2], permutation[idx1]

            # Échange entre les instances de temps en temps
            if i % 50 == 0 and j < parallel_instances - 1:
                # Échanger avec une instance voisine
                instances[j], instances[j + 1] = instances[j + 1], instances[j]

        # Mise à jour de la meilleure solution globale
        for perm, score, mots_valides in instances:
            if score > best_overall_score:
                best_overall_permutation = perm
                best_overall_score = score
                mots_valides_final = mots_valides  # Mettre à jour les mots valides de la meilleure permutation

        # Ajustement dynamique de la température
        if iterations > 0:
            temperature = max(temperature * cooling_rate * (1 - (i / iterations)), 1)
        else:
            temperature *= cooling_rate  # Retour sans ajustement

    # Solution finale
    substitution = dict(zip(list(frequence_chiffre.keys()), best_overall_permutation))
    final_text = appliquer_substitution_binaire(texte_chiffre, substitution)

    return best_overall_permutation, best_overall_score, mots_valides_final, final_text


# Fonction principale de déchiffrement
def decrypt(C):
    M=""
  
    book_ids = load_text_ids()
    freq_symbol, total_symbol = load_texts(book_ids) # quantité de chaque symbole et nombre de symboles total
  
    for cle in freq_symbol:
        freq_symbol[cle] /= total_symbol # fréquence de chaque symbole dans un grand nombre de texte
    sorted_freq_symbol = dict(sorted(freq_symbol.items(), key=lambda item: item[1], reverse=True)) # fréquence des symboles dans les 50 textes par ordre décroissant
    
    freq_symbol_c = freq_symbol_C(C)
    sorted_freq_symbol_c = dict(sorted(freq_symbol_c.items(), key=lambda item: item[1], reverse=True)) # fréquence des symboles dans C par ordre décroissant
    
    # Appliquer la fonction de recuit simulé pour obtenir la meilleure permutation
    meilleure_permutation, meilleur_score, mots_valides, meilleur_texte = recuit_simule_hybride(C, sorted_freq_symbol_c, sorted_freq_symbol)
    M = meilleur_texte
    # print(f"Meilleur score: {meilleur_score}")
    # print(f"Meilleure permutation: {meilleure_permutation}")
    # print(f"Mots valides: {mots_valides}")
    # print(f"Meilleur texte: {meilleur_texte}")

    return M
