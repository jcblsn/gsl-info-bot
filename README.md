# Great Salt Lake Water Level Bot


The Great Salt Lake is [disappearing](https://www.reuters.com/business/environment/utahs-great-salt-lake-is-drying-out-threatening-ecological-economic-disaster-2022-07-14/). This repo serves as a simple reminder and as proof of concept for a Bluesky bot.

![](bot-screenshot.png)

## Functionality

I scrape the current water level data from the [Great Salt Lake Water Level](http://greatsalt.uslakes.info/Level.asp) website, log it to `levels.csv`, and post it to Bluesky using the [atprototools](https://github.com/iandklatzco/atprototools) package. I include comparisons to the average water level 1, 2, and 10 years ago calculated using [USGS historical data](https://nwis.waterdata.usgs.gov/usa/nwis/uv/).

## Requirements

Required Python packages are listed in `requirements.txt`.

## Attribution

- Water level data is retrieved from the [Great Salt Lake Water Level](http://greatsalt.uslakes.info/Level.asp) website.
- Thanks to the authors of [atprototools](https://github.com/ianklatzco/atprototools) for the Python tools for Bluesky.


## License

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
