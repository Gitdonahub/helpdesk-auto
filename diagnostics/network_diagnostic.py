import subprocess
import sys

def run_command(command):
    """Exécute une commande et retourne (succès, sortie)."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        # Retourne exactement deux éléments : (booléen succès, chaîne sortie)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def ping(host):
    """Teste la connectivité ICMP vers un hôte."""
    result = run_command(["ping", "-n", "1", host])
    return result[0]   # premier élément = succès

def dns_lookup(domain):
    """Teste la résolution DNS d'un domaine."""
    result = run_command(["nslookup", domain])
    return result[0]

def get_default_gateway():
    """Récupère la passerelle par défaut à partir d'ipconfig."""
    result = run_command(["ipconfig"])
    if not result[0]:
        return None
    output = result[1]
    for line in output.splitlines():
        if "Passerelle par défaut" in line or "Default Gateway" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                gateway = parts[-1].strip()
                if "." in gateway:
                    return gateway
    return None

def get_ip_address():
    """Récupère l'adresse IPv4 de la machine à partir d'ipconfig."""
    result = run_command(["ipconfig"])
    if not result[0]:
        return None
    output = result[1]
    for line in output.splitlines():
        if "Adresse IPv4" in line or "IPv4 Address" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                ip = parts[-1].strip()
                if "." in ip:
                    return ip
    return None

def check_dns_service():
    """Vérifie que le service Client DNS est en cours d'exécution."""
    result = run_command(["sc", "query", "Dnscache"])
    if not result[0]:
        return False
    output = result[1]
    if "RUNNING" in output.upper():
        return True
    return False

def run_diagnostic():
    """Exécute le diagnostic réseau complet et retourne un texte détaillé."""
    lines = []
    lines.append("=== Diagnostic réseau détaillé ===")

    # 1. Adresse IP
    ip_address = get_ip_address()
    if ip_address is None:
        lines.append("Impossible d'obtenir une adresse IP. Carte réseau désactivée ou problème matériel ?")
        return "\n".join(lines)
    lines.append(f"Adresse IP détectée : {ip_address}")

    if ip_address.startswith("169.254."):
        lines.append("Adresse IP APIPA détectée (169.254.x.x). Cela signifie que le DHCP a échoué.")
        lines.append("Cause probable : problème DHCP (serveur DHCP injoignable, câble défectueux, ou configuration réseau).")
        return "\n".join(lines)

    # 2. Service DNS
    lines.append("")
    lines.append("[0] Vérification du service Client DNS...")
    if check_dns_service():
        lines.append("    -> Service DNS en cours d'exécution.")
    else:
        lines.append("    -> Service DNS arrêté ou introuvable.")
        lines.append("Cause probable : le service Client DNS est arrêté. Action corrective : démarrer le service.")
        return "\n".join(lines)

    # 3. Passerelle
    gateway = get_default_gateway()
    if gateway is None:
        lines.append("Impossible de détecter la passerelle par défaut. Vérifiez votre configuration IP.")
        return "\n".join(lines)
    lines.append(f"Passerelle par défaut détectée : {gateway}")

    # 4. Ping passerelle (avec sortie brute)
    lines.append("")
    lines.append("[1] Test de connectivité vers la passerelle...")
    success, output = run_command(["ping", "-n", "1", gateway])
    if success:
        lines.append("    -> Passerelle joignable.")
        lines.append("    Détail de la commande :")
        lines.append("    " + output.strip().replace("\n", "\n    "))
    else:
        lines.append("    -> Passerelle injoignable.")
        lines.append("    Détail de la commande :")
        lines.append("    " + output.strip().replace("\n", "\n    "))
        lines.append("Cause probable : problème local (câble débranché, Wi-Fi désactivé, carte réseau en panne, ou mauvaise configuration IP).")
        lines.append("Vérifiez votre connexion physique et votre configuration réseau.")
        return "\n".join(lines)

    # 5. Ping serveur DNS
    lines.append("")
    lines.append("[2] Test de connectivité vers le serveur DNS 8.8.8.8...")
    success, output = run_command(["ping", "-n", "1", "8.8.8.8"])
    if success:
        lines.append("    -> DNS joignable.")
        lines.append("    Détail : " + output.strip().replace("\n", "\n    "))
    else:
        lines.append("    -> DNS injoignable.")
        lines.append("    Détail : " + output.strip().replace("\n", "\n    "))
        lines.append("Cause probable : problème de routage ou de connectivité au-delà de la passerelle.")
        lines.append("Vérifiez votre routeur ou contactez votre fournisseur d'accès.")
        return "\n".join(lines)

    # 6. Résolution DNS
    lines.append("")
    lines.append("[3] Test de résolution DNS (google.com)...")
    success, output = run_command(["nslookup", "google.com"])
    if success:
        lines.append("    -> Résolution réussie.")
        lines.append("    Détail : " + output.strip().replace("\n", "\n    "))
    else:
        lines.append("    -> Échec de la résolution.")
        lines.append("    Détail : " + output.strip().replace("\n", "\n    "))
        lines.append("Cause probable : problème DNS (le serveur DNS ne répond pas ou configuration incorrecte).")
        lines.append("Action corrective suggérée : exécuter 'ipconfig /flushdns' et vérifier les serveurs DNS.")
        return "\n".join(lines)

    # Si tout passe
    lines.append("")
    lines.append("=== Diagnostic ===")
    lines.append("Tous les tests sont bons. Votre connexion Internet semble fonctionnelle.")
    return "\n".join(lines)

# Si on exécute ce fichier directement, on lance le diagnostic en mode console
if __name__ == "__main__":
    print(run_diagnostic())