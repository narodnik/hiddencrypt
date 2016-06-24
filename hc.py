#!/usr/bin/python3
import argparse
import sys
import os.path
import configparser
import pickle
import struct
import getpass
import random

import lookup
import util

class HiddenCrypt:

    def __init__(self, options):
        self._initialize_config_path(options)

        if self._is_setup():
            self._load_config()
        else:
            self._setup()

    def _initialize_config_path(self, options):
        self._path = options.config
        if not self._path:
            # Default path
            self._path = os.path.join(os.path.expanduser("~"), ".hiddencrypt")

    @property
    def _rc_file(self):
        return os.path.join(self._path, "hc.rc")
    @property
    def _slab_file(self):
        return os.path.join(self._path, "slab")
    @property
    def _lookup_file(self):
        return os.path.join(self._path, "lookup")

    def _is_setup(self):
        return os.path.isfile(self._rc_file)

    def _setup(self):
        print("Please wait. Initializing HiddenCrypt for the first time...")
        os.makedirs(self._path, exist_ok=True)

        config = configparser.ConfigParser()
        config["main"] = {"offset_mult": "100MB",
                          "volumes_limit": "10",
                          "random_padding": "2MB",
                          "mapping_name": "HiddenCrypt",
                          "mapping_path": "/dev/mapper/",
                          "mount_path": "/mnt"}

        with open(self._rc_file, "w") as configfile:
            config.write(configfile)

        offset_mult = 100 * 1000 * 1000
        self._setup_slab(offset_mult, 10)

        self._lookup = lookup.Lookup(self._lookup_file)
        self._lookup.setup()

        # Create 10 fake volumes
        self._load_config()
        for i in range(10):
            password = os.urandom(20)
            self.new(password, volume_id=i, is_fake=True)
        print("Done.")

    def _load_config(self):
        config = configparser.RawConfigParser()
        config.read(self._rc_file)

        main = config["main"]
        self._offset_mult = main["offset_mult"]
        self._volumes_limit = int(main["volumes_limit"])
        self._random_padding = main["random_padding"]

        self._options = {"mapping_name": main["mapping_name"],
                         "mapping_path": main["mapping_path"],
                         "mount_path": main["mount_path"]}

        self._offset_mult = util.size_to_bytesize(self._offset_mult)
        self._random_padding = util.size_to_bytesize(self._random_padding)

        self._volume_size = self._offset_mult - self._random_padding

        self._lookup = lookup.Lookup(self._lookup_file)
        self._lookup.load()

    def _setup_slab(self, offset_mult, volumes_limit):
        filesize = volumes_limit * offset_mult
        util.create_blank_file(self._slab_file, filesize)

    def new(self, password, volume_id=None, is_fake=False):
        if volume_id is None:
            volume_id = random.randrange(0, self._volumes_limit)
        offset = volume_id * self._offset_mult
        offset += random.randrange(0, self._random_padding)

        self._lookup.add(password, offset)

        util.setup_volume(password, offset, self._volume_size,
                          self._slab_file, self._options, is_fake)

    def open(self, password):
        offset = self._lookup.get(password)

        util.mount_volume(password, offset, self._volume_size,
                          self._slab_file, self._options)

    def close(self):
        util.close_volume(self._options)

# hc new [VOLUME]
def command_new(args):
    hc = HiddenCrypt(args)
    print("No volume ID selected. Choosing a random ID.")
    print("Please enter a password.")
    password = getpass.getpass()
    password_again = getpass.getpass(prompt="Again: ")
    if password != password_again:
        util.error("Non-matching passwords.")
        return -1
    password = str.encode(password)
    hc.new(password)
    return 0

def command_open(args):
    hc = HiddenCrypt(args)
    password = getpass.getpass()
    password = str.encode(password)
    hc.open(password)
    return 0

def command_close(args):
    hc = HiddenCrypt(args)
    hc.close()
    return 0

def main():
    parser = argparse.ArgumentParser(prog="HiddenCrypt")
    parser.add_argument('--version', "-v", action='version',
                        version='%(prog)s 2.0')
    parser.add_argument("--config", "-c", dest="config",
                        help="Change default config directory.")
    subparsers = parser.add_subparsers(help="commands")

    parser_new = subparsers.add_parser("new",
        help="create a new encrypted volume")
    parser_new.set_defaults(func=command_new)

    parser_open = subparsers.add_parser("open",
        help="open an encrypted volume")
    parser_open.set_defaults(func=command_open)

    parser_close = subparsers.add_parser("close",
        help="close an encrypted volume")
    parser_close.set_defaults(func=command_close)

    args = parser.parse_args()
    try:
        return args.func(args)
    except AttributeError:
        parser.print_help()
        return -1

if __name__ == "__main__":
    sys.exit(main())

