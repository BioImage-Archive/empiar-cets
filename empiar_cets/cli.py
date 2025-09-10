import json
import logging
import os
import typer
from pathlib import Path
from rich.logging import RichHandler
from typing import Annotated, Optional

from cryoet_metadata._base._models import Dataset

from .cets_utils import dict_to_cets_model, save_cets_model_to_json
from .empiar_utils import get_files_for_empiar_entry_cached
from .thumbnail import process_tomogram_thumbnail
from .yaml_parsing import load_empiar_yaml, parse_regions
from .cets.region import create_cets_region_from_region_definition

app = typer.Typer()

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(asctime)s - %(levelname)s - %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger()

@app.command("empiar-to-cets")
def convert_empiar_to_cets(
        accession_id: Annotated[
            str, 
            typer.Argument(
                help="The EMPIAR accession ID for the entry to be converted."
            )
        ],
):

    yaml_definition_dict = load_empiar_yaml(accession_id)
    regions = parse_regions(yaml_definition_dict)

    empiar_files = get_files_for_empiar_entry_cached(accession_id)

    cets_dataset_dict = {}
    dataset_regions = []
    for region in regions:
        cets_region_dict = create_cets_region_from_region_definition(
            accession_id,
            region, 
            empiar_files
        )
        dataset_regions.append(cets_region_dict)

    cets_dataset_dict["name"] = accession_id
    cets_dataset_dict["regions"] = dataset_regions
    cets_dataset = dict_to_cets_model(
        cets_dataset_dict, 
        cets_model_class=Dataset
    )
    save_cets_model_to_json(accession_id, accession_id, cets_dataset)      


@app.command("create-thumbnails")
def create_thumbnail_images(
        accession_id: Annotated[
            str, 
            typer.Argument(
                help="The EMPIAR accession ID for the CETS object to create thumbnails for."
            )
        ],
        thumbnail_size: Annotated[
            Optional[tuple[int, int]], 
            typer.Option(
                "--thumbnail-size", 
                "-t", 
                help="Size of the output thumbnails in pixels, as [x, y]. Deafult is [256, 256].",
            )
        ] = [256, 256],
        projection_method: Annotated[
            Optional[str], 
            typer.Option(
                "--projection_method", 
                "-p",
                help="Method for projection on z-axis, must be one of 'max', 'mean', or 'middle'. Default is max.",
            )
        ] = "max",
        limit_projection: Annotated[
            Optional[float], 
            typer.Option(
                "--limit-projection", 
                "-lp", 
                min=0.0, 
                max=1.0, 
                help="Proportion of slices to project over, about the central slice of the tomogram. Defailt is 0.5 (half slices).",
            )
        ] = 0.5,
        limit_annotation: Annotated[
            Optional[float], 
            typer.Option(
                "--limit-annotation", 
                "-la", 
                min=0.0, 
                max=1.0, 
                help="Proportion of annotation points to accept, about the central slice of the tomogram. Default is 0.5 (half depth).",
            )
        ] = 0.5,
):
    
    valid_projection_choices = ["mean", "max", "middle"]
    if projection_method not in valid_projection_choices:
        raise typer.BadParameter(f"projection_method must be one of: {', '.join(valid_projection_choices)}")

    dataset_file_path = Path(f"local-data/{accession_id}/dataset/{accession_id}.json")
    if not os.path.exists(dataset_file_path):
        raise FileNotFoundError(f"File {dataset_file_path} not found.")
    try:
        with open(dataset_file_path, 'r') as f:
            dataset_dict = json.load(f)
    except json.JSONDecodeError as e:
        raise
    
    dict_to_cets_model(dataset_dict, Dataset)

    for region in dataset_dict["regions"]:
        if region["tomograms"] is not None:
            process_tomogram_thumbnail(
                accession_id, 
                region["tomograms"], 
                region["annotations"], 
                thumbnail_size, 
                projection_method, 
                limit_projection, 
                limit_annotation, 
            )


if __name__ == "__main__":
    app()
