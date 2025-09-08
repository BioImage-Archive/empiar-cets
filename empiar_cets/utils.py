from pathlib import Path


def make_local_file_cache(
        accession_id: str,
        file_type: str,
        file_label: str,
) -> Path:

    cache_dirpath = Path(f"local-data/{accession_id}/{file_type}")
    cache_dirpath.mkdir(exist_ok=True, parents=True)
    cache_path = cache_dirpath / f"{file_label}.json"

    return cache_path
