import rich
import json
from pathlib import Path
from typing import Any, Optional, Type
from pydantic import BaseModel, ValidationError
from pydantic.alias_generators import to_snake


def dict_to_cets_model(
    dict: dict[str, Any],
    cets_model_class: Type[BaseModel],
) -> Optional[BaseModel]:
    
    cets_model = None
    try:
        cets_model = cets_model_class.model_validate(dict)
    except ValidationError as e:
        rich.print(
            f"[red]Validation error for {cets_model_class.__name__} with data: {dict}. Error: {e}[/red]"
        )
    
    return cets_model


def get_model_type_dir(cache_dirpath, model: Type[BaseModel]) -> Path:
    """Get the directory path for a specific model type within this accession"""
    model_type = to_snake(model.__name__)
    return cache_dirpath / model_type


def save_cets_model_to_json(
        accession_id: str,
        region_title: str, 
        cets_model: BaseModel,
) -> None:
    
    if not isinstance(cets_model, BaseModel):
        raise TypeError("Object must be a Pydantic model")
    
    cache_dirpath = Path(f"local-data/{accession_id}")
    cache_dirpath.mkdir(exist_ok=True, parents=True)

    model_dir = get_model_type_dir(cache_dirpath, cets_model.__class__)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = model_dir / f"{region_title}.json"

    with open(model_path, 'w') as f:
        json.dump(cets_model.model_dump(), f, indent=2)
    rich.print(f"[green]Saved CETS model to {model_path}[/green]")

