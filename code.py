import os
import time
import gc
import board
import busio
from digitalio import DigitalInOut
import neopixel
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
import storage
import displayio
import math
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.circle import Circle

red_circle = None
#I googled "iss location api" and this is one of the first sites to come up
WHERETHEISS="https://api.wheretheiss.at/v1/satellites/25544"

def set_background(file_or_color, position=None):
    image_file = open(file_or_color, "rb")
    bitmap_contents = displayio.OnDiskBitmap(image_file)

    tile_grid = displayio.TileGrid(
        bitmap_contents,
        pixel_shader=displayio.ColorConverter(),
        default_tile=0,
        x=0,  # Position relative to its parent group
        y=0,
        width=1,  # Number of tiles in the grid
        height=1,
        # tile_width=None,  # Number of tiles * tile size must match BMP size
        # tile_height=None,  # None means auto size the tiles
        )

    group.append(tile_grid)
    board.DISPLAY.show(group)

def set_backlight(val):
    """Adjust the TFT backlight.
    :param val: The backlight brightness. Use a value between ``0`` and ``1``, where ``0`` is
                off, and ``1`` is 100% brightness.
    """
    board.DISPLAY.brightness = val

def neo_status(value):
    """The status NeoPixel.
    :param value: The color to change the NeoPixel.
    """
    if neopix:
        neopix.fill(value)

def _connect_esp():
    neo_status((0, 0, 100))
    while not _esp.is_connected:
        # secrets dictionary must contain 'ssid' and 'password' at a minimum
        print("Connecting to AP", secrets['ssid'])
        if secrets['ssid'] == 'CHANGE ME' or secrets['ssid'] == 'CHANGE ME':
            change_me = "\n"+"*"*45
            change_me += "\nPlease update the 'secrets.py' file on your\n"
            change_me += "CIRCUITPY drive to include your local WiFi\n"
            change_me += "access point SSID name in 'ssid' and SSID\n"
            change_me += "password in 'password'. Then save to reload!\n"
            change_me += "*"*45
            raise OSError(change_me)
        neo_status((100, 0, 0)) # red = not connected
        try:
            _esp.connect(secrets)
        except RuntimeError as error:
            print("Could not connect to internet", error)
            print("Retrying in 3 seconds...")
            time.sleep(3)

def convert_lat_long( latitude, longitude, width, height):
    #cribbed from https://github.com/mfeldheim/hermap/blob/master/src/Geo/Projection.php#L56-L57
    x = math.floor((longitude+180)*(width/360)+.5)
    y = math.floor((height/2)-(width*math.log(math.tan((math.pi/4)+((latitude*math.pi/180)/2)))/(2*math.pi))+.5)
    #print("X coordiate: %d" % int(x))
    #print("Y coordiate: %d" % int(y))
    return (int(x), int(y))

print("Lets go from dim to bright")
i = 0
while i <= 1:
    set_backlight(i)
    time.sleep(.5)
    i += 0.1

# load font
print("Loading fonts")
cwd = ("/"+__file__).rsplit('/', 1)[0]
font = bitmap_font.load_font(cwd+"/fonts/Arial-ItalicMT-17.bdf")
text = None
print("Loaded fonts")

#load settings
try:
    from secrets import secrets
except ImportError:
    print("""WiFi settings are kept in secrets.py, please add them there!
the secrets dictionary must contain 'ssid' and 'password' at a minimum""")

print( "Loaded settings" )
print( "Wireless ssid: " + secrets['ssid'] )

neopix = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)

print( "Init ESP32")
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_gpio0 = DigitalInOut(board.ESP_GPIO0)
esp32_reset = DigitalInOut(board.ESP_RESET)
esp32_cs = DigitalInOut(board.ESP_CS)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

_esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready,
                                            esp32_reset, esp32_gpio0)

for _ in range(3): # retries
    try:
        print("ESP firmware:", str(_esp.firmware_version,'utf-8'))
        break
    except RuntimeError:
        print("Retrying ESP32 connection")
        time.sleep(1)
        _esp.reset()
else:
    raise RuntimeError("Was not able to find ESP32")

try:
    requests.set_socket(socket, _esp)
except Exception as excp:
    print("set_socket exception: ", excp)

_connect_esp()

print("My IP address is", _esp.pretty_ip(_esp.ip_address))

group = displayio.Group(max_size=10)

print('Resolution: %sx%s' %
      (board.DISPLAY.width, board.DISPLAY.height))

print("Showing startup screens")
# show thank you and bootup file if available
for bootscreen in ("/pyportal_startup.bmp", "/earth-nasa.bmp"):
    print("Trying to load: " + bootscreen )
    try:
        os.stat(bootscreen)
        for i in range(100, -1, -1):  # dim down
            set_backlight(i/100)
            time.sleep(0.005)
        set_background(bootscreen)
        board.DISPLAY.wait_for_frame()
        for i in range(100):  # dim up
            set_backlight(i/100)
            time.sleep(0.005)
        time.sleep(2)
    except OSError:
        pass # they removed it, skip!

while True:
    try:
        neo_status((0,0,100))
        while not _esp.is_connected:
            # settings dictionary must contain 'ssid' and 'password' at a minimum
            print("ESP32 CONNECTING...")
            neo_status((100, 0, 0)) # WARNING # red = not connected
            _connect_esp()
            print("ESP32 CONNECTED!")
        else:
            print("ESP32 Connected")

        print("Data source: " + WHERETHEISS)
        print("Retrieving data source...", end='')
        neo_status((100, 100, 0))   # yellow = fetching data
        resp = requests.get(WHERETHEISS)
        neo_status((0, 0, 100))   # green = got data
        print("Reply is OK!")
    except Exception as excp:
        print("Failed to get data, retrying\n")
        print("Error message is: ", excp)
        continue
    print(resp.text)
    json_out = resp.json()
    latitude = json_out["latitude"]
    longitude = json_out["longitude"]
    print("Lat: %f\tLong: %f" % (latitude,longitude))
    coordinates = convert_lat_long( latitude, longitude,board.DISPLAY.width,board.DISPLAY.height)
    print("X: %d\tY: %d" % coordinates)

    x = coordinates[0]
    y = coordinates[1]

#    #math seems off. Let me fudge it
#    #could the the quality of the image from wekimedia
#    if x - 5 < 0 :
#        x = 320 - 5 + x
#    else:
#        x -= 5
#
#    if y - 5 < 0 :
#        y = 240 - 5 + y
#    else:
#        y -= 5

    if red_circle is None:
        print("Need to make the first dot")
        red_circle = Circle(
            x0=x,
            y0=y,
            r=5,
            fill=0xFF0000,
            outline=0xFFFFFF,
            )
        group.append(red_circle)
    else:
        red_circle.x = x
        red_circle.y = y

    print("Sleeping for 60 seconds")
    time.sleep(60)
