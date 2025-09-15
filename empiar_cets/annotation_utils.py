import starfile
from typing import Optional
from pandas import DataFrame
from pathlib import Path

from .empiar_utils import download_file_from_empiar
from .utils import make_local_data_path


def filter_starfile_df(
        star_df: DataFrame, 
        tomogram_column: str,
        image_name: Optional[str] = None,
) -> DataFrame:
    
    if image_name is None:
        filtered_df = star_df
    else:
        filtered_df = star_df[star_df[f"{tomogram_column}"] == image_name]

    return filtered_df


def load_annotation_star_file(
        accession_id: str, 
        star_label: str, 
        file_name: str, 
        image_name: Optional[str] = None, 
        tomogram_column: Optional[str] = "rlnMicrographName", 
) -> str:
    
    local_data_path = make_local_data_path(
        accession_id, 
        file_type="star", 
        file_label=star_label
    )

    if Path(local_data_path).exists():
        return str(local_data_path)
    
    temp_star_path = download_file_from_empiar(accession_id, file_name)

    try: 
        star_df = starfile.read(temp_star_path)
        filtered_df = filter_starfile_df(
            star_df, 
            image_name, 
            tomogram_column
        )
        filtered_df.to_json(local_data_path, orient='records', indent=2)

        return str(local_data_path)
        
    finally:
        Path(temp_star_path).unlink()

