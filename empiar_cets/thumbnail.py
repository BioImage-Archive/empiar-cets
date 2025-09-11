import json
import logging
import mrcfile
import numpy as np
import os
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from typing import Union

from .config import settings

logger = logging.getLogger(__name__)

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
    logger.info(f"Download complete: {final_size:,} bytes")


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
    
    return coordinates


def project_and_scale_coordinates(
        coordinates: list[tuple[float, float, float]],
        tomogram_shape: tuple[int, int, int], 
        thumbnail_size: tuple[int, int], 
        limit_annotation: float, 
) -> list[tuple[float, float]]:
    
    tomo_depth, tomo_width, tomo_height = tomogram_shape

    z_centre = tomo_depth / 2
    coords_2d = [(x, y) for x, y, z in coordinates if (abs(z - z_centre) / tomo_depth) <= limit_annotation]
    
    scale_x = thumbnail_size[0] / tomo_width 
    scale_y = thumbnail_size[1] / tomo_height 
    
    scaled_coords = [(x * scale_x, y * scale_y) for x, y in coords_2d]
    
    # TODO: some check of validity here, e.g.:
    # valid_coords = [(x, y) for x, y in scaled_coords 
    #                if 0 <= x <= thumb_width and 0 <= y <= thumb_height]
    
    return scaled_coords


def create_tomogram_thumbnail(
        tomogram_data: np.ndarray, 
        thumbnail_size: tuple[int, int],
        coordinates: Union[list[tuple[float, float]], None],
        method: str, 
        limit_projection: float, 
):
    
    depth = tomogram_data.shape[0]
    if limit_projection < 1.0:
        central_slice = depth // 2
        half_window = int((depth * limit_projection) // 2)
        start_slice = max(0, central_slice - half_window)
        end_slice = min(depth, central_slice + half_window)
        tomogram_data = tomogram_data[start_slice:end_slice, :, :]
        logger.info(f"Projecting over slices {start_slice} to {end_slice} (total {end_slice - start_slice})")

    if method == "max":
        projection = np.max(tomogram_data, axis=0)
    elif method == "mean":
        projection = np.mean(tomogram_data, axis=0)
    elif method == "middle":
        middle_idx = tomogram_data.shape[0] // 2
        projection = tomogram_data[middle_idx]
    else:
        raise ValueError("Method must be 'max', 'mean', or 'middle'")
    
    # TODO: some check of orientation?
    # TODO: and dimensions?
    projection = np.flipud(projection) 
    projection = projection.astype(np.float64)
    projection = (projection - projection.min()) / (projection.max() - projection.min())
    projection = (projection * 255).astype(np.uint8)

    img = Image.fromarray(projection, mode='L')
    img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
    img = img.convert('RGB')
    
    if coordinates:

        draw = ImageDraw.Draw(img)
        point_size = 3
        point_color = (0, 255, 255, 64) 
        for x, y in coordinates:
            left = x - point_size
            top = y - point_size
            right = x + point_size
            bottom = y + point_size
            
            draw.ellipse([left, top, right, bottom], 
                        fill=None, 
                        outline=point_color)

    return img


def process_tomogram_thumbnail(
        accession_id: str, 
        tomograms: list, 
        annotations: Union[list, None], 
        thumbnail_size: tuple[int, int], 
        projection_method: str, 
        limit_projection: float, 
        limit_annotation: float, 
):
    
    output_dir = Path(f"local-data/{accession_id}/thumbnails")
    output_dir.mkdir(exist_ok=True, parents=True)

    cache_dirpath = settings.cache_root_dirpath / f"{accession_id}" / "files"
    cache_dirpath.mkdir(exist_ok=True, parents=True)

    for tomogram in tomograms:

        tomo_path = tomogram["path"]
        filename = os.path.basename(tomo_path).replace(".mrc", "")
        cache_filename = f"cache_{filename}.mrc"

        cache_filepath = os.path.join(cache_dirpath, cache_filename)
        if os.path.exists(cache_filepath):
            logger.info(f"Using cached file: {cache_filepath}")
        else:
            logger.info(f"Downloading tomogram from: {tomo_path}")
            download_mrc_file(tomo_path, cache_filepath)

        with mrcfile.open(cache_filepath, mode="r") as mrc:

            # TODO: allow for more than one annotation
            # TODO: allow for other annotations types (assume point curently)
            # TODO: make a field for correspondence of annotation to tomogram

            tomo_data = mrc.data.copy()

            projected_coords = None
            if annotations is not None:
                if len(annotations) == 1:
                    json_file_path = annotations[0]["path"]
                    original_coords = load_star_coordinates_from_json(json_file_path)
                    projected_coords = project_and_scale_coordinates(
                        original_coords, 
                        tomo_data.shape, 
                        thumbnail_size, 
                        limit_annotation, 
                    )
                else:
                    logger.info("More than one annotation set found; skipping.")

            thumbnail = create_tomogram_thumbnail(
                tomo_data, 
                thumbnail_size, 
                projected_coords, 
                projection_method, 
                limit_projection, 
            )
            
            thumbnail_path = os.path.join(output_dir, f"{filename}_{projection_method}_thumbnail.png")
            thumbnail.save(thumbnail_path)
