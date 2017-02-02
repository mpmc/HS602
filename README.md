##HS602

Information and simple scripts to control the HS602 capture device, manufactured by "maxmediatek" and sold under many different names/brands.

* [Maplin Game Capture HD](http://www.maplin.co.uk/p/maplin-game-capture-hd-a84qu)  ("discontinued").
* [Startech USB2HDCAPS](https://www.startech.com/uk/AV/Converters/Video/standalone-video-capture-device~USB2HDCAPS)
* [Diamond GameCaster HD "GC2000"](http://www.diamondmm.com/diamond-gc2000-video-capture-edit-stream.html)

---
###Connecting to the Device via Serial
On my device (the Maplin variant) the serial/UART pins are populated. You need a TTL UART converter - I used a "USB 2.0 CP2102 To TTL UART Module 6Pin Serial Converter". 

Connect the dupont wires/cables in the following order (facing the back of the SD card slot):

```[ 1 ][ 2 ][ 3 ][ 4 ]```

* 1 = VCC (5V)
* 2 = TX
* 3 = RX
* 4 = GND

If you want to be extra careful **don't** connect the VCC (5V) wire & use the USB connection for power. Also be aware that powering via serial (without external power) & an Ethernet cable connected will cause it to crash after a few minutes.

**Tip**: If your device is like mine it'll have a square pin (on the underside) that indicates VCC (5V).

Use your favourite software to connect at 115200 baud/speed with parity set to EVEN (this is listed under serial in PUTTY).

---

###The Script(s)

I plan on writing a PHP version sometime in the future.

**Use of these scripts is at your own risk.**

####Python

This is a very limited script at the moment, it's only possible to set the streamurl, key and toggle broadcasting. There is no interface (yet). See example.py for usage.

**Python3.x is required.**

---
###Improvements

I'm always happy to receive suggestions, fixes or whatever. 

---
####Links
[XDA developers' forum thread](https://forum.xda-developers.com/hardware-hacking/hardware/easily-moddable-hdmi-capture-box-t2988451)