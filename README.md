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

## Bedienung

- Button 1: Geschwindigkeit hoeher
- Button 2: Geschwindigkeit niedriger
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

Wenn das Display nur blau leuchtet, aber keine Schrift zeigt:

- Am kleinen blauen Poti auf dem I2C-Adapter langsam drehen. Das ist der Kontrast.
- `python3 test_display.py` starten. Der Test probiert die typischen PCF8574-Adressen.
- Wenn der Test nichts findet: `i2cdetect -y 1` ausfuehren und die angezeigte Adresse in `.env` eintragen.
- Wenn gar keine Adresse angezeigt wird: SDA/SCL, VCC/GND und aktiviertes I2C in `raspi-config` pruefen.
- GPIO2/SDA ist Pin 3 am Raspberry-Pi-Header, GPIO3/SCL ist Pin 5.
- Wenn schwarze Kaestchen, aber keine Schrift erscheinen: Adresse oder Initialisierung stimmt noch nicht.

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

Die Beispielbelegung ist fuer einfache RGB-Scheinwerfer:

- Kanal 1: Master-Dimmer
- Kanal 2: Rot
- Kanal 3: Gruen
- Kanal 4: Blau
- Kanal 5: Strobe/Flash

Du kannst die Kanaele in `.env` aendern.

## Programmstruktur

- `main.py`: startet alles und verbindet Buttons, Display und DMX-Ausgabe
- `config.py`: GPIO-Pins und Einstellungen aus `.env`
- `buttons.py`: Button-Anbindung ueber `gpiozero`
- `display.py`: Ausgabe auf dem 20x4-I2C-LCD
- `state.py`: aktueller Zustand wie Modus, Speed, Flash und An/Aus
- `lighting.py`: erzeugt aus dem Zustand die 512 DMX-Kanalwerte
- `dmx_output.py`: USB-DMX-Ausgabe, aktuell `enttec_pro`, `open_dmx` oder `log`

Wenn spaeter mehrere Scheinwerfer oder feste Szenen dazukommen, ist `lighting.py`
der richtige Ort fuer die Logik. Wenn der konkrete USB-DMX-Wandler ein anderes
serielles Protokoll braucht, kommt diese Anpassung in `dmx_output.py`.
