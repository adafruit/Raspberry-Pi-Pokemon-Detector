# pi_lure
Raspberry Pi Pokemon Finder

Uses https://github.com/keyphact/pgoapi excellent code

encryption file here: http://pastebin.com/raw/fCSw0Fz4

compile encryption file: gcc -std=c99 -shared -o libencrypt.so -fPIC encrypt.c

sudo apt-get install python python-pip python-dev

pip install --upgrade pip

pip install -r requirements.txt

make sure to use full path for encryption file in adapokefinder.py

set config.json file with login credentials