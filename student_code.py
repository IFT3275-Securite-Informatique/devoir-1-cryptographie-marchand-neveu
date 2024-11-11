import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import random
import math
from textblob import TextBlob
from pattern.fr import lexicon

# Fonction pour charger les IDs de textes en français depuis le site Gutenberg
def load_text_ids():
    # URL de la page contenant la liste des livres en français
    url = "https://www.gutenberg.org/browse/languages/fr"

    # Envoie une requête GET pour récupérer le contenu de la page
    response = requests.get(url)

    # Vérifie si la requête a réussi
    if response.status_code == 200:
        # Analyse le contenu de la page HTML avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Trouve tous les liens qui contiennent "/ebooks/"
        links = soup.find_all('a', href=True)

        # Extrait les IDs des livres à partir des liens
        book_ids = []
        for link in links:
            href = link['href']
            if href.startswith("/ebooks/"):
                # Extrait l'ID après "/ebooks/"
                book_id = href.split("/ebooks/")[1]
                book_ids.append(book_id)
        print("Nombre de textes à récupérer : ")
        print(len(book_ids))
        return book_ids
    else:
        print(f"Erreur lors de la récupération de la page : {response.status_code}")
        return None

# Fonction pour charger les textes des livres et analyser les fréquences des caractères
def load_texts(books_ids):
    number_text_train = 50
    books_ids = books_ids[:number_text_train]  # Sélectionne les 50 premiers livres

    # Dictionnaire pour compter les occurrences des caractères (lettres et paires de lettres)
    carac_counts = defaultdict(int)
    total_symbol = 0
    i = 0

    # Liste de caractères et de bigrammes d'intérêt
    caracteres = [...]  # Liste de caractères définie
    bicaracteres = [...]  # Liste de bigrammes définie

    full_text = ""

    # Pour chaque livre, récupérer le texte et compter les caractères
    for book_id in books_ids:
        # Construit l'URL du livre
        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        
        # Envoie une requête GET pour récupérer le texte du livre
        response = requests.get(url)
        
        if response.status_code == 200:
            text = response.text
            full_text += text

            # Parcourt le texte pour compter lettres et bigrammes
            while i < len(text):
                # Vérifie les paires de caractères
                if i + 1 < len(text):
                    pair = text[i] + text[i + 1]
                    if pair in bicaracteres:
                        carac_counts[pair] += 1
                        total_symbol += 1
                        i += 2  # Saute les deux caractères utilisés
                        continue

                # Vérifie le caractère seul
                if text[i] in caracteres:
                    carac_counts[text[i]] += 1
                    total_symbol += 1

                # Continue l'analyse du texte
                i += 1
        else:
            print(f"Erreur lors de la récupération du livre {book_id}.")
    return carac_counts, total_symbol

# Fonction pour calculer les fréquences des octets dans le texte chiffré
def freq_symbol_C(C):
    len_c = len(C)
    freq_symbol_c = defaultdict(int)
    n_symbols = len_c // 8
    
    # Parcourt le texte chiffré par blocs de 8 caractères
    for i in range(0, len_c - 7, 8):
        freq_symbol_c[C[i:i+8]] += 1
    
    # Calcule les fréquences relatives
    for cle in freq_symbol_c:
        freq_symbol_c[cle] /= n_symbols
        
    return freq_symbol_c

# Applique la substitution au texte chiffré en binaire
def appliquer_substitution_binaire(texte_binaire, substitution):
    texte_dechiffre = ""
    # Boucle par octets (8 bits)
    for i in range(0, len(texte_binaire), 8):
        octet = texte_binaire[i:i+8]
        lettre = substitution.get(octet, octet)  # Remplace l'octet par la lettre correspondante
        texte_dechiffre += lettre
    return texte_dechiffre

# Compare le texte déchiffré avec un dictionnaire pour vérifier la validité des mots
def comparer_texte_avec_dictionnaire(texte_dechiffre):
    mots = texte_dechiffre.split()  # Sépare le texte en mots
    mots_a_verifier = mots[:150]  # Sélectionne les 150 premiers mots
    mots_valides = [
        mot for mot in mots_a_verifier 
        if len(mot) > 2 and mot.lower() in lexicon  # Ignore les mots de 1 ou 2 lettres
    ]
    # Calcule la proportion de mots valides
    proportion_valides = len(mots_valides) / len(mots_a_verifier) if mots_a_verifier else 0
    return proportion_valides, mots_valides

# Génère des permutations initiales optimisées pour le texte chiffré
def generer_permutations_initiales_optimisees(texte_chiffre, frequence_chiffre, frequence_francais, nombre_initialisations=10):
    lettres_chiffrees = list(frequence_chiffre.keys())
    meilleure_permutation = None
    meilleur_score = 0
    mots_valides = []

    for _ in range(nombre_initialisations):
        # Génère une permutation des lettres triée par fréquence
        permutation = sorted(frequence_francais, key=lambda x: frequence_francais[x], reverse=True)
        random.shuffle(permutation[0:int(0.2 * len(permutation))])  # Ajoute un peu de hasard

        substitution = dict(zip(lettres_chiffrees, permutation))
        texte_dechiffre = appliquer_substitution_binaire(texte_chiffre, substitution)

        # Évalue le score de la permutation en comptant les mots valides
        score, mots_valides_temp = comparer_texte_avec_dictionnaire(texte_dechiffre)

        # Met à jour la meilleure permutation si nécessaire
        if score > meilleur_score:
            meilleure_permutation = permutation
            meilleur_score = score
            mots_valides = mots_valides_temp

    return meilleure_permutation, meilleur_score, mots_valides

# Fonction de déchiffrement utilisant le recuit simulé hybride
def recuit_simule_hybride(texte_chiffre, frequence_chiffre, frequence_francais, temperature=1500, cooling_rate=0.95, iterations=50, parallel_instances=100):
    # Initialisation avec des permutations uniques
    instances = [generer_permutations_initiales_optimisees(texte_chiffre, frequence_chiffre, frequence_francais) for _ in range(parallel_instances)]
    
    best_overall_permutation = None
    best_overall_score = 0
    mots_valides_final = None

    for i in range(iterations):
        for j, (permutation, best_score, mots_valides) in enumerate(instances):
            substitution = dict(zip(list(frequence_chiffre.keys()), permutation))
            texte_dechiffre = appliquer_substitution_binaire(texte_chiffre, substitution)
            score, mots_valides = comparer_texte_avec_dictionnaire(texte_dechiffre)

            if score > best_score:
                best_score = score
                instances[j] = (permutation[:], best_score, mots_valides)

            if temperature > 0 and random.random() < math.exp((score - best_score) / temperature):
                idx1, idx2 = random.sample(range(len(permutation)), 2)
                permutation[idx1], permutation[idx2] = permutation[idx2], permutation[idx1]

            if i % 50 == 0 and j < parallel_instances - 1:
                instances[j], instances[j + 1] = instances[j + 1], instances[j]

        # Met à jour la meilleure solution globale
        for perm, score, mots_valides in instances:
            if score > best_overall_score:
                best_overall_permutation = perm
                best_overall_score = score
                mots_valides_final = mots_valides

        # Ajuste la température
        if iterations > 0:
            temperature = max(temperature * cooling_rate * (1 - (i / iterations)), 1)
        else:
            temperature *= cooling_rate

    substitution = dict(zip(list(frequence_chiffre.keys()), best_overall_permutation))
    final_text = appliquer_substitution_binaire(texte_chiffre, substitution)

    return best_overall_permutation, best_overall_score, mots_valides_final, final_text

# Fonction principale de déchiffrement
def decrypt(C):
    M = ""
  
    book_ids = load_text_ids()
    freq_symbol, total_symbol = load_texts(book_ids)

    # Calcule la fréquence relative des symboles
    for cle in freq_symbol:
        freq_symbol[cle] /= total_symbol
    sorted_freq_symbol = dict(sorted(freq_symbol.items(), key=lambda item: item[1], reverse=True))
    
    freq_symbol_c = freq_symbol_C(C)
    sorted_freq_symbol_c = dict(sorted(freq_symbol_c.items(), key=lambda item: item[1], reverse=True))

    permutation, score, mots_valides, texte_final = recuit_simule_hybride(
        C, sorted_freq_symbol_c, sorted_freq_symbol
    )

    # Affiche les résultats
    print(permutation)
    print(score)
    print(mots_valides)
    print(texte_final[:500])  # Affiche un extrait du texte final

    return M 
