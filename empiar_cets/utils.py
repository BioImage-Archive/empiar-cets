from pathlib import Path


def make_local_data_path(
        accession_id: str,
        file_type: str,
        file_label: str,
) -> Path:

    dirpath = Path(f"local-data/{accession_id}/{file_type}")
    dirpath.mkdir(exist_ok=True, parents=True)
    path = dirpath / f"{file_label}.json"

    return path
