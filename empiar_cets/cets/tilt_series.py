from empiar_cets.yaml_parsing import RegionDefinition
from empiar_cets.empiar_utils import EMPIARFileList, get_files_matching_pattern
from empiar_cets.metadata_models import MdocFile


def create_cets_tilt_series_from_region_definition(
        accession_id: str,
        region: RegionDefinition, 
        empiar_files: EMPIARFileList, 
        tilt_series_metadata: MdocFile = None,
) -> list[dict]:
    
    cets_tilt_series = []
    for tilt_series in region.tilt_series:
        
        tilt_series_paths = get_files_matching_pattern(
            empiar_files, 
            tilt_series.file_pattern
        )

        if not tilt_series_paths:
            raise ValueError(f"No files found matching pattern: {tilt_series.file_pattern}")
        
        cets_tilt_series_dict = {}
        accession_no = accession_id.split("-")[1]
        if len(tilt_series_paths) == 1:
            cets_tilt_series_dict["path"] = f"https://ftp.ebi.ac.uk/empiar/world_availability/{accession_no}/data/{tilt_series_paths[0]}"
        # TODO: else if frame-by-frame to add path to each movie frame in a list. 

        if tilt_series_metadata:
            cets_projection_images = create_cets_projection_images_for_tilt_series(tilt_series_metadata)
            cets_tilt_series_dict["images"] = cets_projection_images
        
        cets_tilt_series.append(cets_tilt_series_dict)

    return cets_tilt_series


def create_cets_projection_images_for_tilt_series( 
        tilt_series_metadata: MdocFile, 
) -> list[dict]:
    
    cets_projection_images = []
    image_width, image_height = map(int, tilt_series_metadata.global_headers["ImageSize"].split())
    for z in tilt_series_metadata.z_sections:
        cets_projection_image_dict ={
            "section": str(z.z_value), 
            "nominal_tilt_angle": z.metadata["TiltAngle"], 
            "width": image_width,
            "height": image_height,
        }
        cets_projection_images.append(cets_projection_image_dict)
    
    return cets_projection_images
