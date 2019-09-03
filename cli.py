""" Tesla API CLI application using TeslaPy module """

# Author: Tim Dorssers

from __future__ import print_function
import argparse
import teslapy
import logging
import getpass
import json

CLIENT_ID='e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e'
CLIENT_SECRET='c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220'

def main():
    parser = argparse.ArgumentParser(description='Tesla API CLI')
    parser.add_argument('-e', dest='email', help='login email', required=True)
    parser.add_argument('-p', dest='password', help='login password')
    parser.add_argument('-f', dest='filter', help='filter on id, vin, etc.')
    parser.add_argument('-a', dest='api', help='API call endpoint name')
    parser.add_argument('-k', dest='keyvalue', help='API parameter (key=value)',
                        action='append', type=lambda kv: kv.split('=', 1))
    parser.add_argument('-l', '--list', action='store_true',
                        help='list all selected vehicles')
    parser.add_argument('-o', '--option', action='store_true',
                        help='list vehicle option codes')
    parser.add_argument('-w', '--wake', action='store_true',
                        help='wake up selected vehicle(s)')
    parser.add_argument('-g', '--get', action='store_true',
                        help='get rollup of all vehicle data')
    parser.add_argument('-n', '--nearby', action='store_true',
                        help='list nearby charging sites')
    parser.add_argument('-m', '--mobile', action='store_true',
                        help='get mobile enabled state')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='set logging level to debug')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    password = args.password if args.password else getpass.getpass('Password: ')
    with teslapy.Tesla(args.email, password, CLIENT_ID, CLIENT_SECRET) as tesla:
        tesla.fetch_token()
        selected = cars = tesla.vehicle_list()
        if args.filter:
            selected = [c for c in cars for v in c.values() if v == args.filter]
        logging.info('%d vehicle(s), %d selected' % (len(cars), len(selected)))
        for vehicle in selected:
            if args.list:
                print(vehicle)
            if args.option:
                print(', '.join(vehicle.option_code_list()))
            if args.wake:
                vehicle.sync_wake_up()
            if args.get:
                print(vehicle.get_vehicle_data())
            if args.nearby:
                print(json.dumps(vehicle.get_nearby_charging_sites(), indent=4))
            if args.mobile:
                print(vehicle.mobile_enabled())
            if args.api:
                data = dict(args.keyvalue) if args.keyvalue else None
                logging.debug('API parameters: ' + json.dumps(data))
                print(json.dumps(vehicle.api(args.api, data=data), indent=4))

if __name__ == "__main__":
    main()
