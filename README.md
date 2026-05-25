# mobileLichtsteuerung

Kleine Raspberry-Pi-Steuerung fuer Buttons, 20x4-I2C-LCD und USB-DMX.

## Verkabelung

### Display 2004A mit I2C-Adapter

- Blau: SCL an GPIO3
- Gruen: SDA an GPIO2
- zusaetzlich VCC und GND am Raspberry Pi anschliessen

### Buttons

Die Buttons werden gegen 3,3 V geschaltet. Im Programm sind interne Pull-Downs aktiv.

- Braun: 3,3 V fuer die Button-Seite
- Schwarz: Button 5 an GPIO17
- Weiss: Button 6 an GPIO27
- Grau: Button 4 an GPIO22
- Blau: Button 3 an GPIO23
- Lila: Button 2 an GPIO24
- Rot: Button 1 an GPIO25

### Drehgeber

Der Drehgeber wird gegen GND geschaltet. Im Programm sind interne Pull-Ups aktiv.

- Blau: GND fuer Pull-Up
- Weiss: GND
- Lila: Druckknopf an GPIO4
- Grau: Drehgeber A an GPIO5
- Schwarz: Drehgeber B an GPIO6

## Bedienung

- Drehgeber drehen: Geschwindigkeit hoeher/niedriger
- Drehgeber druecken: Umschalten zwischen Buehne aussen und Buehne innen
- Button 1: Geschwindigkeit hoeher als Backup
- Button 2: Geschwindigkeit niedriger als Backup
- Button 3: Farbwechselmodus
- Button 4: Automatikmodus
- Button 5: Licht an/aus
- Button 6: Flash an/aus

## Installation auf dem Raspberry Pi

```bash
sudo raspi-config
```

Dort `Interface Options` -> `I2C` aktivieren.

```bash
sudo apt update
sudo apt install -y python3-full python3-venv python3-dev build-essential swig liblgpio-dev
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

`python-dotenv` liest beim Start die Datei `.env`. Dadurch stehen Einstellungen wie
DMX-Port, Adaptertyp, LCD-Adresse und DMX-Kanaele nicht fest im Python-Code, sondern
koennen direkt in `.env` geaendert werden.

Wenn dein LCD nicht auf Adresse `0x27` liegt, findest du die Adresse so:

```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```

Dann `LCD_I2C_ADDRESS` in `.env` anpassen, oft ist es `0x27` oder `0x3f`.
Der normale Raspberry-Pi-I2C-Port fuer GPIO2/GPIO3 ist:

```env
LCD_I2C_PORT=1
```

Wenn das Display nur blau leuchtet, aber keine Schrift zeigt:

- Am kleinen blauen Poti auf dem I2C-Adapter langsam drehen. Das ist der Kontrast.
- `python3 test_display.py` starten. Der Test probiert die typischen PCF8574-Adressen.
- Wenn der Test nichts findet: `i2cdetect -y 1` ausfuehren und die angezeigte Adresse in `.env` eintragen.
- Wenn gar keine Adresse angezeigt wird: SDA/SCL, VCC/GND und aktiviertes I2C in `raspi-config` pruefen.
- GPIO2/SDA ist Pin 3 am Raspberry-Pi-Header, GPIO3/SCL ist Pin 5.
- GPIO0/GPIO1 waeren Bus 0, also `/dev/i2c-0`. Den nur testen, wenn das Display wirklich dort angeschlossen ist.
- Wenn schwarze Kaestchen, aber keine Schrift erscheinen: Adresse oder Initialisierung stimmt noch nicht.

Eine komplett leere `i2cdetect -y 1`-Tabelle bedeutet: Der Raspberry Pi sieht
elektrisch kein I2C-Geraet. Dann liegt es nicht am Python-Code. Pruefe in dieser
Reihenfolge:

- SDA wirklich an GPIO2 / physischer Pin 3
- SCL wirklich an GPIO3 / physischer Pin 5
- GND vom Display mit GND vom Raspberry Pi verbunden
- VCC passend angeschlossen
- I2C in `raspi-config` aktiviert und Pi danach neu gestartet
- I2C-Adapter hinten am Display fest verloetet oder sauber gesteckt

Viele LCD-I2C-Backpacks haben Pullups an VCC. Wenn das Modul mit 5 V versorgt
wird, koennen SDA/SCL ebenfalls auf 5 V gezogen werden. Fuer den Raspberry Pi ist
das unschoen; sauber ist 3,3 V-Versorgung, wenn das Display damit funktioniert,
oder ein I2C-Level-Shifter bei 5 V-Versorgung.

## DMX-Adapter

Standard ist:

```env
DMX_PORT=/dev/ttyUSB0
DMX_BACKEND=enttec_pro
```

Wenn beim Start `could not open port /dev/ttyUSB0` kommt, ist der Adapter nicht
eingesteckt, wurde nicht erkannt oder heisst anders. Pruefe ihn auf dem Pi mit:

```bash
ls /dev/ttyUSB*
ls /dev/serial/by-id/
```

Wenn z.B. `/dev/ttyUSB1` angezeigt wird, trage in `.env` ein:

```env
DMX_PORT=/dev/ttyUSB1
```

Falls du einen einfachen Open-DMX/FTDI-Adapter hast:

```env
DMX_BACKEND=open_dmx
```

Zum Testen ohne echten DMX-Adapter:

```env
DMX_BACKEND=log
```

Wenn `No module named 'RPLCD'` kommt, wurden die Python-Pakete noch nicht fuer
genau diesen Python installiert. Im Projektordner:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Wenn `lgpio` beim Installieren mit `error: command 'swig' failed` oder
`cannot find -llgpio` abbricht:

```bash
sudo apt install -y python3-dev build-essential swig liblgpio-dev
source .venv/bin/activate
pip install -r requirements.txt
```

## DMX-Kanaele

Die Aussenlampen sind als 7-Kanal-Scheinwerfer angelegt. Startadressen:

- Lampe 1: DMX 1
- Lampe 2: DMX 9
- Lampe 3: DMX 17
- Lampe 4: DMX 25

In `.env` steht dafuer:

```env
DMX_OUTSIDE_FIXTURES=1,9,17,25
DMX_INSIDE_FIXTURES=
```

Die Kanalbelegung pro Lampe:

- CH1: Master-Helligkeit
- CH2: Rot
- CH3: Gruen
- CH4: Blau
- CH5: Strobe/Flash, 0-7 aus, 8-255 schnell
- CH6: Effektmodus, im Programm auf manuell
- CH7: Effektgeschwindigkeit/Farbauswahl, im Programm aktuell aus

Der Automatikmodus laesst die vier Aussenlampen von links nach rechts, von rechts
nach links, die linken zwei, die rechten zwei und alle zusammen blinken. Der
Farbwechselmodus faehrt die RGB-Werte langsam und smooth durch. Die Geschwindigkeit
wird in beiden Modi ueber den Drehgeber gesteuert.

## Programmstruktur

- `main.py`: startet alles und verbindet Buttons, Display und DMX-Ausgabe
- `config.py`: GPIO-Pins und Einstellungen aus `.env`
- `buttons.py`: Button-Anbindung ueber `gpiozero`
- `rotary_encoder.py`: Drehgeber und Drehgeber-Druckknopf
- `display.py`: Ausgabe auf dem 20x4-I2C-LCD
- `state.py`: aktueller Zustand wie Modus, Speed, Flash und An/Aus
- `lighting.py`: erzeugt aus dem Zustand die 512 DMX-Kanalwerte
- `dmx_output.py`: USB-DMX-Ausgabe, aktuell `enttec_pro`, `open_dmx` oder `log`

Wenn spaeter mehrere Scheinwerfer oder feste Szenen dazukommen, ist `lighting.py`
der richtige Ort fuer die Logik. Wenn der konkrete USB-DMX-Wandler ein anderes
serielles Protokoll braucht, kommt diese Anpassung in `dmx_output.py`.
