"""
Herramienta para visualizar e inspeccionar respuestas JSON crudas de Wazuh Indexer (OpenSearch/Elasticsearch)
como 'datos_wazuh4.json'.
"""
import json
import sys
from pathlib import Path

def view_raw_wazuh(file_path: str):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: No existe el archivo {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 80)
    print(f" REPORTE DE EXTRACCIÓN WAZUH INDEXER: {path.name}")
    print("=" * 80)

    # 1. Metadatos de la consulta
    took = data.get("took", "N/A")
    timed_out = data.get("timed_out", False)
    total_info = data.get("hits", {}).get("total", {})
    total_val = total_info.get("value", "N/A")
    relation = total_info.get("relation", "")

    hits = data.get("hits", {}).get("hits", [])

    print(f"Tiempo de respuesta del Indexer: {took} ms")
    print(f"¿Hubo Timeout?:                  {'Sí' if timed_out else 'No'}")
    print(f"Total de vulns en el clúster:    {total_val} ({'o más' if relation == 'gte' else 'exactas'})")
    print(f"Vulnerabilidades en este JSON:   {len(hits)} (límite default de Elasticsearch si no se usa scroll)")
    print("-" * 80)

    if not hits:
        print("No se encontraron hits en el archivo.")
        return

    # 2. Información del Agente / Host
    first_hit = hits[0].get("_source", {})
    agent = first_hit.get("agent", {})
    host_os = first_hit.get("host", {}).get("os", {})
    cluster = first_hit.get("wazuh", {}).get("cluster", {})

    print(f"Clúster Wazuh:  {cluster.get('name', 'N/A')}")
    print(f"Agente:         ID {agent.get('id', 'N/A')} - {agent.get('name', 'N/A')} (Versión: {agent.get('version', 'N/A')})")
    print(f"Sistema Oper.:  {host_os.get('full', 'N/A')} (Kernel: {host_os.get('kernel', 'N/A')})")
    print("=" * 80)

    # 3. Tabla resumida
    print(f"{'#':<3} | {'CVE ID':<16} | {'SEVERIDAD':<9} | {'SCORE':<5} | {'PAQUETE':<32} | {'DETECTADO'}")
    print("-" * 80)

    for i, hit in enumerate(hits, 1):
        src = hit.get("_source", {})
        vuln = src.get("vulnerability", {})
        pkg = src.get("package", {})

        cve = vuln.get("id", "N/A")
        sev = vuln.get("severity", "N/A")
        score = vuln.get("score", {}).get("base", "N/A")
        pkg_str = f"{pkg.get('name', 'N/A')} ({pkg.get('version', '')})"
        if len(pkg_str) > 32:
            pkg_str = pkg_str[:29] + "..."
        detected = vuln.get("detected_at", "N/A")
        if "T" in detected:
            detected = detected.split("T")[0]

        print(f"{i:<3} | {cve:<16} | {sev:<9} | {str(score):<5} | {pkg_str:<32} | {detected}")

    print("=" * 80)
    print("\n¿Por qué solo hay 10 si el clúster dice 10.000+?")
    print("El comando 'curl' usado consultó '/wazuh-states-vulnerabilities-*/_search' sin especificar 'size'.")
    print("Elasticsearch / OpenSearch limita por defecto a 10 resultados a menos que se use '?size=1000' o la API de scroll.")
    print("Para obtener todas, la API ya implementa 'fetch_all_vulns()' con scroll de 5000 por lote.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "vuln-api/app/datos_wazuh4.json"
    view_raw_wazuh(target)
