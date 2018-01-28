#!/usr/bin/env python3

from argparse import ArgumentParser
from CurseMetaDB.DB import DB
from json import loads, dumps
from sys import exit
from os.path import isfile, isdir, join
from os import makedirs, remove, statvfs, getcwd
from hashlib import sha1

import urllib.request
import urllib.parse
import multiprocessing
import tqdm
import sys

parser = ArgumentParser()

parser.add_argument("metafile", help="Path to latest CurseMetaDB json file", type=str)

parser.add_argument("-m", "--include-mods", action="store_true")
parser.add_argument("-p", "--include-mod-packs", action="store_true")
parser.add_argument("-t", "--include-texture-packs", action="store_true")
parser.add_argument("-w", "--include-worlds", action="store_true")
parser.add_argument("-j", "--threads", default=multiprocessing.cpu_count(), type=int)
parser.add_argument("-n", "--no-check-diskspace", action="store_true")
parser.add_argument("-d", "--diskspace-limit", default=90, type=int)

args = parser.parse_args()

PROJECT_TYPES = ["modpack", "mod", "texturepack", "world"]

types = list()
if args.include_mods:
    types.append(1)
if args.include_mod_packs:
    types.append(0)
if args.include_texture_packs:
    types.append(2)
if args.include_worlds:
    types.append(3)

if len(types) < 1:
    print("Nothing to do!")
    exit(1)

print("Loading DB, this may take a while...")
meta = loads(open(args.metafile).read())

files = [i for i in meta["files"].values() if meta["projects"][str(i["project"])]["type"] in types]

file_types = {}

for f in files:
    file_types[f["id"]] = PROJECT_TYPES[meta["projects"][str(f["project"])]["type"]]

print("Found {} files".format(len(files)))

print("Loading existing data")

if not isfile("data.json"):
    open("data.json", "w+").write("{}")

dat = loads(open("data.json").read())

files = [i for i in files if str(i["id"]) not in dat.keys()]
lenf = len(files)

print("Found {} new files".format(lenf))

if not isdir("downloaded_files"):
    makedirs("downloaded_files")

for i in types:
    if not isdir(join("downloaded_files", PROJECT_TYPES[i])):
        makedirs(join("downloaded_files", PROJECT_TYPES[i]))


def process(file):
    tg = join("downloaded_files", file_types[file["id"]], "{}-{}".format(file["id"], file["filename"]))
    url = file["url"]
    try:
        _1, _2, _3, _4, _5 = urllib.parse.urlsplit(url)
        url = urllib.parse.urlunsplit((_1, _2, urllib.parse.quote(_3), _4, _5))
        urllib.request.urlretrieve(url, tg)
        with open(tg, 'rb') as f:
            d = f.read()
            return file["id"], {"hash": sha1(d).hexdigest(), "size": len(d)}
    except KeyboardInterrupt:
        if isfile(tg):  # avoid half-done files
            try:
                remove(tg)
            except:
                pass
        raise
    except:
        tqdm.tqdm.write("Error on downloading/hashing {} {}".format(file["id"], url))
        if isfile(tg):  # avoid half-done files
            try:
                remove(tg)
            except:
                pass


try:
    with multiprocessing.Pool(args.threads) as p:
        with tqdm.tqdm(total=len(files)) as pbar:
            for i, r in tqdm.tqdm(enumerate(p.imap_unordered(process, files))):
                if r is not None:
                    dat[r[0]] = r[1]
                if i % 100 == 0:
                    open("data.json", "w").write(dumps(dat, separators=(",", ":")))

                    statvfs_r = statvfs(getcwd())
                    if not args.no_check_diskspace and (statvfs_r.f_bavail / statvfs_r.f_blocks) < 1 / (100 - args.diskspace_limit):
                        percent = str((statvfs_r.f_bavail / statvfs_r.f_blocks)*100)
                        raise Exception("File system < {}% free space stopping as a precaution ({}%)".format(100 - args.diskspace_limit, percent))

                pbar.update()
finally:
    open("data.json", "w").write(dumps(dat, separators=(",", ":")))
