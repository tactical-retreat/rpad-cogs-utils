# Dev Utilities

This repo started out as the location for code used by Miru Bot but not actually
deployed as a Cog. Due to my lazyness and the convenience of having everything in
one place, it expanded into the location for basically everything.

It has mostly shrunk back down to just ancillary Miru stuff. All the PAD/DadGuide
stuff is now contained in a separate repo:

https://github.com/nachoapps/dadguide-data

## Other Stuff

### board_data

Contains code/images related to the original implementaion for board detection,
(i.e. ^dawnglare) which compared the histogram of the extracted orb against a
library of labeled orbs.

### azure_scrape / sif_scrape

A couple of folders are dedicated to non-pad stuff, including azure_scrape (broken)
and sif_scrape. They pull images for those games and stick them on the server,
where they can be referenced by Miru Bot.
