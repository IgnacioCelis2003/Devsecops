"""
Script para generar un dataset de alta escala de vulnerabilidades Wazuh para pruebas de paginación y filtros.
Mantiene compatibilidad exacta con el schema de vuln-api/app/seed_data.py
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Semilla fija para reproducibilidad
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
TARGET_FILE = BASE_DIR / "vuln-api" / "app" / "datos_wazuh.json"
BACKUP_FILE = BASE_DIR / "vuln-api" / "app" / "datos_wazuh.original.json"

USERS = [
    {
        "id": 1,
        "username": "admin_sys",
        "password_hash": "$2b$12$e83B/11Y29p3.q.8O.713eI6m9q1YyL7m8K1j9H0i1G2f3E4d5C6a",
        "is_active": True,
        "is_default_password": False,
        "role": "admin",
        "email": "admin_sys@example.local",
        "tags": ["administration", "production"],
        "created_at": "2026-01-10T08:00:00Z"
    },
    {
        "id": 2,
        "username": "analyst_security",
        "password_hash": "$2b$12$K89J21mN34p5.q.6O.814fJ7n0r2ZzM8n9L2k0I1H2G3F4E5D6b",
        "is_active": True,
        "is_default_password": True,
        "role": "security_analyst",
        "email": "analyst_security@example.local",
        "tags": ["security", "vulnerability-management"],
        "created_at": "2026-02-01T09:30:00Z"
    },
    {
        "id": 3,
        "username": "auditor_guest",
        "password_hash": "$2b$12$L90K32oO45q6.r.7P.915gK8o1s3AaN9o0M3l1J2I3H4G5F6E7c",
        "is_active": False,
        "is_default_password": True,
        "role": "auditor",
        "email": "auditor_guest@example.local",
        "tags": ["audit", "read-only"],
        "created_at": "2026-02-15T14:15:00Z"
    }
]

CONNECTIONS = [
    {
        "id": 1,
        "name": "Cluster-Produccion-US",
        "indexer_url": "https://indexer-prod.internal.local:9200",
        "wazuh_user": "wazuh_admin",
        "wazuh_password": "EncryptedPasswordKey_019283",
        "is_active": True,
        "created_at": "2026-01-10T08:30:00Z",
        "tested": True,
        "last_tested_at": "2026-03-01T12:00:00Z",
        "last_test_ok": True
    },
    {
        "id": 2,
        "name": "Cluster-Staging-EU",
        "indexer_url": "https://indexer-stage.internal.local:9200",
        "wazuh_user": "wazuh_stage",
        "wazuh_password": "EncryptedPasswordKey_473829",
        "is_active": True,
        "created_at": "2026-01-15T10:00:00Z",
        "tested": True,
        "last_tested_at": "2026-03-01T11:45:00Z",
        "last_test_ok": False
    },
    {
        "id": 3,
        "name": "Cluster-DMZ-LATAM",
        "indexer_url": "https://indexer-dmz.internal.local:9200",
        "wazuh_user": "wazuh_dmz",
        "wazuh_password": "EncryptedPasswordKey_883921",
        "is_active": True,
        "created_at": "2026-02-01T10:00:00Z",
        "tested": True,
        "last_tested_at": "2026-03-01T09:00:00Z",
        "last_test_ok": True
    }
]

AGENTS = [
    {
        "agent_id": "001",
        "agent_name": "srv-db-primary",
        "conn_id": 1,
        "os_full": "Ubuntu 22.04.3 LTS (Jammy Jellyfish)",
        "os_platform": "ubuntu",
        "os_version": "22.04",
        "package_type": "deb",
        "package_arch": "amd64",
        "tags": ["production", "database", "linux", "critical-inventory"]
    },
    {
        "agent_id": "002",
        "agent_name": "srv-app-web01",
        "conn_id": 1,
        "os_full": "Red Hat Enterprise Linux 9.2 (Plow)",
        "os_platform": "rhel",
        "os_version": "9.2",
        "package_type": "rpm",
        "package_arch": "x86_64",
        "tags": ["production", "web", "linux", "internet-facing"]
    },
    {
        "agent_id": "003",
        "agent_name": "srv-app-web02",
        "conn_id": 1,
        "os_full": "Red Hat Enterprise Linux 9.2 (Plow)",
        "os_platform": "rhel",
        "os_version": "9.2",
        "package_type": "rpm",
        "package_arch": "x86_64",
        "tags": ["production", "web", "backend", "load-balanced"]
    },
    {
        "agent_id": "104",
        "agent_name": "srv-auth-ldap",
        "conn_id": 1,
        "os_full": "Debian GNU/Linux 12 (bookworm)",
        "os_platform": "debian",
        "os_version": "12",
        "package_type": "deb",
        "package_arch": "amd64",
        "tags": ["production", "identity", "ldap", "internal"]
    },
    {
        "agent_id": "105",
        "agent_name": "k8s-node-worker-01",
        "conn_id": 2,
        "os_full": "Debian GNU/Linux 12 (bookworm)",
        "os_platform": "debian",
        "os_version": "12",
        "package_type": "deb",
        "package_arch": "amd64",
        "tags": ["staging", "kubernetes", "worker", "container-runtime"]
    },
    {
        "agent_id": "106",
        "agent_name": "k8s-node-worker-02",
        "conn_id": 2,
        "os_full": "Debian GNU/Linux 12 (bookworm)",
        "os_platform": "debian",
        "os_version": "12",
        "package_type": "deb",
        "package_arch": "amd64",
        "tags": ["staging", "kubernetes", "worker", "pod-runner"]
    },
    {
        "agent_id": "201",
        "agent_name": "ubuntu2204-vm2-lab",
        "conn_id": 3,
        "os_full": "Ubuntu 22.04.5 LTS (Jammy Jellyfish)",
        "os_platform": "ubuntu",
        "os_version": "22.04.5",
        "package_type": "deb",
        "package_arch": "amd64",
        "tags": ["lab", "wazuh-agent", "real-scan", "testing"]
    },
    {
        "agent_id": "202",
        "agent_name": "gw-reverse-proxy",
        "conn_id": 3,
        "os_full": "Alpine Linux v3.19",
        "os_platform": "alpine",
        "os_version": "3.19",
        "package_type": "apk",
        "package_arch": "x86_64",
        "tags": ["dmz", "edge", "nginx", "proxy"]
    }
]

KNOWN_PACKAGES = [
    ("openssl", ["3.0.2-0ubuntu1.10", "3.0.7-1", "1.1.1w-1", "3.1.4-1"]),
    ("curl", ["7.81.0-1ubuntu1.14", "8.2.1-1", "7.76.1-23.el9", "8.5.0-1"]),
    ("xz", ["5.6.1-1", "5.4.1-0.2", "5.2.5-3.el9", "5.6.0-1"]),
    ("runc", ["1.1.5+ds1-1+b1", "1.1.9-0", "1.0.3-2", "1.1.12-1"]),
    ("glibc", ["2.35-0ubuntu3.4", "2.34-60.el9", "2.36-9+deb12u3", "2.38-1"]),
    ("linux-image-5.15.0-187-generic", ["5.15.0-187.197", "5.15.0-184.194"]),
    ("linux-image-6.1.0-18-amd64", ["6.1.76-1", "6.1.69-1"]),
    ("sudo", ["1.9.9-1ubuntu2.4", "1.9.5p2-1", "1.9.12p1-1.el9"]),
    ("nginx", ["1.18.0-6ubuntu14.4", "1.24.0-1", "1.20.1-14.el9", "1.24.0-r6"]),
    ("systemd", ["249.11-0ubuntu3.11", "252.19-1~deb12u1", "252-18.el9"]),
    ("containerd", ["1.6.12-0ubuntu1~22.04.1", "1.7.13-1", "1.6.28-1"]),
    ("python3", ["3.10.12-1~22.04.3", "3.11.2-1+b1", "3.9.18-1.el9"]),
    ("git", ["2.34.1-1ubuntu1.10", "2.39.2-1.1", "2.43.0-1"]),
    ("tar", ["1.34+dfsg-1ubuntu0.1.22.04.1", "1.34+dfsg-1.2", "1.34-6.el9"]),
    ("bash", ["5.1-6ubuntu1", "5.2.15-2+b2", "5.1.8-8.el9"]),
    ("bind9", ["9.18.18-0ubuntu0.22.04.1", "9.18.19-1~deb12u1"]),
    ("redis", ["6.0.16-1ubuntu0.1", "7.0.15-1~deb12u1", "6.2.7-1.el9"]),
    ("postgresql-client", ["14+238", "15+248", "16+256"]),
    ("ca-certificates", ["20230311ubuntu0.22.04.1", "20230311", "20240203"]),
    ("util-linux", ["2.37.2-4ubuntu3.4", "2.38.1-5+deb12u1", "2.37.4-15.el9"])
]

CVES_CATALOG = [
    # Critical
    ("CVE-2024-3094", "CRITICAL", 10.0, "Malicious backdoor in upstream xz/liblzma leading to SSH authentication bypass."),
    ("CVE-2021-44228", "CRITICAL", 10.0, "Apache Log4j2 JNDI features used in configuration do not protect against attacker controlled LDAP."),
    ("CVE-2024-6387", "CRITICAL", 9.8, "regreSSHion: Remote Unauthenticated Code Execution in OpenSSH server signal handler race condition."),
    ("CVE-2023-4863", "CRITICAL", 9.8, "Heap buffer overflow in libwebp allowing remote arbitrary code execution."),
    ("CVE-2021-3156", "CRITICAL", 9.8, "Heap-based buffer overflow in Sudo (Baron Samedit) allows privilege escalation to root."),
    ("CVE-2022-22965", "CRITICAL", 9.8, "Spring4Shell: RCE in Spring Framework via Data Binding on JDK9+."),
    ("CVE-2023-32360", "CRITICAL", 9.6, "Authentication bypass in internal API management component allowing unauthorized operations."),
    ("CVE-2023-44487", "HIGH", 7.5, "HTTP/2 Rapid Reset Attack causing denial of service on high-concurrency web endpoints."),
    
    # High
    ("CVE-2024-0727", "HIGH", 7.5, "Processing maliciously formatted PKCS12 file in OpenSSL leads to denial of service."),
    ("CVE-2023-38545", "HIGH", 8.1, "SOCKS5 heap buffer overflow vulnerability in libcurl during hostname resolution."),
    ("CVE-2024-21626", "HIGH", 8.6, "Leaky file descriptor issue in runc allowing container breakout via /proc/self/cwd."),
    ("CVE-2023-4911", "HIGH", 7.8, "Looney Tunables: Local privilege escalation in glibc dynamic loader GLIBC_TUNABLES."),
    ("CVE-2026-45957", "HIGH", 7.1, "Linux kernel: fix rcu_read_unlock deadloop due to softirq under preempt full."),
    ("CVE-2026-43153", "HIGH", 7.8, "Linux kernel: memory corruption during socket teardown in network subsystem."),
    ("CVE-2026-64412", "HIGH", 7.1, "Race condition in kernel filesystem mount table handling."),
    ("CVE-2025-39905", "HIGH", 7.0, "Integer overflow in package verification routine during batch uncompress."),
    ("CVE-2024-1086", "HIGH", 7.8, "Use-after-free vulnerability in the Linux kernel netfilter: nf_tables component."),
    ("CVE-2023-24329", "HIGH", 7.5, "Python urllib parse module bypass allowing SSRF and URL validation evasion."),
    ("CVE-2023-38039", "HIGH", 7.5, "Curl HTTP headers buffer accumulation leading to denial of service."),
    ("CVE-2023-5678", "HIGH", 7.5, "OpenSSL generates overly large primes during DH key generation leading to CPU exhaustion."),
    
    # Medium
    ("CVE-2026-43161", "MEDIUM", 5.5, "Information disclosure in kernel debug trace buffer commit mechanism."),
    ("CVE-2026-53168", "MEDIUM", 5.5, "Unchecked return value in generic image descriptor parser."),
    ("CVE-2026-43162", "MEDIUM", 5.5, "Timing side-channel in crypto modular exponentiation routine."),
    ("CVE-2026-43165", "MEDIUM", 5.5, "Memory leak during repeated TLS renegotiation handshakes under high load."),
    ("CVE-2026-43201", "MEDIUM", 5.5, "Out of bounds read in string formatting utility function."),
    ("CVE-2023-28322", "MEDIUM", 5.3, "Curl wildcard SSL certificate match false positive on adjacent subdomains."),
    ("CVE-2023-38546", "MEDIUM", 3.7, "Curl cookie injection via file:// URLs in specific build configurations."),
    ("CVE-2023-46218", "MEDIUM", 6.5, "Curl cookie domain mixed case normalization flaw allowing cross-site cookie read."),
    ("CVE-2024-24576", "MEDIUM", 6.8, "Command injection on Windows platform when invoking batch files with unescaped arguments."),
    ("CVE-2023-2650", "MEDIUM", 5.3, "OpenSSL ASN.1 object parsing quadratic time consumption vulnerability."),
    
    # Low
    ("CVE-2023-29491", "LOW", 3.3, "Ncurses library local denial of service via craft tic file."),
    ("CVE-2022-48554", "LOW", 3.3, "Local information disclosure in kernel audit subsystem logs."),
    ("CVE-2023-4039", "LOW", 2.8, "Compiler-generated stack layout optimization in AArch64 can reduce canaries."),
    ("CVE-2023-5178", "LOW", 3.1, "Minor memory leak in Linux kernel NVMe-oF/TCP subsystem."),
    ("CVE-2024-2236", "LOW", 2.5, "Verbose error message revealing path structure on malformed configuration file.")
]

STATUSES = ["ACTIVE", "ACTIVE", "ACTIVE", "IN_REVIEW", "MITIGATED", "RESOLVED"]


def generate_dataset(total_vulns: int = 300) -> dict:
    vulns = []
    histories = []
    interactions = []
    
    seen_unique = set()
    vuln_id = 101
    hist_id = 1
    
    now = datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc)
    
    # Generar primero las 4 originales para no romper referencias conocidas
    original_first_four = [
        {
            "id": 101,
            "connection_id": 1,
            "status": "ACTIVE",
            "agent_id": "001",
            "agent_name": "srv-db-primary",
            "tags": ["production", "database", "linux", "critical-inventory"],
            "os_full": "Ubuntu 22.04.3 LTS (Jammy Jellyfish)",
            "os_platform": "ubuntu",
            "os_version": "22.04",
            "package_name": "openssl",
            "package_version": "3.0.2-0ubuntu1.10",
            "package_type": "deb",
            "package_arch": "amd64",
            "cve_id": "CVE-2024-0727",
            "severity": "HIGH",
            "score_base": 7.5,
            "score_version": "3.1",
            "detected_at": "2026-02-20T04:12:00Z",
            "published_at": "2024-01-25T00:00:00Z",
            "description": "Processing a maliciously formatted PKCS12 file may lead to a denial of service.",
            "reference": "https://nvd.nist.gov/vuln/detail/CVE-2024-0727",
            "scanner_vendor": "Wazuh Vulnerability Detector",
            "first_seen": "2026-02-20T04:12:00Z",
            "last_seen": "2026-03-01T06:00:00Z"
        },
        {
            "id": 102,
            "connection_id": 1,
            "status": "ACTIVE",
            "agent_id": "002",
            "agent_name": "srv-app-web01",
            "tags": ["production", "web", "linux", "internet-facing"],
            "os_full": "Red Hat Enterprise Linux 9.2 (Plow)",
            "os_platform": "rhel",
            "os_version": "9.2",
            "package_name": "xz",
            "package_version": "5.6.1",
            "package_type": "rpm",
            "package_arch": "x86_64",
            "cve_id": "CVE-2024-3094",
            "severity": "CRITICAL",
            "score_base": 10.0,
            "score_version": "3.1",
            "detected_at": "2026-02-22T02:00:00Z",
            "published_at": "2024-03-29T00:00:00Z",
            "description": "Malicious code was discovered in xz-utils versions 5.6.0 and 5.6.1 leading to SSH authentication bypass.",
            "reference": "https://nvd.nist.gov/vuln/detail/CVE-2024-3094",
            "scanner_vendor": "Wazuh Vulnerability Detector",
            "first_seen": "2026-02-22T02:00:00Z",
            "last_seen": "2026-03-01T06:00:00Z"
        },
        {
            "id": 103,
            "connection_id": 1,
            "status": "MITIGATED",
            "agent_id": "001",
            "agent_name": "srv-db-primary",
            "tags": ["production", "database", "linux", "remediated"],
            "os_full": "Ubuntu 22.04.3 LTS (Jammy Jellyfish)",
            "os_platform": "ubuntu",
            "os_version": "22.04",
            "package_name": "curl",
            "package_version": "7.81.0-1ubuntu1.14",
            "package_type": "deb",
            "package_arch": "amd64",
            "cve_id": "CVE-2023-38545",
            "severity": "HIGH",
            "score_base": 8.1,
            "score_version": "3.1",
            "detected_at": "2026-01-15T08:00:00Z",
            "published_at": "2023-10-11T00:00:00Z",
            "description": "SOCKS5 heap buffer overflow vulnerability in curl.",
            "reference": "https://nvd.nist.gov/vuln/detail/CVE-2023-38545",
            "scanner_vendor": "Wazuh Vulnerability Detector",
            "first_seen": "2026-01-15T08:00:00Z",
            "last_seen": "2026-02-10T18:00:00Z"
        },
        {
            "id": 104,
            "connection_id": 2,
            "status": "ACTIVE",
            "agent_id": "105",
            "agent_name": "k8s-node-worker-01",
            "tags": ["staging", "kubernetes", "worker", "container-runtime"],
            "os_full": "Debian GNU/Linux 12 (bookworm)",
            "os_platform": "debian",
            "os_version": "12",
            "package_name": "runc",
            "package_version": "1.1.5+ds1-1+b1",
            "package_type": "deb",
            "package_arch": "amd64",
            "cve_id": "CVE-2024-21626",
            "severity": "HIGH",
            "score_base": 8.6,
            "score_version": "3.1",
            "detected_at": "2026-02-25T11:20:00Z",
            "published_at": "2024-01-31T00:00:00Z",
            "description": "Leaky file descriptor issue in runc allowing container breakout.",
            "reference": "https://nvd.nist.gov/vuln/detail/CVE-2024-21626",
            "scanner_vendor": "Wazuh Vulnerability Detector",
            "first_seen": "2026-02-25T11:20:00Z",
            "last_seen": "2026-03-01T06:00:00Z"
        }
    ]
    
    for row in original_first_four:
        key = (row["connection_id"], row["agent_id"], row["package_name"], row["package_version"], row["cve_id"])
        seen_unique.add(key)
        vulns.append(row)
        vuln_id = max(vuln_id, row["id"] + 1)
        
        # Historial para las 4 primeras
        histories.append({
            "id": hist_id,
            "vulnerability_id": row["id"],
            "action": "DETECTED",
            "details": "Vulnerabilidad detectada durante escaneo de seguridad inicial.",
            "timestamp": row["detected_at"]
        })
        hist_id += 1
        if row["status"] != "ACTIVE":
            histories.append({
                "id": hist_id,
                "vulnerability_id": row["id"],
                "action": "STATUS_CHANGED",
                "details": f"Estado actualizado a {row['status']}.",
                "timestamp": row["last_seen"]
            })
            hist_id += 1

    # Generar el resto hasta llegar a total_vulns
    attempts = 0
    max_attempts = total_vulns * 50
    while len(vulns) < total_vulns and attempts < max_attempts:
        attempts += 1
        agent = random.choice(AGENTS)
        pkg_name, versions = random.choice(KNOWN_PACKAGES)
        pkg_ver = random.choice(versions)
        cve_id, severity, score_base, description = random.choice(CVES_CATALOG)
        
        # Evitar violar la restricción UNIQUE (connection_id, agent_id, package_name, package_version, cve_id)
        key = (agent["conn_id"], agent["agent_id"], pkg_name, pkg_ver, cve_id)
        if key in seen_unique:
            continue
        seen_unique.add(key)
        
        days_ago_detected = random.randint(1, 90)
        detected_time = now - timedelta(days=days_ago_detected, hours=random.randint(1, 23), minutes=random.randint(0, 59))
        days_ago_last = random.randint(0, min(days_ago_detected, 15))
        last_seen_time = now - timedelta(days=days_ago_last, hours=random.randint(0, 12))
        published_days_ago = days_ago_detected + random.randint(100, 700)
        published_time = now - timedelta(days=published_days_ago)
        
        status = random.choice(STATUSES)
        
        # Tags dinámicos según agente y severidad
        tags = list(agent["tags"])
        if severity == "CRITICAL":
            tags.append("urgent-action")
        elif severity == "HIGH":
            tags.append("high-priority")
        
        vuln_record = {
            "id": vuln_id,
            "connection_id": agent["conn_id"],
            "status": status,
            "agent_id": agent["agent_id"],
            "agent_name": agent["agent_name"],
            "tags": tags,
            "os_full": agent["os_full"],
            "os_platform": agent["os_platform"],
            "os_version": agent["os_version"],
            "package_name": pkg_name,
            "package_version": pkg_ver,
            "package_type": agent["package_type"],
            "package_arch": agent["package_arch"],
            "cve_id": cve_id,
            "severity": severity,
            "score_base": score_base,
            "score_version": "3.1",
            "detected_at": detected_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "published_at": published_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": description,
            "reference": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "scanner_vendor": "Wazuh Vulnerability Detector",
            "first_seen": detected_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_seen": last_seen_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        vulns.append(vuln_record)
        
        # Historial de eventos
        histories.append({
            "id": hist_id,
            "vulnerability_id": vuln_id,
            "action": "DETECTED",
            "details": f"Detectado por Wazuh Vulnerability Detector en {agent['agent_name']}.",
            "timestamp": detected_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        hist_id += 1
        
        if status in ("MITIGATED", "RESOLVED", "IN_REVIEW"):
            histories.append({
                "id": hist_id,
                "vulnerability_id": vuln_id,
                "action": "STATUS_CHANGED",
                "details": f"Analista de seguridad actualizó el estado a {status}.",
                "timestamp": last_seen_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            })
            hist_id += 1
            
        vuln_id += 1
        
    # Interacciones de usuarios
    for i in range(1, 25):
        user = random.choice(USERS)
        endpoint = random.choice([
            "/api/v1/vulns?limit=50&offset=0",
            "/api/v1/vulns?severity=CRITICAL",
            "/api/v1/vulns?status=ACTIVE",
            "/api/v1/wazuh-connections/1/sync",
            "/api/v1/wazuh-connections/2/test",
            "/api/v1/vulns?connection_id=1"
        ])
        interactions.append({
            "id": i,
            "user_id": user["id"],
            "endpoint": endpoint,
            "method": "POST" if "sync" in endpoint or "test" in endpoint else "GET",
            "details": f"Consulta paginada o sincronización ejecutada por {user['username']}",
            "timestamp": (now - timedelta(hours=i*2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        
    return {
        "users": USERS,
        "wazuh_connections": CONNECTIONS,
        "user_interactions": interactions,
        "wazuh_vulnerabilities": vulns,
        "vulnerability_history": histories
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generador de datos a gran escala para Wazuh API")
    parser.add_argument("--count", type=int, default=300, help="Cantidad de vulnerabilidades a generar (default: 300)")
    parser.add_argument("--output", type=str, default=str(TARGET_FILE), help="Ruta del archivo JSON de salida")
    parser.add_argument("--backup", action="store_true", default=True, help="Crear backup del archivo actual")
    args = parser.parse_args()
    
    out_path = Path(args.output)
    if args.backup and out_path.exists() and not BACKUP_FILE.exists():
        import shutil
        shutil.copy2(out_path, BACKUP_FILE)
        print(f"[+] Backup guardado en: {BACKUP_FILE}")
        
    print(f"[*] Generando dataset con {args.count} vulnerabilidades...")
    dataset = generate_dataset(total_vulns=args.count)
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    print(f"[OK] Archivo generado exitosamente en: {out_path}")
    print(f"    - Conexiones: {len(dataset['wazuh_connections'])}")
    print(f"    - Vulnerabilidades: {len(dataset['wazuh_vulnerabilities'])}")
    print(f"    - Historiales: {len(dataset['vulnerability_history'])}")
    print(f"    - Interacciones: {len(dataset['user_interactions'])}")


if __name__ == "__main__":
    main()
