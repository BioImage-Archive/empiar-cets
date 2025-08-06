from pathlib import Path

from empiar_cets.yaml_parsing import RegionDefinition, MovieStack
from empiar_cets.empiar_utils import EMPIARFileList, get_files_matching_pattern
from empiar_cets.metadata_models import MdocFile


def create_cets_movie_stack_collection_from_region_definition(
        accession_id: str,
        region: RegionDefinition,
        empiar_files: EMPIARFileList, 
        movie_metadata: MdocFile = None, 
) -> list[dict]:
    
    cets_movie_stacks = create_cets_movie_stacks_from_region_definition(accession_id, region, empiar_files, movie_metadata)
    cets_movie_stack_series = [{"stacks": cets_movie_stacks}]

    cets_movie_stack_collection = {"movie_stacks": cets_movie_stack_series}
    
    # TODO: add gain and defect file to movie stack collection

    return [cets_movie_stack_collection]


def create_cets_movie_stacks_from_region_definition(
        accession_id: str,
        region: RegionDefinition, 
        empiar_files: EMPIARFileList, 
        movie_metadata: MdocFile = None,
) -> list[dict]:
    
    cets_movie_stacks = []
    for movie_stack in region.movie_stacks:
        
        movie_stack_paths = get_files_matching_pattern(
            empiar_files, 
            movie_stack.file_pattern
        )

        if not movie_stack_paths:
            raise ValueError(f"No files found matching pattern: {movie_stack.file_pattern}")
        
        accession_no = accession_id.split("-")[1]
        if len(movie_stack_paths) == 1:
            cets_movie_stack_dict = {"path": f"https://ftp.ebi.ac.uk/empiar/world_availability/{accession_no}/data/{movie_stack_paths[0]}"}
        # TODO: else if frame-by-frame to add path to each movie frame in a list. 

        if movie_metadata:
            cets_movie_frames = create_cets_movie_frames_for_volume_movie(
                movie_stack, 
                movie_metadata
            )
            cets_movie_stack_dict["images"] = cets_movie_frames

        cets_movie_stacks.append(cets_movie_stack_dict)
    
    return cets_movie_stacks


def create_cets_movie_frames_for_volume_movie(
        movie_stack: MovieStack,
        movie_metadata: MdocFile,
) -> list[dict]:
    
    file_name_pattern = Path(movie_stack.file_pattern).name
    metadata_section = movie_metadata.search_by_subframe_path(file_name_pattern)[0] 
    if not metadata_section:
        raise ValueError(f"No metadata section found for file pattern: {file_name_pattern}")

    # TODO: accumlated dose?
    # TODO: proper file paths for each frame
    cets_movie_frames = []
    image_width, image_height = map(int, movie_metadata.global_headers["ImageSize"].split())
    for f in range(int(metadata_section.metadata["NumSubFrames"])):
        cets_movie_frame_dict = {
            "section": str(f), 
            "nominal_tilt_angle": metadata_section.metadata["TiltAngle"],
            "width": image_width,
            "height": image_height,
        }
        cets_movie_frames.append(cets_movie_frame_dict)
    
    return cets_movie_frames