# helpdesk-auto
markdown
# TrustSolve 🔧

**Système de HelpDesk IT automatisé avec diagnostic intelligent**

TrustSolve est une application web de ticketing informatique qui automatise le diagnostic des incidents courants (réseau, imprimante, disque, performance, messagerie, Microsoft 365) et fournit une plateforme complète de suivi pour les utilisateurs, techniciens et administrateurs.

---

## 📋 Table des matières

- [Présentation](#-présentation)
- [Fonctionnalités](#-fonctionnalités)
- [Captures d'écran](#-captures-décran)
- [Architecture](#-architecture)
- [Technologies](#-technologies)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Diagnostics disponibles](#-diagnostics-disponibles)
- [Sécurité](#-sécurité)
- [Structure du projet](#-structure-du-projet)
- [Améliorations futures](#-améliorations-futures)
- [Auteur](#-auteur)
- [Licence](#-licence)

---

## 🎯 Présentation

Dans toute organisation, le service informatique reçoit quotidiennement des demandes répétitives : « Je n'ai plus Internet », « Mon imprimante ne fonctionne pas », « Mon PC est lent »… Ces incidents simples mobilisent beaucoup de temps technicien pour des vérifications toujours identiques.

**TrustSolve** répond à ce problème en offrant :

- Un **diagnostic automatique** exécuté en quelques secondes après la description du problème.
- Un **résumé clair** pour l'utilisateur (cause probable + actions correctives).
- Un **rapport technique complet** pour les techniciens.
- Un **système de ticketing** avec chat, statuts et historique.
- Un **espace admin** pour gérer utilisateurs, techniciens et contacts support.

---

## ✨ Fonctionnalités

### 👤 Pour les utilisateurs
- Inscription avec matricule à 5 chiffres (plage contrôlée).
- Mot de passe généré automatiquement et changement obligatoire à la première connexion.
- Création de tickets avec secteur en liste déroulante (CAT, RSI, RH, CNS, AIM).
- **Diagnostic automatique** en fonction du problème décrit.
- **Résumé vocal** du résultat (synthèse vocale du navigateur).
- Suivi de ses propres tickets avec statut et historique.
- Chat avec les techniciens sur chaque ticket.

### 🛠️ Pour les techniciens
- Vue globale de tous les tickets avec filtres par statut.
- Accès au **diagnostic complet** (détails techniques).
- **Relance du diagnostic** depuis leur propre poste pour comparaison.
- Historique des relances conservé pour chaque ticket.
- Changement de statut (Ouvert, En cours, Résolu, Fermé).
- **Espace de test** pour lancer des diagnostics librement.

### 🔐 Pour l'administrateur
- Tableau de bord avec statistiques (utilisateurs, tickets, répartition).
- Génération de **codes d'invitation** pour les techniciens.
- Gestion des utilisateurs (recherche, filtrage par rôle, suppression, réinitialisation de mot de passe).
- Registre des matricules (15620 → 15720) avec état libre/pris.
- Gestion du **répertoire des contacts support**.

---

## 🏗️ Architecture
┌─────────────────┐
│ Navigateur │
│ (Utilisateur, │
│ Technicien, │
│ Admin) │
└────────┬────────┘
│ HTTP
▼
┌─────────────────┐
│ Flask (app) │ ← Routes, sessions, authentification
└────────┬────────┘
│
┌────┴────┬──────────┬───────────┐
▼ ▼ ▼ ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│ SQLite │ │Modules │ │Jinja2 │ │Web Speech API│
│ (BDD) │ │diagnos.│ │Templates│ │(synthèse voc.)│
└────────┘ └────────┘ └────────┘ └──────────────┘
│
▼
┌──────────────────┐
│ PowerShell/WMIC │
│ (commandes sys.) │
└──────────────────┘

text

---

## 🧰 Technologies

| Catégorie | Outils |
|---|---|
| **Langage** | Python 3.12+ |
| **Framework web** | Flask |
| **Base de données** | SQLite |
| **Templates** | Jinja2 |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Sécurité** | Werkzeug Security (PBKDF2), sessions Flask |
| **Scripting système** | PowerShell, WMIC |
| **Synthèse vocale** | Web Speech API (navigateur) |

---

## 📦 Prérequis

- **Python 3.12 ou supérieur**
- **Windows** (les diagnostics utilisent PowerShell et WMIC)
- **PowerShell** accessible depuis le PATH système
- Un navigateur moderne (Chrome, Edge, Firefox, Safari)

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/TrustSolve.git
cd TrustSolve
2. Créer un environnement virtuel (recommandé)
bash
python -m venv venv
venv\Scripts\activate
3. Installer les dépendances
bash
pip install flask werkzeug
4. Lancer l'application
bash
python app.py
L'application sera accessible à l'adresse : http://127.0.0.1:5000

🎮 Utilisation
Compte administrateur par défaut
Champ	Valeur
Matricule	admin
Mot de passe	21park90
⚠️ Changez ce mot de passe en production !

Comptes de test
Des comptes de test peuvent être créés manuellement via la page d'inscription :

Utilisateurs : inscription libre avec matricule (15620 → 15720).

Techniciens : inscription avec un code d'invitation généré par l'admin.

Workflow typique
L'utilisateur se connecte, choisit son secteur, décrit son problème.

Le système analyse la description, lance le diagnostic adapté, affiche un résumé (avec lecture vocale automatique).

Le ticket est enregistré avec le diagnostic complet.

Le technicien consulte le ticket, peut relancer le diagnostic depuis son poste, échanger via le chat et changer le statut.

L'admin supervise l'ensemble depuis son tableau de bord.

🔍 Diagnostics disponibles
Catégorie	Vérifications effectuées
Réseau	Ping passerelle, ping DNS, résolution de noms, adresse IP, bail DHCP, service Client DNS
Imprimante	Service Spouleur, imprimante par défaut, liste des imprimantes
Disque	Espace libre par lecteur, gros fichiers (>500 Mo), seuil critique 10%
Performance	Utilisation CPU, mémoire disponible, top 5 des processus
Messagerie	Installation d'Outlook, exécution, connectivité serveur
Microsoft 365	Installation Word/Excel/PowerPoint/Teams/OneDrive/Outlook, connectivité aux services
🔒 Sécurité
Mots de passe hachés avec Werkzeug (PBKDF2, sel aléatoire).

Génération aléatoire forte de mots de passe (majuscules, minuscules, chiffres, symboles).

Changement obligatoire à la première connexion.

Contrôle d'accès basé sur les rôles (utilisateur / technicien / admin).

Codes d'invitation pour l'inscription des techniciens.

Cloisonnement des tickets : chaque utilisateur ne voit que les siens.

Registre de matricules contrôlé (plage 15620 → 15720, unicité garantie).

Journalisation des changements de statut et des relances de diagnostic.

📁 Structure du projet
text
TrustSolve/
├── app.py                          # Routes Flask et logique métier
├── database.py                     # Accès à la base de données
├── diagnostics/
│   ├── network_diagnostic.py       # Diagnostic réseau
│   └── printer_diagnostic.py       # Diagnostic imprimante
├── disk_diagnostics.py             # Diagnostic espace disque
├── performance_diagnostics.py      # Diagnostic performance
├── email_diagnostics.py            # Diagnostic messagerie + Microsoft 365
├── templates/
│   ├── base.html                   # Template de base (navbar, TTS script)
│   ├── login.html                  # Connexion
│   ├── register.html               # Inscription
│   ├── password_display.html       # Affichage du mot de passe généré
│   ├── force_change_password.html  # Changement obligatoire 1ère connexion
│   ├── profil.html                 # Profil utilisateur
│   ├── index.html                  # Formulaire de diagnostic
│   ├── result.html                 # Résultat (avec lecture vocale)
│   ├── mes_tickets.html            # Liste des tickets utilisateur
│   ├── ticket_detail.html          # Détail d'un ticket
│   ├── technicien.html             # Espace technicien
│   ├── tech_diagnostics.html       # Tests technicien
│   ├── tech_diagnostics_result.html
│   ├── support.html                # Répertoire des contacts support
│   ├── admin_dashboard.html        # Tableau de bord admin
│   ├── admin_codes.html            # Génération de codes
│   ├── admin_users.html            # Gestion des utilisateurs
│   ├── admin_contacts.html         # Gestion des contacts support
│   ├── admin_matricules.html       # Registre des matricules
│   └── admin_reset_result.html     # Résultat de réinitialisation
├── static/
│   └── style.css                   # Feuille de style personnalisée
├── matricules.txt                  # Registre de référence (15620-15720)
├── tickets.db                      # Base de données (générée au démarrage)
└── README.md
🚧 Améliorations futures
□ Notifications par email lors des changements de statut
□ Export PDF des tickets
□ Intégration Active Directory (authentification SSO)
□ Tests unitaires et d'intégration
□ Pagination dans les listes
□ Tableau de bord avec graphiques (Chart.js)
□ Support multi-langue
□ Assistant vocal plus avancé (choix de voix, vitesse)
□ Déploiement via Docker
