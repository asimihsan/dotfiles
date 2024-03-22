from pathlib import Path
import sys

VENDOR_DIR = str(Path(__file__).parent)

print(sys.path)

if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))
