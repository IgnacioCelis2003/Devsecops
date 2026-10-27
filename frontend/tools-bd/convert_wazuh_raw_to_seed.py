"""
Conversor de respuestas crudas de Wazuh Indexer (OpenSearch/Elasticsearch como datos_wazuh4.json)
al formato de seed para PostgreSQL (datos_wazuh.json) usado por vuln-api.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

def convert_raw_to_seed(raw_file_path: str, output_file_path: str = None, connection_id: int = 1):
    raw_path = Path(raw_file_path)
    if not raw_path.exists():
        print(f"Error: No existe el archivo {raw_path}")
        return

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    hits = raw_data.get("hits", {}).get("hits", [])
    if not hits:
        print("No se encontraron hits en el archivo.")
        return

    converted_vulns = []
    converted_history = []
    
    for idx, hit in enumerate(hits, start=1001):
        src = hit.get("_source", {})
        agent = src.get("agent", {})
        host_os = src.get("host", {}).get("os", {})
        pkg = src.get("package", {})
        vuln = src.get("vulnerability", {})

        cve_id = vuln.get("id")
        if not cve_id:
            continue

        severity = (vuln.get("severity") or "UNKNOWN").upper()
        if severity == "-":
            severity = "UNKNOWN"

        score_base = vuln.get("score", {}).get("base")
        if score_base == -1.0 or score_base is None:
            score_base = None

        detected_at = vuln.get("detected_at") or datetime.now(timezone.utc).isoformat()
        published_at = vuln.get("published_at")

        vuln_record = {
            "id": idx,
            "connection_id": connection_id,
            "status": "ACTIVE",
            "agent_id": agent.get("id", "002"),
            "agent_name": agent.get("name", "ubuntu2204-vm2-lab"),
            "tags": ["real-wazuh-import", host_os.get("platform", "linux")],
            "os_full": host_os.get("full"),
            "os_platform": host_os.get("platform"),
            "os_version": host_os.get("version"),
            "package_name": pkg.get("name"),
            "package_version": pkg.get("version"),
            "package_type": pkg.get("type", "deb"),
            "package_arch": pkg.get("architecture", "amd64"),
            "cve_id": cve_id,
            "severity": severity,
            "score_base": score_base,
            "score_version": vuln.get("score", {}).get("version", "3.1"),
            "detected_at": detected_at,
            "published_at": published_at,
            "description": vuln.get("description"),
            "reference": vuln.get("reference"),
            "scanner_vendor": "Wazuh Vulnerability Detector (Real)",
            "first_seen": detected_at,
            "last_seen": detected_at,
        }
        converted_vulns.append(vuln_record)

        converted_history.append({
            "id": idx,
            "vulnerability_id": idx,
            "action": "DETECTED",
            "details": f"Vulnerabilidad real detectada por agente Wazuh {agent.get('name')}",
            "timestamp": detected_at
        })

    result = {
        "users": [],
        "wazuh_connections": [],
        "user_interactions": [],
        "wazuh_vulnerabilities": converted_vulns,
        "vulnerability_history": converted_history
    }

    if output_file_path:
        out_path = Path(output_file_path)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[OK] Convertidas {len(converted_vulns)} vulnerabilidades a: {out_path}")
    else:
        print(f"[OK] Procesadas {len(converted_vulns)} vulnerabilidades reales.")

    return result

if __name__ == "__main__":
    src_file = sys.argv[1] if len(sys.argv) > 1 else "vuln-api/app/datos_wazuh4.json"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "vuln-api/app/datos_reales_convertidos.json"
    convert_raw_to_seed(src_file, out_file)
