
def create_cets_alignment_from_region_directive(
        alignment_metadata: dict,
) -> list[dict]:
    
    # TODO: should Alignment class have a path field?

    alignments = []
    for i, alignment in enumerate(alignment_metadata["projection_alignments"]):
        cets_projection_alignment_sequence = []
        for transform in alignment["sequence"]:
            if transform["type"] == "translation":
                cets_projection_alignment_sequence.append({
                    "translation": transform["translation"],
                    "name": transform["name"],
                })
            elif transform["type"] == "affine":
                cets_projection_alignment_sequence.append({
                    "affine": transform["affine"],
                    "name": transform["name"],
                })
        cets_projection_alignment_dict = {
            "sequence": cets_projection_alignment_sequence,
        }
        alignments.append(cets_projection_alignment_dict)
    
    cets_alignments = {"projection_alignments": alignments}
    
    return [cets_alignments]
    