# diagnostics/printer_diagnostic.py

import subprocess

def run_command(command):
    """Exécute une commande et retourne (succès, sortie)."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def get_default_printer():
    """Retourne le nom de l'imprimante par défaut (ou None si aucune)."""
    ps_command = "Get-CimInstance Win32_Printer | Where-Object {$_.Default -eq $true} | Select-Object -ExpandProperty Name"
    success, output = run_command(["powershell", "-Command", ps_command])
    if success and output.strip():
        return output.strip()
    return None

def list_printers():
    """Retourne la liste des imprimantes installées."""
    ps_command = "Get-CimInstance Win32_Printer | Select-Object -ExpandProperty Name"
    success, output = run_command(["powershell", "-Command", ps_command])
    if success:
        return output.strip()
    return "Aucune imprimante trouvée."

def run_printer_diagnostic():
    """Exécute le diagnostic d'impression et retourne un texte détaillé."""
    lines = []
    lines.append("=== Diagnostic impression ===")

    # 1. Service spooler
    lines.append("")
    lines.append("[1] Vérification du service Spouleur d'impression...")
    success, output = run_command(["sc", "query", "Spooler"])
    if success and "RUNNING" in output.upper():
        lines.append("    -> Service spooler en cours d'exécution.")
    else:
        lines.append("    -> Service spooler arrêté ou introuvable.")
        lines.append("Cause probable : le spooler d'impression est arrêté.")
        lines.append("Action corrective suggérée : redémarrer le service Spooler.")
        return "\n".join(lines)

    # 2. Imprimante par défaut
    lines.append("")
    lines.append("[2] Vérification de l'imprimante par défaut...")
    default_printer = get_default_printer()
    if default_printer:
        lines.append(f"    -> Imprimante par défaut : {default_printer}")
    else:
        lines.append("    -> Aucune imprimante par défaut définie.")
        lines.append("Cause probable : aucune imprimante par défaut configurée.")
        lines.append("Action corrective suggérée : définir une imprimante par défaut dans les paramètres Windows.")
        return "\n".join(lines)

    # 3. Liste des imprimantes
    lines.append("")
    lines.append("[3] Imprimantes installées :")
    printers = list_printers()
    if printers and printers != "Aucune imprimante trouvée.":
        for p in printers.splitlines():
            lines.append(f"    - {p}")
    else:
        lines.append("    Aucune imprimante installée.")
        lines.append("Cause probable : aucune imprimante installée sur ce poste.")
        return "\n".join(lines)

    # Si tout semble OK
    lines.append("")
    lines.append("=== Diagnostic ===")
    lines.append("Le service d'impression et les imprimantes semblent corrects.")
    lines.append("Si le problème persiste, vérifiez la connexion physique de l'imprimante ou contactez le support.")
    return "\n".join(lines)



if __name__ == "__main__":
    print(run_printer_diagnostic())