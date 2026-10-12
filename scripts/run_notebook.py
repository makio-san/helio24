"""Execute the notebook locally without committing data-bearing outputs."""
import os
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
for variable, folder in [('MPLCONFIGDIR', 'matplotlib'), ('JUPYTER_RUNTIME_DIR', 'jupyter')]:
    path = ROOT / 'data/cache' / folder
    path.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(variable, str(path))

if __name__ == '__main__':
    source = ROOT / 'notebooks/01_helio24_baseline.ipynb'
    notebook = nbformat.read(source, as_version=4)
    client = NotebookClient(notebook, timeout=900, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}})
    client.execute()
    destination = ROOT / 'artifacts/01_helio24_baseline.executed.ipynb'
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, destination)
    print(f'Executed notebook: {destination}')
