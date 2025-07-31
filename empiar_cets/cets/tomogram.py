from empiar_cets.yaml_parsing import RegionDirective
from empiar_cets.empiar_utils import EMPIARFileList, get_files_matching_pattern, read_mrc_header_pyfs


def create_cets_tomograms_from_region_directive(
        accession_id: str,
        region: RegionDirective, 
        empiar_files: EMPIARFileList
) -> list[dict]:
    
    cets_tomograms = []
    accession_no = accession_id.split("-")[1]
    for tomogram in region.tomograms:
        tomogram_paths = get_files_matching_pattern(
            empiar_files, 
            tomogram.file_pattern
        )

        if not tomogram_paths:
            raise ValueError(f"No files found matching pattern: {tomogram.file_pattern}")

        cets_tomogram_dict = {}
        if len(tomogram_paths) == 1:
            cets_tomogram_dict["path"] = f"https://ftp.ebi.ac.uk/empiar/world_availability/{accession_no}/data/{tomogram_paths[0]}"
        
        # Read MRC header information
        file_path = f"/empiar/world_availability/{accession_no}/data/{tomogram_paths[0]}"
        mrc_header_info = read_mrc_header_pyfs(file_path)

        cets_tomogram_dict["width"] = mrc_header_info["dimensions"][0]
        cets_tomogram_dict["height"] = mrc_header_info["dimensions"][1]
        cets_tomogram_dict["depth"] = mrc_header_info["dimensions"][2]

        cets_tomograms.append(cets_tomogram_dict)

    return cets_tomograms
