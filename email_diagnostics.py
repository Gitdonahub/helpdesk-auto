# email_diagnostics.py

import subprocess

def run_command(command):
    """Exécute une commande et retourne (succès, sortie)."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def check_outlook_installed():
    """
    Vérifie si Microsoft Outlook est installé en cherchant dans le registre Windows.
    Retourne True si installé, False sinon.
    """
    ps_command = "Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Office\\16.0\\Outlook' -ErrorAction SilentlyContinue"
    success, output = run_command(["powershell", "-Command", ps_command])
    if success and output.strip():
        return True
    # Vérifier d'autres versions d'Office
    ps_command2 = "Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Office\\15.0\\Outlook' -ErrorAction SilentlyContinue"
    success2, output2 = run_command(["powershell", "-Command", ps_command2])
    if success2 and output2.strip():
        return True
    # Vérifier la présence de l'exécutable Outlook
    ps_command3 = "Test-Path 'C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE'"
    success3, output3 = run_command(["powershell", "-Command", ps_command3])
    if success3 and "True" in output3:
        return True
    return False

def check_outlook_running():
    """
    Vérifie si le processus Outlook est en cours d'exécution.
    Retourne True si le processus existe, False sinon.
    """
    ps_command = "Get-Process OUTLOOK -ErrorAction SilentlyContinue"
    success, output = run_command(["powershell", "-Command", ps_command])
    return success and output.strip() != ""

def test_mail_server_connectivity(server="outlook.office365.com", port=443):
    """
    Teste la connectivité au serveur de messagerie sur le port spécifié.
    Retourne (succès, message).
    """
    ps_command = f"Test-NetConnection -ComputerName {server} -Port {port} -InformationLevel Quiet"
    success, output = run_command(["powershell", "-Command", ps_command])
    if success and output.strip() == "True":
        return True, f"Connexion à {server}:{port} réussie."
    else:
        return False, f"Impossible de se connecter à {server}:{port}."

def run_email_diagnostic():
    """Exécute le diagnostic de messagerie et retourne un texte détaillé."""
    lines = []
    lines.append("=== Diagnostic messagerie / Outlook ===")

    # 1. Vérifier si Outlook est installé
    lines.append("")
    lines.append("[1] Vérification de l'installation d'Outlook...")
    if check_outlook_installed():
        lines.append("    -> Outlook est installé.")
    else:
        lines.append("    -> Outlook ne semble pas être installé sur ce poste.")
        lines.append("Cause probable : Microsoft Outlook n'est pas installé.")
        lines.append("Action corrective suggérée : installez Microsoft Office ou contactez le support.")
        return "\n".join(lines)

    # 2. Vérifier si Outlook est en cours d'exécution
    lines.append("")
    lines.append("[2] Vérification de l'état d'Outlook...")
    if check_outlook_running():
        lines.append("    -> Outlook est en cours d'exécution.")
    else:
        lines.append("    -> Outlook n'est pas en cours d'exécution.")
        lines.append("Action corrective suggérée : lancez Outlook depuis le menu Démarrer.")

    # 3. Tester la connectivité au serveur de messagerie
    lines.append("")
    lines.append("[3] Test de connectivité au serveur de messagerie...")
    # Vous pouvez adapter le serveur à votre environnement
    success, message = test_mail_server_connectivity("outlook.office365.com","/m365.cloud.microsoft.com" , 443)
    lines.append(f"    {message}")
    if not success:
        lines.append("Cause probable : problème de connexion réseau ou serveur de messagerie injoignable.")
        lines.append("Action corrective suggérée : vérifiez votre connexion Internet et les paramètres du serveur de messagerie.")
        return "\n".join(lines)

    # 4. Conclusion
    lines.append("")
    lines.append("=== Diagnostic ===")
    lines.append("Outlook est installé et la connectivité au serveur semble correcte.")
    lines.append("Si vous rencontrez des problèmes de messagerie, vérifiez vos paramètres de compte.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(run_email_diagnostic())



# microsoft365_diagnostics.py

def run_command(command):
    """Exécute une commande et retourne (succès, sortie)."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def check_application_installed(app_name):
    """
    Vérifie si une application Microsoft 365 est installée.
    On utilise le registre Windows pour détecter les installations Office.
    Pour simplifier, on vérifie la présence de l'exécutable dans le dossier Office.
    """
    # Dossier typique d'Office 365
    office_path = "C:\\Program Files\\Microsoft Office\\root\\Office16"
    exe_name = app_name.upper() + ".EXE"
    ps_command = f"Test-Path '{office_path}\\{exe_name}'"
    success, output = run_command(["powershell", "-Command", ps_command])
    if success and "True" in output:
        return True
    # Vérifier aussi via le registre (clé de désinstallation)
    # On peut utiliser Get-ItemProperty sur HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*
    # mais restons simple avec l'exécutable.
    return False

def check_application_running(app_name):
    """
    Vérifie si l'application est en cours d'exécution.
    """
    ps_command = f"Get-Process {app_name} -ErrorAction SilentlyContinue"
    success, output = run_command(["powershell", "-Command", ps_command])
    return success and output.strip() != ""

def test_microsoft_connectivity():
    """
    Teste la connectivité aux services Microsoft 365 (login.microsoftonline.com).
    """
    server = "login.microsoftonline.com"
    port = 443
    ps_command = f"Test-NetConnection -ComputerName {server} -Port {port} -InformationLevel Quiet"
    success, output = run_command(["powershell", "-Command", ps_command])
    if success and output.strip() == "True":
        return True, f"Connexion à {server}:{port} réussie."
    else:
        return False, f"Impossible de se connecter à {server}:{port}."

def run_microsoft365_diagnostic():
    """Exécute le diagnostic Microsoft 365 et retourne un texte détaillé."""
    lines = []
    lines.append("=== Diagnostic Microsoft 365 / Office ===")

    # Liste des applications à vérifier
    apps_to_check = [
        ("Winword", "Microsoft Word"),
        ("Excel", "Microsoft Excel"),
        ("Powerpnt", "Microsoft PowerPoint"),
        ("Teams", "Microsoft Teams"),
        ("OneDrive", "OneDrive"),
        ("Outlook", "Microsoft Outlook"),
    ]

    # 1. Vérifier chaque application
    lines.append("")
    lines.append("[1] Vérification de l'installation des applications :")
    installed_apps = []
    missing_apps = []
    for process_name, display_name in apps_to_check:
        installed = check_application_installed(process_name)
        if installed:
            lines.append(f"    - {display_name} : installé")
            installed_apps.append((process_name, display_name))
        else:
            lines.append(f"    - {display_name} : NON installé")
            missing_apps.append((process_name, display_name))

    # 2. Vérifier les processus en cours
    lines.append("")
    lines.append("[2] Vérification des applications en cours d'exécution :")
    for process_name, display_name in installed_apps:
        running = check_application_running(process_name)
        if running:
            lines.append(f"    - {display_name} : en cours d'exécution")
        else:
            lines.append(f"    - {display_name} : arrêté")

    # 3. Tester la connectivité aux services Microsoft 365
    lines.append("")
    lines.append("[3] Test de connectivité aux services Microsoft 365...")
    success, message = test_microsoft_connectivity()
    lines.append(f"    {message}")
    if not success:
        lines.append("Cause probable : problème de réseau ou service Microsoft 365 indisponible.")
        lines.append("Action corrective suggérée : vérifiez votre connexion Internet, les paramètres de proxy/firewall, ou contactez le support.")
        return "\n".join(lines)

    # 4. Conclusion
    lines.append("")
    lines.append("=== Diagnostic ===")
    if missing_apps:
        lines.append("Certaines applications Microsoft 365 ne sont pas installées sur ce poste.")
        lines.append("Applications manquantes : " + ", ".join([name for _, name in missing_apps]))
        lines.append("Action corrective suggérée : installez les applications manquantes via le portail Microsoft 365 ou contactez le support.")
    else:
        lines.append("Toutes les applications Microsoft 365 vérifiées sont installées.")
        lines.append("La connectivité aux services Microsoft 365 est correcte.")
        lines.append("Si vous rencontrez des problèmes, essayez de redémarrer l'application ou de réparer Office via le panneau de configuration.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(run_microsoft365_diagnostic())