import json
import mrcfile
import numpy as np
import os
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO
from typing import Union

from .config import settings


def download_mrc_file_b(
        url, 
        local_filename
):
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(local_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def download_mrc_file(
        url: str, 
        cache_filepath: str, 
):

    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(cache_filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    final_size = os.path.getsize(cache_filepath)
    print(f"Download complete: {final_size:,} bytes")


def load_star_coordinates_from_json(
        json_file_path: str
) -> list[tuple[float, float, float]]:
    
    with open(json_file_path, 'r') as f:
        star_data = json.load(f)
    
    coordinates = []
    for entry in star_data:
        x = entry["rlnCoordinateX"]
        y = entry["rlnCoordinateY"] 
        z = entry["rlnCoordinateZ"]
        coordinates.append((x, y, z))
    
    print(f"Loaded {len(coordinates)} coordinates from JSON")
    return coordinates


def project_and_scale_coordinates(
        coordinates: list[tuple[float, float, float]],
        tomogram_shape: tuple[int, int, int], 
        thumbnail_size: int, 
) -> list[tuple[float, float]]:
    """
    Project 3D coordinates to 2D and scale to thumbnail dimensions.
    
    coordinates: List of (x, y, z) tuples
    tomogram_shape: Original tomogram dimensions (width, height)
        note we use Z to filter out some points
    thumbnail_size: Target thumbnail size (assumed square)
        
    Returns a list of scaled (x, y) coordinates for thumbnail
    """
    
    tomo_depth, tomo_width, tomo_height = tomogram_shape

    z_tol = 0.5
    z_centre = tomo_depth / 2
    coords_2d = [(x, y) for x, y, z in coordinates if (abs(z - z_centre) / tomo_depth) <= z_tol]
    
    scale_x = thumbnail_size / tomo_width 
    scale_y = thumbnail_size / tomo_height 
    
    scaled_coords = [(x * scale_x, y * scale_y) for x, y in coords_2d]
    
    # TODO: some check of validity here, e.g.:
    # valid_coords = [(x, y) for x, y in scaled_coords 
    #                if 0 <= x <= thumb_width and 0 <= y <= thumb_height]
    
    return scaled_coords


def create_tomogram_thumbnail(
        tomogram_data: np.ndarray, 
        thumbnail_size: int, 
        coordinates: Union[list[tuple[float, float]], None],
        method="middle_slice", 
):
    """
    Create thumbnail from 3D tomogram data.
    
    Parameters:
    - tomogram_data: 3D numpy array (depth, height, width)
    - thumbnail_size: tuple of (width, height) for thumbnail
    - method: 'max_projection', 'mean_projection', or 'middle_slice'
    """
    
    if method == "max_projection":
        projection = np.max(tomogram_data, axis=0)
    elif method == "mean_projection":
        projection = np.mean(tomogram_data, axis=0)
    elif method == "middle_slice":
        middle_idx = tomogram_data.shape[0] // 2
        projection = tomogram_data[middle_idx]
    else:
        raise ValueError("Method must be 'max_projection', 'mean_projection', or 'middle_slice'")

    # projection_norm = ((projection - projection.min()) / 
    #                   (projection.max() - projection.min()) * 255).astype(np.uint8)
    
    img = Image.fromarray(projection, mode='L')  # 'L' for grayscale
    img_norm = ImageOps.autocontrast(img, (0, 1))
    img_rgb = img_norm.convert('RGBA')
    thumbnail = img_rgb.resize([thumbnail_size, thumbnail_size], Image.Resampling.LANCZOS)
    
    if coordinates:

        draw = ImageDraw.Draw(thumbnail)
        point_size = 3
        point_color = (0, 255, 255, 64) # cyan, half opacity
        for x, y in coordinates:
            left = x - point_size
            top = y - point_size
            right = x + point_size
            bottom = y + point_size
            
            draw.ellipse([left, top, right, bottom], 
                        fill=None, 
                        outline=point_color)

    return thumbnail


def process_tomogram_thumbnail(
        accession_id: str, 
        tomograms: list, 
        annotations: Union[list, None], 
        thumbnail_size: int = 512
):
    
    output_dir = Path(f"local-data/{accession_id}/thumbnails")
    output_dir.mkdir(exist_ok=True, parents=True)

    methods = ["middle_slice"]

    cache_dirpath = settings.cache_root_dirpath / "files"
    cache_dirpath.mkdir(exist_ok=True, parents=True)

    for tomogram in tomograms:

        tomo_path = tomogram["path"]
        filename = os.path.basename(tomo_path).replace(".mrc", "")
        cache_filename = f"cache_{filename}.mrc"

        cache_filepath = os.path.join(cache_dirpath, cache_filename)
        if os.path.exists(cache_filepath):
            print(f"Using cached file: {cache_filepath}")
        else:
            print(f"Downloading tomogram from: {tomo_path}")
            download_mrc_file(tomo_path, cache_filepath)

        with mrcfile.open(cache_filepath, mode="r") as mrc:

            tomo_data = mrc.data.copy()
            print(f"Tomogram shape: {tomo_data.shape}")
            print(f"Data type: {tomo_data.dtype}")
            print(f"Min value: {tomo_data.min():.2f}, Max value: {tomo_data.max():.2f}")

            # TODO: allow for more than one annotation
            # TODO: allow for other annotations types (assume point curently)
            # TODO: make a field for correspondence of annotation to tomogram
            projected_coords = None
            if annotations is not None:
                if len(annotations) == 1:
                    json_file_path = annotations[0]["path"]
                    print(f"Loading annotations from: {json_file_path}")
                    original_coords = load_star_coordinates_from_json(json_file_path)
                    projected_coords = project_and_scale_coordinates(
                        original_coords, 
                        tomo_data.shape, 
                        thumbnail_size, 
                    )
                else:
                    print("More than one annotation set found; skipping.")

            for method in methods:
                print(f"Creating thumbnail using {method}...")
                thumbnail = create_tomogram_thumbnail(
                    tomo_data, 
                    thumbnail_size, 
                    projected_coords, 
                    method, 
                )
                
                thumbnail_path = os.path.join(output_dir, f"{filename}_{method}_thumbnail.png")
                thumbnail.save(thumbnail_path)
                print(f"Saved thumbnail: {thumbnail_path}")
