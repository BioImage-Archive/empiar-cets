import typer

import cryoet_metadata._base._models

from .cets_utils import dict_to_cets_model, save_cets_model_to_json
from .empiar_utils import get_files_for_empiar_entry_cached
from .yaml_parsing import load_empiar_yaml, parse_regions
from .cets.region import create_cets_region_from_region_definition

app = typer.Typer()


@app.command()
def convert_empiar_to_cets(
    accession_id: str, 
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
        cets_model_class=cryoet_metadata._base._models.Dataset
    )
    save_cets_model_to_json(accession_id, accession_id, cets_dataset)      


@app.command()
def dummy():
    pass
