import gemmi
import json
import starfile
from typing import List, Optional, Tuple
from pandas import DataFrame
from pathlib import Path

from .empiar_utils import download_file_from_empiar
from .utils import make_local_file_cache


def get_coordinates_from_gemmi_doc(star_file, block_name=None):
    # TODO: make input param a path — to use for plotting thumbnails
    """
    Extract x, y, z coordinates from a gemmi star file object as tuples.
    
    Args:
        star_file: gemmi.cif.Document object from gemmi.cif.read_file()
        block_name: optional name of specific block to read from
    
    Returns:
        list of tuples: [(x1, y1, z1), (x2, y2, z2), ...]
    """
    if block_name is None:
        block = star_file[0]
    else:
        block = star_file[block_name]
    
    coord_columns = ['_rlnCoordinateX', '_rlnCoordinateY', '_rlnCoordinateZ']
    coordinates = []
    
    for loop in block:
        if all(col in loop.tags for col in coord_columns):
            x_col = loop.find_tag('_rlnCoordinateX')
            y_col = loop.find_tag('_rlnCoordinateY') 
            z_col = loop.find_tag('_rlnCoordinateZ')
            
            for row in loop:
                x = float(row[x_col])
                y = float(row[y_col])
                z = float(row[z_col])
                coordinates.append((x, y, z))
            break
    
    return coordinates


def filter_star_by_image_name(
        filepath: str, 
        block_name: Optional[str] = None,
        image_name: Optional[str] = None, 
        tomogram_column: Optional[str] = "_rlnMicrographName", 
) -> str:
    
    star_file = gemmi.cif.read_file(filepath)
    filtered_doc = gemmi.cif.Document()
    
    if block_name is None:
        source_block = star_file[0]
    else:
        source_block = star_file[block_name]
    
    new_block = filtered_doc.add_new_block(source_block.name)
    
    # copy all non-loop items (comments, single values, etc.)
    for item in source_block:
        if not isinstance(item, gemmi.cif.Loop):
            if item.pair is not None:
                print('pair', item.pair)
            elif item.loop is not None:
                print('loop', item.loop)
            elif item.frame is not None:
                print('frame', item.frame)
            #new_block.set_pair(item.pair[0], item.pair[1])
    
    for loop in source_block:
        if isinstance(loop, gemmi.cif.Loop) and tomogram_column in loop.tags:
            
            new_loop = new_block.init_loop("", loop.tags)
            tomo_col = loop.find_tag(tomogram_column)
            
            # copy matching rows
            for row in loop:
                if str(row[tomo_col]) == str(image_name):
                    new_loop.add_row([row[i] for i in range(len(loop.tags))])
        
        elif isinstance(loop, gemmi.cif.Loop):
            # copy other loops unchanged
            new_loop = new_block.init_loop("", loop.tags)
            for row in loop:
                new_loop.add_row([row[i] for i in range(len(loop.tags))])
        
        print("here")
    
    return filtered_doc


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


def load_annotation_star_file_with_cache(
        accession_id: str, 
        star_label: str, 
        file_name: str, 
        image_name: Optional[str] = None, 
        tomogram_column: Optional[str] = "rlnMicrographName", 
) -> str:
    
    cache_path = make_local_file_cache(
        accession_id, 
        file_type="star", 
        file_label=star_label
    )

    if Path(cache_path).exists():
        return str(cache_path)
    
    accession_no = accession_id.split("-")[1]
    url_base = "https://ftp.ebi.ac.uk/empiar/world_availability/" 
    url = f"{url_base}{accession_no}/data/{file_name}"
    temp_star_path = download_file_from_empiar(url, file_type="star")

    # try:
    #     star_file = filter_star_by_image_name(
    #         temp_star_path, 
    #         block_name, 
    #         image_name, 
    #         tomogram_column, 
    #     )
    #     star_file.write_file(str(cache_path))

    #     return str(cache_path)

    try: 
        star_df = starfile.read(temp_star_path)
        filtered_df = filter_starfile_df(
            star_df, 
            image_name, 
            tomogram_column
        )
        filtered_df.to_json(cache_path, orient='records', indent=2)

        return str(cache_path)
        
    finally:
        Path(temp_star_path).unlink()

