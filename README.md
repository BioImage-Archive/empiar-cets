# EMPIAR – CETS
For conversion of EMPIAR data to the cryoET standards (CETS) model specification.

## Installation + configuration
With poetry, as usual.

There are currently no further configuration steps, since there is no API for depositing objects — all is saved locally within the repository directory.

## Use
There is only one command:

    poetry run empiar-cets convert-empiar-to-cets <EMPIAR_accession_id>

and so far, there is only one EMPIAR entry, EMPIAR-12104, with the requisite yaml definition file, thus:

    poetry run empiar-cets convert-empiar-to-cets EMPIAR-12104

is the only option. 

## Input
The yaml definition files are similar to those used in the EMPIAR ingest, but naturally, have a slightly different (and still developing) format, to assist in parsing EMPIAR data to the CETS specification. 

## Output
Output files are stored locally, in the folder "local-data", subfolders of which are named according to EMPIAR accession ID. Of principal interest is the json file that contains the data according to the CETS specification. The models are defined [here](https://github.com/cryo-et-standards/cryoet-geometry), but actually, the fork, [here](https://github.com/Chr1st0p43rR/cryoet-geometry-fork/tree/empiar-cets-start) (and note the branch), is what's used in this project, for it has a small change which is necessary for proper recording of transformation matrices. The classes according to which the output is built are found in this [file](https://github.com/Chr1st0p43rR/cryoet-geometry-fork/blob/empiar-cets-start/src/cryoet_metadata/_base/_models.py), specifically. 

The other output that is saved comprises json files representing the list of all EMPIAR files for the particular entry, and various metadata formats. 