# performance_diagnostics.py

import subprocess
import json
import os

POWERSHELL = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"),
                           "System32", "WindowsPowerShell", "v1.0", "powershell.exe")

def run_command(command):
    """Exécute une commande et retourne (succès, sortie)."""
    try:
        result = subprocess.run(command, capture_output=True, text=True,encoding="cp1252",errors="replace" , timeout=15)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def get_cpu_usage():
    """Utilisation CPU via les compteurs de performance (fiable sur VM)."""
    ps = (
        "(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor "
        "| Where-Object { $_.Name -eq '_Total' }).PercentProcessorTime"
    )
    success, output = run_command([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps])
    if success:
        val = output.strip().replace("\r", "").replace("\n", "")
        if val:
            try:
                return float(val.replace(",", "."))
            except:
                pass
    return None

def get_memory_info():
    """Retourne (total_GB, libre_GB, pourcentage_utilise) via PowerShell JSON."""
    ps = (
        "$os = Get-CimInstance Win32_OperatingSystem; "
        "$obj = [PSCustomObject]@{ "
        "Total = [int64]$os.TotalVisibleMemorySize; "
        "Free = [int64]$os.FreePhysicalMemory }; "
        "$obj | ConvertTo-Json -Compress"
    )
    success, output = run_command([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps])
    if not success:
        return None
    try:
        data = json.loads(output.strip())
        total_kb = int(data["Total"])
        free_kb = int(data["Free"])
        total_gb = total_kb / (1024**2)
        free_gb = free_kb / (1024**2)
        used_percent = ((total_gb - free_gb) / total_gb) * 100
        return total_gb, free_gb, used_percent
    except Exception as e:
        return None

def get_top_processes(limit=5):
    """Retourne les processus les plus gourmands via sortie texte simple."""
    ps = (
        f"Get-Process | Where-Object {{ $_.CPU -ne $null }} | "
        f"Sort-Object CPU -Descending | Select-Object -First {limit} | "
        f"ForEach-Object {{ Write-Output ($_.Name + '|' + $_.CPU) }}"
    )
    success, output = run_command([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps])
    if not success:
        return []
    processes = []
    for line in output.splitlines():
        line = line.strip().replace("\r", "")
        if "|" in line:
            parts = line.split("|")
            if len(parts) == 2:
                try:
                    name = parts[0].strip()
                    cpu = float(parts[1].strip().replace(",", "."))
                    processes.append((name, cpu))
                except:
                    continue
    return processes

def run_performance_diagnostic():
    """Exécute le diagnostic de performance et retourne un texte détaillé."""
    lines = []
    lines.append("=== Diagnostic performance / lenteur ===")

    # 1. CPU
    lines.append("")
    lines.append("[1] Vérification de l'utilisation du processeur...")
    cpu_usage = get_cpu_usage()
    if cpu_usage is not None:
        lines.append(f"    Utilisation CPU : {cpu_usage:.1f}%")
        if cpu_usage > 80:
            lines.append("    Attention : charge CPU élevée.")
        else:
            lines.append("    Charge CPU normale.")
    else:
        lines.append("    Impossible de récupérer l'utilisation CPU.")

    # 2. Mémoire
    lines.append("")
    lines.append("[2] Vérification de la mémoire...")
    mem_info = get_memory_info()
    if mem_info:
        total_gb, free_gb, used_percent = mem_info
        lines.append(f"    Mémoire totale : {total_gb:.2f} Go")
        lines.append(f"    Mémoire libre : {free_gb:.2f} Go")
        lines.append(f"    Mémoire utilisée : {used_percent:.1f}%")
        if used_percent > 85:
            lines.append("    Attention : mémoire presque saturée.")
        else:
            lines.append("    Mémoire suffisante.")
    else:
        lines.append("    Impossible de récupérer les informations mémoire.")

    # 3. Processus
    lines.append("")
    lines.append("[3] Processus les plus gourmands en CPU :")
    top_procs = get_top_processes()
    if top_procs:
        for name, cpu_time in top_procs:
            lines.append(f"    - {name} (temps CPU : {cpu_time:.2f} s)")
    else:
        lines.append("    Aucun processus anormal détecté.")

    # 4. Conclusion
    lines.append("")
    lines.append("=== Diagnostic ===")
    if cpu_usage is not None and cpu_usage > 80:
        lines.append("Cause probable : charge CPU élevée. Un programme utilise beaucoup de ressources.")
        lines.append("Action corrective suggérée : fermez les applications inutiles, vérifiez les processus dans le gestionnaire des tâches.")
    elif mem_info and mem_info[2] > 85:
        lines.append("Cause probable : mémoire vive saturée.")
        lines.append("Action corrective suggérée : fermez des programmes, redémarrez l'ordinateur, ou ajoutez de la RAM.")
    else:
        lines.append("Aucun problème de performance majeur détecté. La lenteur peut venir d'un autre facteur (disque, réseau, etc.).")
        lines.append("Action corrective suggérée : vérifiez l'espace disque et les mises à jour système.")

    return "\n".join(lines)


if __name__ == "__main__":
    print(run_performance_diagnostic())