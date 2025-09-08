import re
from pathlib import Path
from ruamel.yaml import YAML
from typing import Optional, List
from pydantic import BaseModel


class MovieMetadata(BaseModel):
    label: str
    file_pattern: str


class MovieStack(BaseModel):
    label: str
    file_pattern: str


class TiltSeriesMetadata(BaseModel):
    label: str
    file_pattern: str


class TiltSeries(BaseModel):
    label: str
    file_pattern: str


class Alignment(BaseModel):
    label: str
    file_pattern: str


class Tomogram(BaseModel):
    label: str
    file_pattern: str


class Annotation(BaseModel):
    label: str
    annotation_type: str
    file_name: str
    block_name: Optional[str] = None 
    image_name: Optional[str] = None
    tomogram_column: Optional[str] = None


# TODO: should metadata be a list? In what circumstances will there be multiple files, and what formats?
class RegionDefinition(BaseModel):
    title: str
    movie_metadata: Optional[MovieMetadata] = None
    movie_stacks: Optional[List[MovieStack]] = None
    tilt_series_metadata: Optional[TiltSeriesMetadata] = None
    tilt_series: Optional[List[TiltSeries]] = None
    alignments: Optional[Alignment] = None
    tomograms: Optional[List[Tomogram]] = None 
    annotations: Optional[List[Annotation]] = None


def load_empiar_yaml(accession_id: str) -> dict:

    if not re.match(r'^EMPIAR-\d+$', accession_id):
        raise ValueError(f"Invalid EMPIAR accession ID format: {accession_id}")
    
    numeric_id = accession_id.split('-')[1]
    yaml_filename = f"empiar_{numeric_id}.yaml"
    yaml_fpath = Path("definition_files/")/yaml_filename
    
    yaml = YAML()
    try:
        with open(yaml_fpath) as fh:
            yaml_dict = yaml.load(fh)
            return yaml_dict
    except FileNotFoundError:
        raise FileNotFoundError(f"YAML file not found: {yaml_fpath}")
    except Exception as e:
        raise type(e)(f"Error parsing YAML file {yaml_fpath}: {str(e)}")
    

def parse_regions(
        definition_dict: dict,
) -> list[RegionDefinition]:
    
    regions = []
    for region in definition_dict["regions"]:
        region_definition = RegionDefinition.model_validate(region)
        regions.append(region_definition)
    
    return regions
