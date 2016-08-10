#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""
import os
import sys
import json
import time
import pprint
import logging
import getpass
import argparse
import random
from subprocess import call

import RPi.GPIO as GPIO
from time import sleep
 
LED_PIN1 = 17
LED_PIN2 = 27
LED_PIN3 = 22
 
print "Setting up GPIO"
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN1, GPIO.OUT)
GPIO.setup(LED_PIN2, GPIO.OUT)
GPIO.setup(LED_PIN3, GPIO.OUT)
 
def enable_led(pinNum, should_enable):
    if should_enable:
        GPIO.output(pinNum, True)
    else:
        GPIO.output(pinNum, False)


# add directory of this file to PATH, so that the package will be found
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# import Pokemon Go API lib
from pgoapi import pgoapi
from pgoapi import utilities as util

#Pokemon organized by rarity, taken from http://www.gamerevolution.com/faq/pokemon-go/pokmon-rarity---from-common-to-legendary-with-pictures-125819

COMMON_POKE = [69,10,50,84,96,23,133,92,74,118,98,66,129,81,56,52,32,29,43,46,16,60,19,27,79,48,100,13,41]
UNCOMMON_POKE = [63,24,1,4,35,104,101,102,42,75,88,58,93,106,116,39,124,14,140,64,109,82,11,53,17,25,77,54,20,111,28,86,90,21,7,120,72,37]
RARE_POKE = [142,59,12,113,91,85,147,51,125,83,22,136,55,44,107,97,135,99,108,68,67,126,122,30,33,38,138,95,47,61,137,57,78,112,117,119,123,143,121,114,73,110,40]
VERY_RARE_POKE = [65,15,5,87,148,103,94,76,130,2,141,115,131,105,89,34,31,139,18,127,62,26,80,134,49,71,45,8,70]
EPIC_POKE = [9,6,36,149,128,3]
LEGENDARY_POKE = [144,132,151,150,146,145]

POKE_NAMES = ["Bulbasaur","Ivysaur","Venusaur","Charmander","Charmeleon","Charizard","Squirtle","Wartortle","Blastoise","Caterpie","Metapod","Butterfree","Weedle","Kakuna","Beedrill","Pidgey","Pidgeotto","Pidgeot","Rattata","Raticate","Spearow","Fearow","Ekans","Arbok","Pikachu","Raichu","Sandshrew","Sandslash","Nidoran♀","Nidorina","Nidoqueen","Nidoran♂","Nidorino","Nidoking","Clefairy","Clefable","Vulpix","Ninetales","Jigglypuff","Wigglytuff","Zubat","Golbat","Oddish","Gloom","Vileplume","Paras","Parasect","Venonat","Venomoth","Diglett","Dugtrio","Meowth","Persian","Psyduck","Golduck","Mankey","Primeape","Growlithe","Arcanine","Poliwag","Poliwhirl","Poliwrath","Abra","Kadabra","Alakazam","Machop","Machoke","Machamp","Bellsprout","Weepinbell","Victreebel","Tentacool","Tentacruel","Geodude","Graveler","Golem","Ponyta","Rapidash","Slowpoke","Slowbro","Magnemite","Magneton","Farfetch","Doduo","Dodrio","Seel","Dewgong","Grimer","Muk","Shellder","Cloyster","Gastly","Haunter","Gengar","Onix","Drowzee","Hypno","Krabby","Kingler","Voltorb","Electrode","Exeggcute","Exeggutor","Cubone","Marowak","Hitmonlee","Hitmonchan","Lickitung","Koffing","Weezing","Rhyhorn","Rhydon","Chansey","Tangela","Kangaskhan","Horsea","Seadra","Goldeen","Seaking","Staryu","Starmie","Mr","Scyther","Jynx","Electabuzz","Magmar","Pinsir","Tauros","Magikarp","Gyarados","Lapras","Ditto","Eevee","Vaporeon","Jolteon","Flareon","Porygon","Omanyte","Omastar","Kabuto","Kabutops","Aerodactyl","Snorlax","Articuno","Zapdos","Moltres","Dratini","Dragonair","Dragonite","Mewtwo","Mew"]

log = logging.getLogger(__name__)

def init_config():
    parser = argparse.ArgumentParser()
    config_file = "config.json"

    # If config file exists, load variables from json
    load   = {}
    if os.path.isfile(config_file):
        with open(config_file) as data:
            load.update(json.load(data))

    # Read passed in Arguments
    required = lambda x: not x in load
    parser.add_argument("-a", "--auth_service", help="Auth Service ('ptc' or 'google')",
        required=required("auth_service"))
    parser.add_argument("-u", "--username", help="Username", required=required("username"))
    parser.add_argument("-p", "--password", help="Password")
    parser.add_argument("-l", "--location", help="Location", required=required("location"))
    parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    parser.add_argument("-t", "--test", help="Only parse the specified location", action='store_true')
    parser.set_defaults(DEBUG=False, TEST=False)
    config = parser.parse_args()

    # Passed in arguments shoud trump
    for key in config.__dict__:
        if key in load and config.__dict__[key] == None:
            config.__dict__[key] = str(load[key])

    if config.__dict__["password"] is None:
        log.info("Secure Password Input (if there is no password prompt, use --password <pw>):")
        config.__dict__["password"] = getpass.getpass()

    if config.auth_service not in ['ptc', 'google']:
      log.error("Invalid Auth service specified! ('ptc' or 'google')")
      return None

    return config

def main():
    enable_led(LED_PIN1, False)
    enable_led(LED_PIN2, False)
    enable_led(LED_PIN3, False)
    # log format
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
    # log level for http request class
    logging.getLogger("requests").setLevel(logging.WARNING)
    # log level for main pgoapi class
    logging.getLogger("pgoapi").setLevel(logging.INFO)
    # log level for internal pgoapi class
    logging.getLogger("rpc_api").setLevel(logging.INFO)

    config = init_config()
    if not config:
        return

    if config.debug:
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("pgoapi").setLevel(logging.DEBUG)
        logging.getLogger("rpc_api").setLevel(logging.DEBUG)


    # instantiate pgoapi
    api = pgoapi.PGoApi()

    # parse position
    position = util.get_pos_by_name(config.location)
    if not position:
        log.error('Your given location could not be found by name')
        return
    elif config.test:
        return

    # set player position on the earth
    api.set_position(*position)

    # new authentication initialitation
    api.set_authentication(provider = config.auth_service, username = config.username, password =  config.password)

    # provide the FULL PATH for your encrypt .so
    api.activate_signature("/home/pi/pgoapi/libencrypt.so")
    
    while True:
        find_poi(api, position[0], position[1]);
        time.sleep(30);
    # print get maps object
    # cell_ids = util.get_cell_ids(position[0], position[1])
    # timestamps = [0,] * len(cell_ids)
    # response_dict = api.get_map_objects(latitude =position[0], longitude = position[1], since_timestamp_ms = timestamps, cell_id = cell_ids)
    # print('Response dictionary (get_player): \n\r{}'.format(pprint.PrettyPrinter(indent=4).pformat(response_dict)))


def find_poi(api, lat, lng):
    poi = {'pokemons': {}, 'forts': []}
    step_size = 0.0015
    step_limit = 1
    coords = generate_spiral(lat, lng, step_size, step_limit)

    FOUND_POKEMON = [];

    for coord in coords:
        lat = coord['lat']
        lng = coord['lng']
        api.set_position(lat, lng, 0)

        
        #get_cellid was buggy -> replaced through get_cell_ids from pokecli
        #timestamp gets computed a different way:
        cell_ids = util.get_cell_ids(lat, lng)
        timestamps = [0,] * len(cell_ids)
        response_dict = api.get_map_objects(latitude = util.f2i(lat), longitude = util.f2i(lng), since_timestamp_ms = timestamps, cell_id = cell_ids)
        if (response_dict['responses']):
            if 'status' in response_dict['responses']['GET_MAP_OBJECTS']:
                if response_dict['responses']['GET_MAP_OBJECTS']['status'] == 1:
                    for map_cell in response_dict['responses']['GET_MAP_OBJECTS']['map_cells']:
                        if 'wild_pokemons' in map_cell:
                            for pokemon in map_cell['wild_pokemons']:
                                FOUND_POKEMON.append(pokemon['pokemon_data']['pokemon_id'])
                                # pokekey = get_key_from_pokemon(pokemon)
                                # pokemon['hides_at'] = time.time() + pokemon['time_till_hidden_ms']/1000
                                # poi['pokemons'][pokekey] = pokemon

        time.sleep(0.51)

    for x in FOUND_POKEMON:
        print("#{} NEARBY, {}!".format(x,POKE_NAMES[x-1]))
        if(x in COMMON_POKE):
            enable_led(17,True)
        if(x in UNCOMMON_POKE or x in RARE_POKE or x in VERY_RARE_POKE or x in EPIC_POKE or x in LEGENDARY_POKE):
            print("RARE POKEMON FOUND!")
            enable_led(27,True)
            enable_led(22,True)
    # new dict, binary data
    # print('POI dictionary: \n\r{}'.format(json.dumps(poi, indent=2)))
    # print('POI dictionary: \n\r{}'.format(pprint.PrettyPrinter(indent=4).pformat(poi)))
    # print(poi['pokemons']['pokemon_data']['pokemon_id'])
    
    # for x in poi['pokemons']:
    #     print(poi['pokemons'][x])



    # print('Open this in a browser to see the path the spiral search took:')
    # print_gmaps_dbug(coords)


def get_key_from_pokemon(pokemon):
    return '{}-{}'.format(pokemon['spawn_point_id'], pokemon['pokemon_data']['pokemon_id'])

def print_gmaps_dbug(coords):
    url_string = 'http://maps.googleapis.com/maps/api/staticmap?size=400x400&path='
    for coord in coords:
        url_string += '{},{}|'.format(coord['lat'], coord['lng'])
    print(url_string[:-1])

def generate_spiral(starting_lat, starting_lng, step_size, step_limit):
    coords = [{'lat': starting_lat, 'lng': starting_lng}]
    steps,x,y,d,m = 1, 0, 0, 1, 1
    rlow = 0.0
    rhigh = 0.0005

    while steps < step_limit:
        while 2 * x * d < m and steps < step_limit:
            x = x + d
            steps += 1
            lat = x * step_size + starting_lat + random.uniform(rlow, rhigh)
            lng = y * step_size + starting_lng + random.uniform(rlow, rhigh)
            coords.append({'lat': lat, 'lng': lng})
        while 2 * y * d < m and steps < step_limit:
            y = y + d
            steps += 1
            lat = x * step_size + starting_lat + random.uniform(rlow, rhigh)
            lng = y * step_size + starting_lng + random.uniform(rlow, rhigh)
            coords.append({'lat': lat, 'lng': lng})

        d = -1 * d
        m = m + 1
    return coords


if __name__ == '__main__':
    main()
