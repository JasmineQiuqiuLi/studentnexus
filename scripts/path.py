from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

def find_root():
    # get the current file's directory
    current_dir=Path(__file__).resolve().parent
    
    # check the root directory by looking for a specific file or folder that indicates the root
    while True:
        if (current_dir / ".git").exists():  # pathlib uses / to join paths:
            return current_dir
        if current_dir.parent == current_dir:  # reached the root of the filesystem
            raise FileNotFoundError("Root directory not found.")
        current_dir = current_dir.parent
# print(os.getenv("PROJECT_ROOT"))
ROOT_DIR = Path(os.getenv("PROJECT_ROOT")) if os.getenv("PROJECT_ROOT") else find_root()
print(f"Project root directory: {ROOT_DIR}")

DATA_DIR = ROOT_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
RAW_DIR = DATA_DIR / "raw"
LOG_DIR = ROOT_DIR / "logs"
CLEANED_DIR = DATA_DIR / "cleaned"

for p in [DATA_DIR, REGISTRY_DIR, RAW_DIR, LOG_DIR, CLEANED_DIR]:
    p.mkdir(parents=True, exist_ok=True)
