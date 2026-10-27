"""
Script CLI para cargar datos de prueba Wazuh en la base de datos PostgreSQL.
Uso:
    python vuln-api/app/load-data.py [--replace] [ruta_al_json]
"""
import sys
import argparse
from pathlib import Path

# Agregar directorio superior al sys.path para importaciones de módulo
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
sys.path.insert(0, str(CURRENT_DIR.parent))

from app.seed_data import seed_database, DEFAULT_DATA_PATH

def main():
    parser = argparse.ArgumentParser(description="Cargador de datos Wazuh para vuln-api")
    parser.add_argument("file_path", nargs="?", default=str(DEFAULT_DATA_PATH), help="Ruta al archivo JSON a cargar")
    parser.add_argument("--replace", action="store_true", help="Reemplazar datos existentes (vulnerabilidades, historial, conexiones)")
    args = parser.parse_args()

    json_path = Path(args.file_path)
    if not json_path.exists():
        print(f"Error: El archivo no existe: {json_path}")
        sys.exit(1)

    print(f"[*] Cargando datos desde {json_path} (replace={args.replace})...")
    try:
        seed_database(json_path=json_path, replace=args.replace)
        print("[OK] Datos cargados exitosamente en la base de datos.")
    except Exception as e:
        print(f"Error al cargar datos en la base de datos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
