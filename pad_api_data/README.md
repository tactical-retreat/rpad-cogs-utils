# PAD Data Processing

This folder contains the ETL pipeline that downloads raw PAD data (and saves it),
converts it to a more useful format (and saves it), and then applies updates to
the DadGuide (PadGuide) database.

If you're looking to do your own processing, start with `pad_etl/data`.

If you're interested in duplicating this whole process, you should probably
contact tactical_retreat, it's somewhat involved.

A lot of the shell scripts in this directory have paths on the server I use
hardcoded because I'm lazy and its easier. Most of them are run periodically
via cron jobs.

## Scripts in this directory

The scripts here do all the data updating, and also some misc utility stuff.

### Primary data pull

| Script                      | Purpose                                               |
| ---                         | ---                                                   |
| pull_data.sh                | Coordinates the PAD ETL process, sycs data to cloud   |
| pad_data_pull.py            | Downloads PAD data from server via API                |
| padguide_processor.py       | Updates PadGuide database, writes processed files     |
| default_db_config.json      | Dummy file for PG database connection                 |

### Secondary data pull stuff

| Script                      | Purpose                                               |
| ---                         | ---                                                   |
| auto_dungeon_scrape.py      | Identifies dungeons with no data and starts loader    |
| pad_dungeon_pull.py         | Actually pulls the dungen spawns and saves them       |
| load_dungeon.py             | Loads dungeon info on demand                          |
| copy_image_data.py          | Moves image files into place for DadGuide             |
| dungeon_wave_exporter.py    | Extracts wave spawn data to disk for publishing       |
| extract_padguide_db.py      | Dumps PadGuide database (for Miru's use)              |

### Enemy skills

| Script                      | Purpose                                               |
| ---                         | ---                                                   |
| rebuild_enemy_skills.py     | Rebuilds the enemy skill flat file database           |
| dungeon_integration_test.py | Uses the ES database to create dungeon data output    |


# Testing/Utility

| Script                      | Purpose                                               |
| ---                         | ---                                                   |
| integration_test.py         | Creates/compares processed golden files to find diffs |
| print_dungeon.py            | Helper that prints dungeon info, used from web        |

## pad_etl

Contains all the library code that the scripts in this directory rely on. It
does the data pulling, processing, formatting, and database updating. There's
a lot of stuff in here.

## Less important subdirectories

### utils

Random scripts and code. 

Most importantly, `refresh_data.[sh|bat]` will simplify pulling the latest
published data files for development purposes, such as running the integration
tests or generating enemy skill/dungeon data.

### padguide

Utility scripts for serving padguide data and doing some administrative stuff.
Contains all the PHP endpoints (masquerading as JSP) that serve the actual
data to DadGuide clients.

### crud

Contains some UI stuff that is used for administrative purposes. You're probably
not interested in it.

### deprecated

Contains some stuff that is supposed to be deprecated but I'm still running it
for Reni's blog =)
