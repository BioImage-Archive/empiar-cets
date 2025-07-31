import json
import struct
import re
from pathlib import Path
from fs.ftpfs import FTPFS
from typing import Any, Union, List

from .metadata_models import MdocFile, ZValueSection
from .empiar_utils import download_metadata_file_from_empiar


def save_mdoc_to_json(mdoc: MdocFile, filepath: str) -> None:
    
    with open(filepath, 'w') as f:
        json.dump(mdoc.to_dict(), f, indent=2)


def save_alignment_to_json(alignment: dict[str, Any], filepath: str) -> None:
    
    with open(filepath, 'w') as f:
        json.dump(alignment, f, indent=2)


def load_mdoc_from_json(filepath: str) -> MdocFile:
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return MdocFile.from_dict(data)


def load_alignment_from_json(filepath: str) -> dict[str, Any]:
    """Load Alignment object from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return data


def load_metdata_file_with_cache(
        accession_id: str,
        file_type: str,
        file_label: str,
) -> Path:

    cache_dirpath = Path(f"local-data/{accession_id}/{file_type}")
    cache_dirpath.mkdir(exist_ok=True, parents=True)
    cache_path = cache_dirpath / f"{file_label}.json"

    return cache_path


def load_mdoc_with_cache(
        accession_id: str, 
        file_pattern: str,
        mdoc_label: str,
) -> MdocFile:
    
    cache_path = load_metdata_file_with_cache(
        accession_id, 
        file_type='mdoc', 
        file_label=mdoc_label
    )
    
    if Path(cache_path).exists():
        return load_mdoc_from_json(cache_path)

    accession_no = accession_id.split("-")[1]
    url_base = "https://ftp.ebi.ac.uk/empiar/world_availability/" 
    url = f"{url_base}{accession_no}/data/{file_pattern}"
    temp_mdoc_path = download_metadata_file_from_empiar(url, file_type='mdoc')
    
    try:
        mdoc = parse_mdoc_file(temp_mdoc_path)
        save_mdoc_to_json(mdoc, cache_path)
        
        return mdoc
        
    finally:
        Path(temp_mdoc_path).unlink()


def load_xf_with_cache(
        accession_id: str, 
        file_pattern: str,
        xf_label: str,
) -> dict[str, Any]:
    
    cache_path = load_metdata_file_with_cache(
        accession_id, 
        file_type='xf', 
        file_label=xf_label
    )
    
    if Path(cache_path).exists():
        return load_alignment_from_json(cache_path)
    
    accession_no = accession_id.split("-")[1]
    url_base = "https://ftp.ebi.ac.uk/empiar/world_availability/" 
    url = f"{url_base}{accession_no}/data/{file_pattern}"
    temp_xf_path = download_metadata_file_from_empiar(url, file_type='xf')
    
    try:
        alignment = parse_xf_file(temp_xf_path)
        save_alignment_to_json(alignment, cache_path)
        
        return alignment
        
    finally:
        Path(temp_xf_path).unlink()


def parse_value(value_str: str) -> Union[str, int, float]:
    """
    Parse a string value to appropriate type (int, float, or str)
    """
    value_str = value_str.strip()
    
    # Try integer first
    try:
        return int(value_str)
    except ValueError:
        pass
    
    # Try float
    try:
        return float(value_str)
    except ValueError:
        pass
    
    # Return as string
    return value_str


def parse_xf_file(
    filepath: str, 
) -> dict[str, Any]:
    """
    Parse an .xf file and return a dictionary with projection alignments 
    as sequences of affine and translation transformations.

    Each line in the file should contain six values: a11, a12, a21, a22, dx, dy.

    Returns a dictionary with a list of projection alignments.
    """
    
    projection_alignments = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            continue
        
        # Parse the six values: a11 a12 a21 a22 dx dy
        values = line.split()
        if len(values) != 6:
            print(f"Warning: Line {i+1} has {len(values)} values instead of 6, skipping")
            continue
        
        try:
            a11, a12, a21, a22, dx, dy = [float(v) for v in values]
        except ValueError as e:
            print(f"Warning: Could not parse line {i+1}: {line}, error: {e}")
            continue
        
        affine_transform = {
            "type": "affine",
            "name": f"rotation_projection_{i}",
            "output": f"rotated_projection_{i}",
            "affine": [
                [a11, a12, 0.0],
                [a21, a22, 0.0],
                [0.0, 0.0, 1.0]
            ]
        }
        
        translation_transform = {
            "type": "translation",
            "name": f"translation_projection_{i}",
            "input": f"rotated_projection_{i}",
            "translation": [dx, dy]
        }
        
        projection_alignment = {
            "type": "sequence",
            "name": f"alignment_projection_{i}",
            "sequence": [affine_transform, translation_transform]
        }
        
        projection_alignments.append(projection_alignment)
    
    alignment = {
        "projection_alignments": projection_alignments
    }
    
    return alignment


def parse_mdoc_file(filepath: str) -> MdocFile:
    """
    Parse an .mdoc file containing metadata about tilt series and movie frames .
    Return a MdocFile object.
    """
    mdoc = MdocFile(filename=str(filepath))
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    current_section = None
    in_global_headers = True
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Handle comments (lines starting with [T = )
        if line.startswith('[T =') and line.endswith(']'):
            comment = line[4:-1].strip()  # Remove [T = and ]
            mdoc.comments.append(comment)
            continue
        
        # Handle ZValue sections
        z_value_match = re.match(r'\[ZValue\s*=\s*(\d+)\]', line)
        if z_value_match:
            z_value = int(z_value_match.group(1))
            current_section = ZValueSection(z_value=z_value)
            mdoc.z_sections.append(current_section)
            in_global_headers = False
            continue
        
        # Handle key-value pairs
        if '=' in line and not line.startswith('['):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Parse value to appropriate type
            parsed_value = parse_value(value)
            
            # Add to appropriate section
            if in_global_headers:
                mdoc.global_headers[key] = parsed_value
            elif current_section is not None:
                current_section[key] = parsed_value
    
    return mdoc


def read_mrc_header(filepath):
    """    
    Read metadata from MRC file header from a file located at given filepath.
    Returns a dictionary with header information.
    """
    # TODO: local file version

    ftp_url = 'ftp.ebi.ac.uk'

    with FTPFS(ftp_url) as ftp_fs:
        with ftp_fs.open(filepath, 'rb') as f:
            header_data = f.read(1024)
    
    # Parse MRC header - 
    # Format: nx, ny, nz, mode, nxstart, nystart, nzstart, mx, my, mz
    header_ints = struct.unpack('<10i', header_data[:40])
    
    # Bytes 40-52: cell dimensions (3 floats)
    cell_dims = struct.unpack('<3f', header_data[40:52])
    
    # Bytes 52-64: cell angles (3 floats) 
    cell_angles = struct.unpack('<3f', header_data[52:64])
    
    # TODO: currently don't use all of these, find a CETS home for them?
    return {
        'dimensions': header_ints[:3],  # nx, ny, nz
        'mode': header_ints[3],         # data type
        'cell_dimensions': cell_dims,
        'cell_angles': cell_angles
    }

