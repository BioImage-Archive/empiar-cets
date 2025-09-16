from typing import List, Any
from pydantic import BaseModel, Field


class ZValueSection(BaseModel):
    """
    Represents a single [ZValue = n] section from an .mdoc file.
    """

    z_value: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class MdocFile(BaseModel):
    """
    Represents a parsed .mdoc file with global headers and ZValue sections.
    """

    filename: str
    global_headers: dict[str, Any] = Field(default_factory=dict)
    z_sections: list[ZValueSection] = Field(default_factory=list)

    def search_by_subframe_path(
            self, 
            search_string: str, 
            case_sensitive: bool = False
        ) -> List[ZValueSection]:
        """
        Search for sections where the SubFramePath ends with the given search string.
        To be used to find the Z-section for a specific cryoET movie.
        
        Args:
            search_string: String to match against the end of SubFramePath
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List (but should be one?) of ZValueSection objects that match the criteria
        """

        matches = []
        if self.z_sections:
            for section in self.z_sections:
                subframe_path = section.metadata.get("SubFramePath", None)
                if not subframe_path:
                    continue
                    
                subframe_path = str(subframe_path)
                
                if not case_sensitive:
                    subframe_path = subframe_path.lower()
                    search_string = search_string.lower()
                
                if subframe_path.endswith(search_string):
                    matches.append(section)
        
        return matches
