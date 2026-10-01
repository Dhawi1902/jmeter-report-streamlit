import sys
from pathlib import Path

# Lets the tests import app modules (config, core, ...) by name.
sys.path.insert(0, str(Path(__file__).parent))
