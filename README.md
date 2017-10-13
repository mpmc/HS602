# HS602

Information and simple Python scripts/libs to control the HS602 capture device, manufactured by "maxmediatek" and sold under many different names/brands.

* [Maplin Game Capture HD](http://www.maplin.co.uk/p/maplin-game-capture-hd-a84qu)  ("discontinued").
* [Startech USB2HDCAPS](https://www.startech.com/uk/AV/Converters/Video/standalone-video-capture-device~USB2HDCAPS)
* [Diamond GameCaster HD "GC2000"](http://www.diamondmm.com/diamond-gc2000-video-capture-edit-stream.html)


## Serial Connection

On my device (the Maplin variant) the serial/UART pins are populated. You need a TTL UART converter - I used a "USB 2.0 CP2102 To TTL UART Module 6Pin Serial Converter". 

Connect the dupont wires/cables in the following order (facing the back of the SD card slot):

```[ 1 ][ 2 ][ 3 ][ 4 ]```

* 1 = VCC (5V)
* 2 = TX
* 3 = RX
* 4 = GND

If you want to be extra careful **don't** connect the VCC (5V) wire & use the USB connection for power. Also note that powering via serial (without external power) with an Ethernet cable will cause it to crash after a few minutes.

**Tip**: If your device is like mine it'll have a square pin (on the underside) that indicates VCC (5V).

Use your favourite software to connect at 115200 baud/speed with parity set to EVEN (this is listed under serial in PuTTY).


## Features

* Can be used to control a HS602 encoder over the Internet. Although I wouldn't recommend it, it's too insecure! 
* Simple and easy to understand class methods.
* Versions 0.1.1>= are PEP8 compliant.
* Minimal requirements, uses a single import (socket).

## Install

```
pip3 install --user git+git://github.com/mpmc/HS602.git@master
```

* Remove --user to install globally (requires root or sudo).
* Upgrade by running ```pip3 install --user --upgrade hs602```

## Usage

See example.py.

## Features

Almost all the features of the Windows Shareview application.

* Device discovery.
* Streaming toggling (start, stop streaming).
* Set/Get various parameters, rtmp, colour, source, bitrate.
* **Set/Get picture size - which Shareview can't do.**

## Improvements?

* I'm In the process of writing a cross-platform app using the fantastic [appJar](http://github.com/jarvisteach/appjar).

I'm always happy to receive suggestions, fixes or whatever. 

---

## Links
[XDA developers' forum thread](https://forum.xda-developers.com/hardware-hacking/hardware/easily-moddable-hdmi-capture-box-t2988451)
