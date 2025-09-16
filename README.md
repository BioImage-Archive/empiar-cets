# EMPIAR – CETS
For conversion of EMPIAR data to the cryoET standards (CETS) model specification.

## Installation + configuration
With poetry — from the top level of the cloned repository:

    poetry install

There are currently no further configuration steps besides optionally specifying a location for the file cache — this is used only for image data when generating thumbnails (see *Thumbnails*, below), and its default location is specified in `config.py`. It can be changed by entering an alternative location for `cache_root_dirpath` in a .env file, following the example set in the .env_template file here. All other CETS data and associated metadata are saved locally within the repository directory, under "local-data" (see *Output*, below).

## Use
### EMPIAR — CETS
To make CETS objects for an EMPIAR entry:

    poetry run empiar-cets empiar-to-cets <EMPIAR_accession_id>

where there must be a yaml definition file for the given accession ID. The definition file for EMPIAR-12104 is currently the most/best populated, and most convenient to test. Thus:

    poetry run empiar-cets empiar-to-cets EMPIAR-12104

will create CETS data for that entry, which you'll find under "local-data", created if it didn't exist already, in the repository's directory. The CETS data is saved as a json file under "dataset", and associated metadata (list of EMPIAR files, mdoc, star, and xf files) is also cached there, for speedier use if the same command is called again.

### Thumbnails
To generate thumbnails from CETS data:

    poetry run empiar-cets create-thumbnails <EMPIAR_accession_id>

where there must be a CETS dataset json file (i.e., the output of the above command), with at least one tomogram, for the given accession ID. If there are point annotations present in the CETS dataset, then they are superimposed on the thumbnail image. 

There are options here, with long and abbreviated forms:

    --thumbnail-size
    -t

can be used to specify the output thumbnail size, in pixels. Input must be two values for [x, y] e.g., for a 512-by-512 output thumbnail, you'd have `512 512`. The default is [256, 256]. The size of the output thumbnail is actually as close as is possible to the input values, using them as an upper limit for the largest dimension, whilst maintaining the aspect ratio of the original image. 

    --projection-method
    -p

is for choosing the method of projection on the z axis of the image. It must be one of `max`, `mean`, or `middle`, to specify a maximum projection, mean projection, or the central slice only, respectively. Note that if `middle` is chosen, then the `limit-projection` option, below, is somewhat functionless.

    --limit-projection
    -lp

can be used to limit the number of slices to project over, according to the above method (with the aforementioned caveat that `middle` means this option becomes irrelevant). It should be expressed as a proportion of the total number of slices, so that the total number of slcies need not be known in advance. The default is 0.5, and minimum and maximum are 0.0 and 1.0.

    --limit-annotation
    -la

is similar to `--limit-projection`, in that you can choose to limit the number of annotation points, based on a proportion of their z coordinate values. And as above, the default is 0.5, and minimum and maximum are 0.0 and 1.0. This option is useful when there are a lot of annotation points, and they swamp the thumbnail image; by limiting their number, you get to see some of the image, too.

## Input
The yaml definition files are similar to those used in the EMPIAR ingest, but naturally, have a slightly different (and still developing) format, to assist in parsing EMPIAR data to the CETS specification. 

## Output
Output files are stored locally, in the folder "local-data", subfolders of which are named according to EMPIAR accession ID. Of principal interest is the json file that contains the data according to the CETS specification. The models are defined [here](https://github.com/TomoBabel/cets-data-models), but actually, the fork, [here](https://github.com/Chr1st0p43rR/cryoet-geometry-fork/tree/empiar-cets-start) (and note the branch), is currently what's used in this project, for it has a small change which is necessary for proper recording of transformation matrices. The classes according to which the output is built are found in this [file](https://github.com/Chr1st0p43rR/cryoet-geometry-fork/blob/empiar-cets-start/src/cryoet_metadata/_base/_models.py), specifically. 

The other output that is saved comprises json files representing the list of all EMPIAR files for the particular entry, and various metadata formats. 