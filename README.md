### Function

- this app will connect to your wifi (add your SSID and password)
- query the current location of the ISS
- convert lat-long to x-y
- display an earth map
- display a dot where the ISS is overhead-ish

# References

The code pulls the current location from [here](https://api.wheretheiss.at/v1/satellites/25544)

Took code from the [Adafruit pyportal](https://raw.githubusercontent.com/colonwq/Adafruit_CircuitPython_PyPortal/master/adafruit_pyportal.py)

Took code from [Dev Dungeon](https://www.devdungeon.com/content/pyportal-circuitpy-tutorial-adabox-011)

Took math from [hermap](https://github.com/mfeldheim/hermap/blob/master/src/Geo/Projection.php#L56-L57)

Took the Earth map from [Code Club Projects](https://codeclubprojects.org/en-GB/python/iss/materials.html)

# Issues

- Map registration is a bit off. May need to add a fudge factor to slide the iss around. 


