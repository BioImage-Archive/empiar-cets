from empiar_cets.yaml_parsing import RegionDefinition
from empiar_cets.empiar_utils import EMPIARFileList

from empiar_cets.cets.movie_stack_collection import create_cets_movie_stack_collection_from_region_definition
from empiar_cets.cets.tilt_series import create_cets_tilt_series_from_region_definition
from empiar_cets.cets.alignment import create_cets_alignment_from_alignment_metadata
from empiar_cets.cets.tomogram import create_cets_tomograms_from_region_definition
from empiar_cets.cets.annotations import create_cets_annotations_from_region_definition
from empiar_cets.metadata_utils import load_mdoc_file, load_xf_file


def create_cets_region_from_region_definition(
        accession_id: str,
        region: RegionDefinition, 
        empiar_files: EMPIARFileList,
) -> dict:
    
    cets_region = {}

    movie_metadata = None
    if region.movie_metadata:
        movie_metadata = load_mdoc_file(
            accession_id, 
            region.movie_metadata.file_pattern, 
            region.movie_metadata.label
        )
    
    if region.movie_stacks:
        cets_movie_stack_collection = create_cets_movie_stack_collection_from_region_definition(
            accession_id, 
            region, 
            empiar_files, 
            movie_metadata
        )
        cets_region["movie_stack_collections"] = cets_movie_stack_collection
    
    if region.tilt_series_metadata:
        tilt_series_metadata = load_mdoc_file(
            accession_id, 
            region.tilt_series_metadata.file_pattern, 
            region.tilt_series_metadata.label
        )

    if region.tilt_series:
        cets_tilt_series = create_cets_tilt_series_from_region_definition(
            accession_id, 
            region, 
            empiar_files, 
            tilt_series_metadata)
        cets_region["tilt_series"] = cets_tilt_series

    if region.alignments:
        alignment_metadata = load_xf_file(
            accession_id, 
            region.alignments.file_pattern, 
            region.alignments.label
        )
        cets_alignments = create_cets_alignment_from_alignment_metadata(alignment_metadata)
        cets_region["alignments"] = cets_alignments
    
    if region.tomograms:
        cets_tomograms = create_cets_tomograms_from_region_definition(
            accession_id, 
            region, 
            empiar_files
        )
        cets_region["tomograms"] = cets_tomograms
    
    if region.annotations:
        cets_annotations = create_cets_annotations_from_region_definition(
            accession_id, 
            region, 
            empiar_files
        )
        cets_region["annotations"] = cets_annotations

    return cets_region


