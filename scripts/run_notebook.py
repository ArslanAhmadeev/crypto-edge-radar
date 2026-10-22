"""Execute the pilot notebook reproducibly and remove timing-only metadata."""

from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "01_tge_polymarket_backtest.ipynb"


def main() -> None:
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.execution_count = None
            cell.outputs = []
        cell.metadata.pop("execution", None)

    client = NotebookClient(
        notebook,
        timeout=300,
        kernel_name="python3",
        record_timing=False,
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute()

    for cell in notebook.cells:
        cell.metadata.pop("execution", None)

    nbformat.validate(notebook)
    nbformat.write(notebook, NOTEBOOK_PATH)
    print(f"Executed {NOTEBOOK_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
