# database.py

import sqlite3
from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

DB_NAME = 'tickets.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table users avec matricule et full_name
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            must_change_password INTEGER DEFAULT 1
        )
    ''')
    # Table invite_codes
    c.execute('''
        CREATE TABLE IF NOT EXISTS invite_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            used INTEGER DEFAULT 0,
            used_by INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (used_by) REFERENCES users (id)
        )
    ''')
    # Table tickets (inchangée mais user_name devient full_name)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            user_sector TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            result TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Ouvert',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Table status_history
    c.execute('''
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            changed_by INTEGER NOT NULL,
            changed_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id),
            FOREIGN KEY (changed_by) REFERENCES users (id)
        )
    ''')
    # Table messages
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            sender_role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
        )
    ''')
    # table support
    c.execute('''
        CREATE TABLE IF NOT EXISTS support_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            team TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            sector TEXT,
            available_hours TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def create_default_admin():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
    if c.fetchone()[0] == 0:
        # Admin par défaut : matricule 'admin', mot de passe initial '100000'
        hashed = generate_password_hash('21park90')
        c.execute('INSERT INTO users (matricule, full_name, password, role) VALUES (?, ?, ?, ?)',
                  ('admin', 'Administrateur', hashed, 'admin'))
        conn.commit()
    conn.close()

def generate_random_password(length=10):
    """Génère un mot de passe aléatoire fort (majuscules, minuscules, chiffres, symboles)."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    # On garantit au moins un caractère de chaque type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%&*"),
    ]
    # Compléter jusqu'à la longueur voulue
    for _ in range(length - 4):
        password.append(secrets.choice(alphabet))
    # Mélanger pour éviter un ordre prévisible
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

def create_user(matricule, full_name, role='user', invite_code=None):
    """
    Crée un utilisateur avec un mot de passe initial généré automatiquement.
    Vérifie :
      - le matricule est à 5 chiffres
      - le matricule est dans la plage autorisée (15620-15720)
      - le matricule n'est pas déjà pris
    """
    # 1. Validation format : 5 chiffres
    if not matricule or not matricule.isdigit() or len(matricule) != 5:
        return None, "Le matricule doit contenir exactement 5 chiffres."

    # 2. Validation plage autorisée
    if not is_matricule_in_range(matricule):
        return None, "Ce matricule n'est pas dans la plage autorisée (15620 - 15720)."

    # 3. Validation : déjà pris ?
    if is_matricule_taken(matricule):
        return None, "Ce matricule est déjà utilisé."

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Vérifier code d'invitation si tech
    code_id = None
    if role == 'tech':
        if not invite_code:
            conn.close()
            return None, "Code d'invitation requis pour un technicien."
        c.execute('SELECT id, used FROM invite_codes WHERE code = ?', (invite_code,))
        code_row = c.fetchone()
        if not code_row or code_row[1] == 1:
            conn.close()
            return None, "Code d'invitation invalide ou déjà utilisé."
        code_id = code_row[0]

    # Générer le mot de passe
    password_clear = generate_random_password()
    password_hashed = generate_password_hash(password_clear)

    # Insérer l'utilisateur
    c.execute('INSERT INTO users (matricule, full_name, password, role, must_change_password) VALUES (?, ?, ?, ?, 1)',
              (matricule, full_name, password_hashed, role))
    user_id = c.lastrowid

    # Marquer le code comme utilisé
    if code_id:
        c.execute('UPDATE invite_codes SET used = 1, used_by = ? WHERE id = ?', (user_id, code_id))

    conn.commit()
    conn.close()
    return password_clear, None

def get_user_by_matricule(matricule):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, matricule, full_name, password, role FROM users WHERE matricule = ?', (matricule,))
    user = c.fetchone()
    conn.close()
    return user

def check_password(user, password_clear):
    """Vérifie le mot de passe hashé."""
    return check_password_hash(user[3], password_clear)

def generate_invite_code():
    """Génère un code aléatoire (admin uniquement) et le stocke."""
    import secrets
    code = secrets.token_hex(4).upper()  # ex: 'A1B2C3D4'
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO invite_codes (code, created_at) VALUES (?, ?)',
              (code, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return code

def get_all_invite_codes():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, code, used, created_at FROM invite_codes ORDER BY id DESC')
    codes = c.fetchall()
    conn.close()
    return codes

def update_ticket_result(ticket_id, new_result):
    """Met à jour le résultat du diagnostic d'un ticket."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE tickets SET result = ? WHERE id = ?', (new_result, ticket_id))
    conn.commit()
    conn.close()

def add_message(ticket_id, sender_id, sender_role, message):
    """Ajoute un message au chat d'un ticket."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO messages (ticket_id, sender_id, sender_role, message, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (ticket_id, sender_id, sender_role, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_messages(ticket_id):
    """Retourne tous les messages d'un ticket, du plus ancien au plus récent, avec le nom de l'expéditeur."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT messages.sender_id, messages.sender_role, messages.message, messages.created_at, users.full_name
        FROM messages
        JOIN users ON messages.sender_id = users.id
        WHERE messages.ticket_id = ?
        ORDER BY messages.id ASC
    ''', (ticket_id,))
    messages = c.fetchall()
    conn.close()
    return messages

def get_status_history(ticket_id):
    """Retourne l'historique des changements de statut d'un ticket."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT status_history.old_status, status_history.new_status, status_history.changed_at, users.full_name
        FROM status_history
        JOIN users ON status_history.changed_by = users.id
        WHERE status_history.ticket_id = ?
        ORDER BY status_history.id ASC
    ''', (ticket_id,))
    history = c.fetchall()
    conn.close()
    return history

# Les fonctions tickets restent identiques à l'exception des noms de colonnes utilisateur.
# Nous les adaptons si nécessaire (user_name -> full_name). Voir ci-dessous.
# (Reprendre les fonctions get_tickets_for_user, etc. en remplaçant user_name par full_name si besoin)

def save_ticket(user_id, user_name, user_sector, description, category, result):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO tickets (user_id, user_name, user_sector, description, category, result, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'Ouvert', ?)
    ''', (user_id, user_name, user_sector, description, category, result, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_tickets_for_user(user_id, status_filter=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if status_filter:
        c.execute('SELECT id, user_name, user_sector, description, category, status, created_at FROM tickets WHERE user_id = ? AND status = ? ORDER BY id DESC', (user_id, status_filter))
    else:
        c.execute('SELECT id, user_name, user_sector, description, category, status, created_at FROM tickets WHERE user_id = ? ORDER BY id DESC', (user_id,))
    tickets = c.fetchall()
    conn.close()
    return tickets

def get_all_tickets(status_filter=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if status_filter:
        c.execute('SELECT id, user_name, user_sector, description, category, status, created_at, result FROM tickets WHERE status = ? ORDER BY id DESC', (status_filter,))
    else:
        c.execute('SELECT id, user_name, user_sector, description, category, status, created_at, result FROM tickets ORDER BY id DESC')
    tickets = c.fetchall()
    conn.close()
    return tickets

def get_ticket(ticket_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, user_id, user_name, user_sector, description, category, result, status, created_at FROM tickets WHERE id = ?', (ticket_id,))
    ticket = c.fetchone()
    conn.close()
    return ticket

def update_ticket_result(ticket_id, new_result):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE tickets SET result = ? WHERE id = ?', (new_result, ticket_id))
    conn.commit()
    conn.close()

def add_support_contact(name, team, phone, email, sector, available_hours):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO support_contacts (name, team, phone, email, sector, available_hours, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, team, phone, email, sector, available_hours, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_all_support_contacts():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, team, phone, email, sector, available_hours FROM support_contacts ORDER BY team ASC')
    contacts = c.fetchall()
    conn.close()
    return contacts

def delete_support_contact(contact_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM support_contacts WHERE id = ?', (contact_id,))
    conn.commit()
    conn.close()

def get_all_users(role_filter=None):
    """Retourne la liste des utilisateurs (avec filtre optionnel par rôle)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if role_filter and role_filter in ('user', 'tech', 'admin'):
        c.execute('SELECT id, matricule, full_name, role FROM users WHERE role = ? ORDER BY role, id DESC', (role_filter,))
    else:
        c.execute('SELECT id, matricule, full_name, role FROM users ORDER BY role, id DESC')
    users = c.fetchall()
    conn.close()
    return users

def delete_user(user_id):
    """Supprime un utilisateur (et ses tickets associés si nécessaire)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Supprimer les messages envoyés par cet utilisateur
    c.execute('DELETE FROM messages WHERE sender_id = ?', (user_id,))
    # Supprimer les tickets dont il est propriétaire (les messages associés sont gérés par cascade logique)
    c.execute('DELETE FROM tickets WHERE user_id = ?', (user_id,))
    # Supprimer l'utilisateur
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def count_users_by_role(role):
    """Retourne le nombre d'utilisateurs ayant un rôle donné."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE role = ?', (role,))
    count = c.fetchone()[0]
    conn.close()
    return count

def count_tickets_total():
    """Retourne le nombre total de tickets."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM tickets')
    count = c.fetchone()[0]
    conn.close()
    return count

def count_tickets_last_7_days():
    """Retourne le nombre de tickets créés dans les 7 derniers jours."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM tickets
        WHERE created_at >= datetime('now', '-7 days')
    ''')
    count = c.fetchone()[0]
    conn.close()
    return count

def count_tickets_by_status():
    """Retourne un dictionnaire {statut: nombre} pour tous les statuts."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT status, COUNT(*) FROM tickets GROUP BY status')
    rows = c.fetchall()
    conn.close()
    return dict(rows)

def count_tickets_by_category():
    """Retourne un dictionnaire {catégorie: nombre}."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT category, COUNT(*) FROM tickets GROUP BY category')
    rows = c.fetchall()
    conn.close()
    return dict(rows)

def update_user_password(user_id, new_password_clear, must_change=0):
    """Met à jour le mot de passe d'un utilisateur."""
    hashed = generate_password_hash(new_password_clear)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET password = ?, must_change_password = ? WHERE id = ?',
              (hashed, must_change, user_id))
    conn.commit()
    conn.close()

def user_must_change_password(user_id):
    """Retourne True si l'utilisateur doit changer son mot de passe."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT must_change_password FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return bool(row[0]) if row else False

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, matricule, full_name, password, role FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_ticket_status(ticket_id, new_status, changed_by):
    """Met à jour le statut d'un ticket et enregistre l'historique."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Récupérer l'ancien statut
    c.execute('SELECT status FROM tickets WHERE id = ?', (ticket_id,))
    row = c.fetchone()
    old_status = row[0] if row else None
    # Mettre à jour le ticket
    c.execute('UPDATE tickets SET status = ? WHERE id = ?', (new_status, ticket_id))
    # Enregistrer dans l'historique
    c.execute('''
        INSERT INTO status_history (ticket_id, old_status, new_status, changed_by, changed_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (ticket_id, old_status, new_status, changed_by, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def is_matricule_taken(matricule):
    """Vérifie si un matricule est déjà utilisé (sauf par l'admin qui n'a pas de matricule numérique)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE matricule = ?', (matricule,))
    row = c.fetchone()
    conn.close()
    return row is not None

def is_matricule_in_range(matricule):
    """Vérifie si le matricule est dans la plage autorisée (15620 - 15720)."""
    try:
        n = int(matricule)
        return 15620 <= n <= 15720
    except:
        return False

def get_all_matricules_status():
    """
    Retourne une liste de tuples (matricule, pris:bool).
    Basé sur la plage 15620-15720 et les matricules réellement utilisés.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT matricule FROM users WHERE matricule GLOB '[0-9]*'")
    rows = c.fetchall()
    conn.close()

    used = set()
    for (m,) in rows:
        if m and m.isdigit():
            used.add(m)

    all_matricules = []
    for n in range(15620, 15721):
        m = str(n)
        all_matricules.append((m, m in used))
    return all_matricules


