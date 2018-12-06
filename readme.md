# taw_scaper

Simple tawdis.net scraper

## installation

Create a new python3.6 env and install the requirements:

    pip install -r requirements.py

Firefox is needed to work. Make sure you have it installed.
You also need the last [geckodriver](https://github.com/mozilla/geckodriver/releases). Leave it in the same dir as the script.

## usage

See `python taw_scraper.py -h`

## todo

[ ] skip invalid pages
[ ] skip page in timeout errors
[X] resume scraper
[X] wait 20 seconds in consecutive requests
[ ] skip the limitation of 10 request in a hour
[ ] make more verbose
[ ] option to change taw options (Level and Technologies)
