import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
REPOSITORY_DIR = PROJECT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(REPOSITORY_DIR / ".env")

from app.seed_data import DEFAULT_DATA_PATH, seed_database


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Wazuh example data")
    parser.add_argument("json_path", nargs="?", default=str(DEFAULT_DATA_PATH))
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace imported connections, vulnerabilities, history and interactions",
    )
    args = parser.parse_args()
    seed_database(args.json_path, replace=args.replace)
    print("Example data loaded successfully.")
