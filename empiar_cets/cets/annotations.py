from empiar_cets.annotation_utils import load_annotation_star_file_with_cache
from empiar_cets.empiar_utils import EMPIARFileList, get_files_matching_pattern
from empiar_cets.yaml_parsing import RegionDefinition


def create_cets_annotations_from_region_definition(
        accession_id: str,
        region: RegionDefinition, 
        empiar_files: EMPIARFileList
) -> list[dict]:
    
    cets_annotations = []
    for annotation in region.annotations:
        annotation_paths = get_files_matching_pattern(
            empiar_files, 
            annotation.file_name
        )

        if not annotation_paths:
            raise ValueError(f"No files found matching pattern: {annotation.file_name}")

        if annotation.annotation_type == "point_set_3D":

            if len(annotation_paths) == 1:
                annotation_path = load_annotation_star_file_with_cache(
                    accession_id, 
                    annotation.label, 
                    annotation.file_name,
                    image_name=annotation.image_name,
                    tomogram_column=annotation.tomogram_column
                )

                cets_annotation_dict = {
                    "path": annotation_path,
                }
            
            else:
                raise ValueError(f"Multiple files found for annotation pattern: {annotation.file_name}")
            
        cets_annotations.append(cets_annotation_dict)
    
    return cets_annotations
