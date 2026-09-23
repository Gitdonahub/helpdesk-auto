# app.py

from flask import Flask, render_template, request, redirect, url_for, session
from database import *
from werkzeug.security import check_password_hash
from diagnostics.network_diagnostic import run_diagnostic
from diagnostics.printer_diagnostic import run_printer_diagnostic
from disk_diagnostics import run_disk_diagnostic
from performance_diagnostics import run_performance_diagnostic
from email_diagnostics import (run_email_diagnostic, run_microsoft365_diagnostic)

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_changez_moi'  # À changer

# Initialisation de la base de données au démarrage
init_db()
create_default_admin()

# --- Analyse de la description ---
def analyze_description(description):
    desc = description.lower()
    if any(word in desc for word in ["internet", "réseau", "reseau", "connexion", "wifi", "wi-fi", "dns", "ip", "passerelle", "dhcp", "ping"]):
        return "reseau"
    if any(word in desc for word in ["imprimante", "impression", "print", "spooler", "scanner", "copieur","imprimer","copier","copie","copié","imprime","imprimé","inprimante"]):
        return "imprimante"
    if any(word in desc for word in ["disque", "espace", "stockage", "volume", "partition", "full", "plein", "saturation", "disk", "storage", "ssd", "hdd"]):
        return "disque"
    if any(word in desc for word in ["lent", "lenteur", "ralentissement", "performance", "cpu", "mémoire", "ram", "processeur","bloque","bug","bloquer","bugger","bloqué","buggé","ralentit","ralenti","ralentissement","ne fonctionne pas","ne marche pas","ne marche"]):
        return "performance"
    if any(word in desc for word in ["email", "courriel", "mail", "messagerie", "outlook"]):
        return "email"
    if any(word in desc for word in ["microsoft 365", "office 365", "365", "microsoft office", "teams", "onedrive", "sharepoint", "exchange","office"]):
        return "microsoft365"
    return "inconnu"

# --- Décorateur login_required ---
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def get_summary(result_text, category):
    """Extrait les lignes importantes (Cause probable, Action corrective) pour l'utilisateur."""
    lines = result_text.splitlines()
    summary_lines = []
    for line in lines:
        if "Cause probable" in line or "Action corrective" in line or "Tous les tests sont bons" in line or "Diagnostic non disponible" in line:
            summary_lines.append(line)
    if not summary_lines:
        summary_lines = ["Diagnostic effectué. Consultez le détail ci-dessous."]
    return "<br>".join(summary_lines)

# --- Routes d'authentification ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        matricule = request.form.get("matricule", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_matricule(matricule)
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['matricule'] = user[1]
            session['full_name'] = user[2]
            session['role'] = user[4]
            # Vérifier si l'utilisateur doit changer son mot de passe
            if user_must_change_password(user[0]):
                return redirect(url_for('force_change_password'))
            if user[4] == 'tech':
                return redirect(url_for('technicien'))
            elif user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Matricule ou mot de passe invalide.")
    return render_template('login.html', error=None)

@app.route("/force_change_password", methods=["GET", "POST"])
@login_required
def force_change_password():
    if not user_must_change_password(session['user_id']):
        # Pas besoin de changer, rediriger selon le rôle
        return redirect(url_for('index'))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if len(new_password) < 8:
            return render_template('force_change_password.html',
                                   error="Le mot de passe doit contenir au moins 8 caractères.")
        if new_password != confirm:
            return render_template('force_change_password.html',
                                   error="Les mots de passe ne correspondent pas.")
        update_user_password(session['user_id'], new_password, must_change=0)
        # Rediriger selon le rôle
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'tech':
            return redirect(url_for('technicien'))
        else:
            return redirect(url_for('index'))

    return render_template('force_change_password.html', error=None)

@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        user = get_user_by_id(session['user_id'])
        if not check_password_hash(user[3], current):
            return render_template('profil.html', error="Mot de passe actuel incorrect.")

        if len(new_password) < 8:
            return render_template('profil.html', error="Le nouveau mot de passe doit contenir au moins 8 caractères.")
        if new_password != confirm:
            return render_template('profil.html', error="Les mots de passe ne correspondent pas.")

        update_user_password(session['user_id'], new_password, must_change=0)
        return render_template('profil.html', message="Mot de passe modifié avec succès.")

    user = get_user_by_id(session['user_id'])
    return render_template('profil.html', user=user)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        matricule = request.form.get("matricule", "").strip()
        full_name = request.form.get("full_name", "").strip()
        invite_code = request.form.get("invite_code", "").strip()
        role = 'tech' if invite_code else 'user'
        password_clear, error = create_user(matricule, full_name, role, invite_code if role == 'tech' else None)
        if password_clear:
            return render_template('password_display.html', matricule=matricule, password=password_clear)
        else:
            return render_template('register.html', error=error)
    return render_template('register.html', error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/admin")
@login_required
def admin_dashboard():
    if session.get('role') != 'admin':
        return "Accès réservé à l'administrateur.", 403

    stats = {
        'techs': count_users_by_role('tech'),
        'users': count_users_by_role('user'),
        'tickets_total': count_tickets_total(),
        'tickets_week': count_tickets_last_7_days(),
        'by_status': count_tickets_by_status(),
        'by_category': count_tickets_by_category(),
    }
    return render_template('admin_dashboard.html', stats=stats)

@app.route("/admin/codes", methods=["GET", "POST"])
@login_required
def admin_codes():
    if session.get('role') != 'admin':
        return "Accès réservé à l'administrateur.", 403
    new_code = None
    if request.method == "POST":
        new_code = generate_invite_code()
    codes = get_all_invite_codes()
    return render_template('admin_codes.html', codes=codes, new_code=new_code)

@app.route("/admin/utilisateurs", methods=["GET", "POST"])
@login_required
def admin_users():
    if session.get('role') != 'admin':
        return "Accès réservé à l'administrateur.", 403
    message = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "delete_user":
            user_id = request.form.get("user_id")
            if user_id:
                delete_user(int(user_id))
                message = "Utilisateur supprimé."
    role_filter = request.args.get("role", None)
    users = get_all_users(role_filter)
    return render_template('admin_users.html', users=users, message=message, role_filter=role_filter)

@app.route("/admin/contacts", methods=["GET", "POST"])
@login_required
def admin_contacts():
    if session.get('role') != 'admin':
        return "Accès réservé à l'administrateur.", 403
    message = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_support":
            name = request.form.get("name", "").strip()
            team = request.form.get("team", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            sector = request.form.get("sector", "").strip()
            hours = request.form.get("available_hours", "").strip()
            if name and team:
                add_support_contact(name, team, phone, email, sector, hours)
                message = "Contact support ajouté."
        elif action == "delete_support":
            contact_id = request.form.get("contact_id")
            if contact_id:
                delete_support_contact(int(contact_id))
                message = "Contact supprimé."
    contacts = get_all_support_contacts()
    return render_template('admin_contacts.html', contacts=contacts, message=message)

@app.route("/admin/support/delete/<int:contact_id>", methods=["POST"])
@login_required
def admin_support_delete(contact_id):
    if session.get('role') != 'admin':
        return "Accès réservé à l'administrateur.", 403
    delete_support_contact(contact_id)
    return redirect(url_for('admin_support'))

@app.route("/admin/matricules")
@login_required
def admin_matricules():
    if session.get('role') != 'admin':
        return "Accès réservé à l'administrateur.", 403
    matricules = get_all_matricules_status()
    return render_template('admin_matricules.html', matricules=matricules)

@app.route("/admin/reset_password/<int:user_id>", methods=["POST"])
@login_required
def admin_reset_password(user_id):
    if session.get('role') != 'admin':
        return "Accès réservé à l'administrateur.", 403
    new_pass = generate_random_password()
    update_user_password(user_id, new_pass, must_change=1)
    return render_template('admin_reset_result.html',
                           user=get_user_by_id(user_id),
                           new_password=new_pass)

# --- Routes principales protégées ---
@app.route("/")
@login_required
def index():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    if session.get('role') == 'tech':
        return redirect(url_for('technicien'))
    return render_template('index.html')

@app.route("/diagnostic", methods=["POST"])
@login_required
def diagnostic():
    user_sector = request.form.get("user_sector", "")
    description = request.form.get("description", "")
    category = analyze_description(description)

    if category == "reseau":
        full_result = run_diagnostic()
        titre = "Diagnostic réseau"
    elif category == "imprimante":
        full_result = run_printer_diagnostic()
        titre = "Diagnostic impression"
    elif category == "disque":
        full_result = run_disk_diagnostic()
        titre = "Diagnostic espace disque"
    elif category == "performance":
        full_result = run_performance_diagnostic()
        titre = "Diagnostic performance"
    elif category == "email":
        full_result = run_email_diagnostic()
        titre = "Diagnostic messagerie"
    elif category == "microsoft365":
        full_result = run_microsoft365_diagnostic()
        titre = "Diagnostic Microsoft 365"
    else:
        full_result = "Désolé, je ne sais pas encore diagnostiquer ce type de problème automatiquement. Un technicien va prendre en charge votre demande."
        titre = "Diagnostic non disponible"

    # Sauvegarder le ticket avec le nom complet de l'utilisateur
    save_ticket(session['user_id'], session['full_name'], user_sector, description, category, full_result)

    summary = get_summary(full_result, category)

    return render_template('result.html', titre=titre, user_name=session['full_name'],
                           user_sector=user_sector, description=description, full_result=full_result, summary=summary)

@app.route("/mes_tickets")
@login_required
def mes_tickets():
    tickets = get_tickets_for_user(session['user_id'])
    return render_template('mes_tickets.html', tickets=tickets)

@app.route("/technicien")
@login_required
def technicien():
    if session['role'] != 'tech':
        return "Accès réservé aux techniciens.", 403
    filter_status = request.args.get("status", None)
    tickets = get_all_tickets(filter_status)
    return render_template('technicien.html', tickets=tickets)

@app.route("/tech/diagnostics")
@login_required
def tech_diagnostics():
    if session['role'] != 'tech':
        return "Accès réservé aux techniciens.", 403
    return render_template('tech_diagnostics.html')

@app.route("/tech/diagnostics/run", methods=["POST"])
@login_required
def tech_diagnostics_run():
    if session['role'] != 'tech':
        return "Accès réservé aux techniciens.", 403

    category = request.form.get("category", "")
    description = request.form.get("description", "").strip() or "(Test technicien sans description)"

    if category == "reseau":
        full_result = run_diagnostic()
        titre = "Diagnostic réseau"
    elif category == "imprimante":
        full_result = run_printer_diagnostic()
        titre = "Diagnostic impression"
    elif category == "disque":
        full_result = run_disk_diagnostic()
        titre = "Diagnostic espace disque"
    elif category == "performance":
        full_result = run_performance_diagnostic()
        titre = "Diagnostic performance"
    elif category == "email":
        full_result = run_email_diagnostic()
        titre = "Diagnostic messagerie"
    elif category == "microsoft365":
        full_result = run_microsoft365_diagnostic()
        titre = "Diagnostic Microsoft 365"
    else:
        full_result = "Catégorie inconnue. Aucun diagnostic exécuté."
        titre = "Diagnostic"

    return render_template('tech_diagnostics_result.html',
                           titre=titre,
                           full_result=full_result,
                           description=description)

@app.route("/ticket/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = get_ticket(ticket_id)
    if not ticket:
        return "Ticket introuvable", 404
    # Vérifier les droits : le propriétaire ou un technicien peuvent voir
    if session['role'] != 'tech' and ticket[1] != session['user_id']:
        return "Accès non autorisé", 403

    messages = get_messages(ticket_id)
    history = get_status_history(ticket_id)

    # Déterminer le libellé du diagnostic selon la catégorie
    category_labels = {
        "reseau": "Diagnostic réseau",
        "imprimante": "Diagnostic impression",
        "disque": "Diagnostic espace disque",
        "performance": "Diagnostic performance",
        "email": "Diagnostic messagerie",
        "microsoft365": "Diagnostic Microsoft 365",
        "inconnu": "Diagnostic non disponible"
    }
    category_label = category_labels.get(ticket[5], "Diagnostic")

    # Résumé pour l'utilisateur (extrait les lignes importantes)
    summary = get_summary(ticket[6], ticket[5])

    return render_template('ticket_detail.html', ticket=ticket, messages=messages,
                           history=history, summary=summary, category_label=category_label)

@app.route("/ticket/<int:ticket_id>/status", methods=["POST"])
@login_required
def change_status(ticket_id):
    if session['role'] != 'tech':
        return "Accès réservé aux techniciens.", 403
    new_status = request.form.get("status", "Ouvert")
    update_ticket_status(ticket_id, new_status, session['user_id'])
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route("/ticket/<int:ticket_id>/rediagnose", methods=["POST"])
@login_required
def rediagnose(ticket_id):
    if session['role'] != 'tech':
        return "Accès réservé aux techniciens.", 403
    ticket = get_ticket(ticket_id)
    if not ticket:
        return "Ticket introuvable", 404
    category = ticket[5]
    if category == "reseau":
        new_result = run_diagnostic()
    elif category == "imprimante":
        new_result = run_printer_diagnostic()
    elif category == "disque":
        new_result = run_disk_diagnostic()
    elif category == "performance":
        new_result = run_performance_diagnostic()
    elif category == "email":
        new_result = run_email_diagnostic()
    elif category == "microsoft365":
        new_result = run_microsoft365_diagnostic()
    else:
        new_result = "Diagnostic non disponible pour cette catégorie."
    update_ticket_result(ticket_id, new_result)
    add_message(ticket_id, session['user_id'], 'tech', "Le diagnostic a été relancé. Nouveau résultat enregistré.")
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route("/ticket/<int:ticket_id>/message", methods=["POST"])
@login_required
def post_message(ticket_id):
    ticket = get_ticket(ticket_id)
    if not ticket:
        return "Ticket introuvable", 404
    if session['role'] != 'tech' and ticket[1] != session['user_id']:
        return "Accès non autorisé", 403
    message = request.form.get("message", "")
    if message.strip():
        add_message(ticket_id, session['user_id'], session['role'], message.strip())
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route("/support")
@login_required
def support_directory():
    contacts = get_all_support_contacts()
    return render_template('support.html', contacts=contacts)



if __name__ == "__main__":
    app.run(debug=True)