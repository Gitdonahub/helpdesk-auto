# disk_diagnostics.py

import subprocess

def run_command(command):
    """Exécute une commande et retourne (succès, sortie)."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def get_disk_space():
    """
    Récupère l'espace libre et total de chaque lecteur logique.
    Retourne une liste de tuples (lecteur, espace_libre_GB, espace_total_GB, pourcentage_libre).
    """
    # Utilisation de PowerShell pour obtenir des informations précises
    ps_command = "Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID, FreeSpace, Size"
    success, output = run_command(["powershell", "-Command", ps_command])
    if not success:
        return None
    disks = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split(":")
        if len(parts) == 2:
            drive = parts[0].strip()
            values = parts[1].strip().split()
            if len(values) == 2:
                try:
                    free_bytes = int(values[0])
                    total_bytes = int(values[1])
                    free_gb = free_bytes / (1024**3)
                    total_gb = total_bytes / (1024**3)
                    percent_free = (free_gb / total_gb) * 100
                    disks.append((drive, free_gb, total_gb, percent_free))
                except:
                    continue
    return disks

def find_large_files(drive, threshold_mb=500):
    """
    Recherche les fichiers de plus de threshold_mb Mo sur le lecteur spécifié.
    Retourne une liste des 5 plus gros fichiers (chemin, taille en Mo).
    """
    ps_command = f"Get-ChildItem -Path {drive}\\ -Recurse -File -ErrorAction SilentlyContinue | Where-Object {{ $_.Length -gt {threshold_mb}MB }} | Sort-Object Length -Descending | Select-Object -First 5 FullName, Length"
    success, output = run_command(["powershell", "-Command", ps_command])
    if not success:
        return []
    files = []
    lines = output.strip().splitlines()
    for line in lines:
        if line.strip():
            # Le format de sortie est : "FullName                                    Length"
            # On récupère le chemin et la taille (dernier élément)
            parts = line.rsplit(maxsplit=1)
            if len(parts) == 2:
                try:
                    size_mb = int(parts[1]) / (1024**2)
                    files.append((parts[0], size_mb))
                except:
                    continue
    return files

def run_disk_diagnostic():
    """Exécute le diagnostic d'espace disque et retourne un texte détaillé."""
    lines = []
    lines.append("=== Diagnostic espace disque ===")

    # 1. Récupérer l'espace disque
    disks = get_disk_space()
    if disks is None:
        lines.append("Impossible de récupérer les informations des lecteurs.")
        return "\n".join(lines)

    lines.append("")
    lines.append("[1] Vérification de l'espace libre sur les lecteurs :")
    problematic_disks = []
    for drive, free_gb, total_gb, percent_free in disks:
        lines.append(f"    Lecteur {drive} : {free_gb:.2f} Go libres sur {total_gb:.2f} Go ({percent_free:.1f}% libres)")
        if percent_free < 10:  # seuil critique : moins de 10% libre
            problematic_disks.append(drive)

    # 2. Si des lecteurs sont critiques, chercher les gros fichiers
    if problematic_disks:
        lines.append("")
        lines.append("[2] Recherche des fichiers volumineux sur les lecteurs critiques :")
        for drive in problematic_disks:
            large_files = find_large_files(drive)
            if large_files:
                lines.append(f"    Fichiers de plus de 500 Mo sur {drive} :")
                for path, size_mb in large_files:
                    lines.append(f"        - {path} ({size_mb:.1f} Mo)")
            else:
                lines.append(f"    Aucun fichier volumineux trouvé sur {drive}.")
    else:
        lines.append("")
        lines.append("[2] Aucun lecteur critique détecté.")

    # 3. Conclusion
    lines.append("")
    lines.append("=== Diagnostic ===")
    if problematic_disks:
        lines.append("Cause probable : espace disque insuffisant sur un ou plusieurs lecteurs.")
        lines.append("Action corrective suggérée : supprimer des fichiers inutiles, vider la corbeille, exécuter le nettoyage de disque (cleanmgr), ou déplacer des données vers un autre support.")
    else:
        lines.append("Tous les lecteurs ont un espace libre suffisant. Aucun problème d'espace disque détecté.")

    return "\n".join(lines)


if __name__ == "__main__":
    print(run_disk_diagnostic())