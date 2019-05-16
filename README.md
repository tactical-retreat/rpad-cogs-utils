# PAD Dev Utilities

This repo started out as the location for code used by Miru Bot but not actually
deployed as a Cog. Due to my lazyness and the convenience of having everything in
one place, it expanded into the location for basically everything.

## PAD Asset Stuff

### image_pull

Contains scripts and code for extracting PAD image/video assets. It has its own
detailed readme file which explains how to get access to the files.

### orb_styles_pull

Scripts/code for extracting orb skins. Has its own readme file.

### voice_pull

Scripts/code for extracting voice lines. Has its own readme file.

## PAD Data Processing

### pad_api_data

Contains code related to calling the PAD API, parsing the results into data structures,
converting them into usable forms, updating the local copy of the PadGuide database,
and writing data files out.

If you're using any of the 'raw' files I export, you might want to process them using
a derivative of the code in pad_api_data/pad_etl/data.

### pad_data

Contains the results of the dungeon data processor run against the dungeon/spawn data
for all known spawns. The 'golden' subdirectory contains data that is theoretically
correct. The 'new' subdirectory contains all the other dungeons.

### enemy skill data

Under pad_api_data/pad_etl/processor/enemy_data you can find a serialized set of every
enemy behavior, as computed by the code. This probably deserves to be moved into the
pad_data directory, and both of them probably should move to another repo.

## Other Stuff

### board_data

Contains code/images related to the original implementaion for board detection,
(i.e. ^dawnglare) which compared the histogram of the extracted orb against a
library of labeled orbs.

### azure_scrape / sif_scrape

A couple of folders are dedicated to non-pad stuff, including azure_scrape (broken)
and sif_scrape. They pull images for those games and stick them on the server,
where they can be referenced by Miru Bot.
