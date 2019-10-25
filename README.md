# HS602

Information and Python module (and soon a GUI) to control the HS602 capture device, manufactured by "maxmediatek" and sold under many different names/brands.

* [Maplin Game Capture HD](http://www.maplin.co.uk/p/maplin-game-capture-hd-a84qu)  ("discontinued")
* [Startech USB2HDCAPS](https://www.startech.com/uk/AV/Converters/Video/standalone-video-capture-device~USB2HDCAPS)
* [Diamond GameCaster HD "GC2000"](http://www.diamondmm.com/diamond-gc2000-video-capture-edit-stream.html)
* [RATOC Game Recorder 2 REX-HDGCBOX2](http://www.ratocsystems.com/services/driver/visual/hdgcbox2_rgr.html)
* Skydigital Supercast T3 ([review](https://lpokeh.blogspot.com/2015/07/skydigital-t3-20-hdmi-review.html))

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/b1ee4a339ae24f919f12cee209f3bec0)](https://www.codacy.com/app/hello_58/HS602?utm_source=github.com&utm_medium=referral&utm_content=mpmc/HS602&utm_campaign=badger)

## Features

* **Multi-platform** - works anywhere there's Python3!
* Almost all the features of the Windows Shareview application.
* Device discovery.
* Streaming toggling (start, stop streaming).
* Set/Get various parameters, rtmp, colour, source, bitrate, **and more - that Shareview can't do**.
* Can be used to control a HS602 encoder over the Internet. Although I wouldn't recommend it, it's too insecure!
* Simple and easy to understand/use (hopefully ;) ).
* Versions 0.1.1>= are PEP8 compliant.
* Minimal requirements, uses just socket, concurrent.futures (for callbacks (coming soon)) and gettext (for optional translation).

## Install

**Python 3.2 or later required.**

### Linux

* Make sure you have pip3 installed, then run.. ```pip3 install --user git+git://github.com/mpmc/HS602.git@master```
* Remove --user to install globally (requires root or sudo).
* Upgrade by running ```pip3 install --user --upgrade hs602```

### Windows

* [Install Python](https://www.python.org/downloads/windows/).
* Download (and extract) or clone this repository.


## Example Usage

### Linux

1. Once installed via pip, make a copy of [```example.py```](https://raw.githubusercontent.com/mpmc/HS602/master/hs602/example.py).
2. Modify it to your liking ```nano examply.py```.
3. Run it! In your terminal, navigate to where your file is, e.g. ```cd ~/example.py```, chmod it ```chmod +x example.py``` then run ```./example.py```.

### Windows:

1. Make a copy of [```example.py```](https://raw.githubusercontent.com/mpmc/HS602/master/hs602/example.py) and place it somewhere you can easily find it, then right click and choose *Edit with Python IDLE.*
2. Modify it to your liking.
3. Run it! In Python IDLE, click *Run -> Check Module*  then *Run -> Run Module*.

If you get ```ModuleNotFoundError: No module named 'hs602'``` you need to copy ```example.py``` to the same location as the hs602 (folder).

```
/hs602
/hs602/copy_of_example.py
/hs602/hs602/controller.py
```

## Improvements?

* I'm In the process of writing an app using the fantastic [appJar](http://github.com/jarvisteach/appjar).

I'm always happy to receive suggestions, fixes or whatever.

## Device Debugging/Serial Connection

On my device (the Maplin variant) the serial/UART pins are populated. You need a TTL UART converter - I used a "USB 2.0 CP2102 To TTL UART Module 6Pin Serial Converter".

Connect the dupont wires/cables in the following order (facing the back of the SD card slot):

```[ 1 ][ 2 ][ 3 ][ 4 ]```

* 1 = VCC (5V)
* 2 = TX
* 3 = RX
* 4 = GND

If you want to be extra careful **don't** connect the VCC (5V) wire & use the USB connection for power. Also note that powering via serial (without external power) with an Ethernet cable will cause a crash after a few minutes.

**Tip**: If your device is like mine it'll have a square pin (on the underside) that indicates VCC (5V).

Use your favourite software to connect at 115200 baud/speed with parity set to EVEN (this is listed under serial in PuTTY).

## Links
[XDA developers' forum thread](https://forum.xda-developers.com/hardware-hacking/hardware/easily-moddable-hdmi-capture-box-t2988451)
