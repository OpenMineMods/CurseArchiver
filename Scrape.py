from argparse import ArgumentParser
from CurseMetaDB.DB import DB
from json import loads, dumps
from sys import exit
from os.path import isfile, isdir, join
from os import makedirs, remove

from hashlib import sha1
import urllib.request
import multiprocessing

parser = ArgumentParser()

parser.add_argument("metafile", help="Path to latest CurseMetaDB json file", type=str)

parser.add_argument("-m", "--include-mods", action="store_true")
parser.add_argument("-p", "--include-mod-packs", action="store_true")
parser.add_argument("-t", "--include-texture-packs", action="store_true")
parser.add_argument("-w", "--include-worlds", action="store_true")
parser.add_argument("-j", "--threads", default=multiprocessing.cpu_count(), type=int)

args = parser.parse_args()

types = list()
if args.include_mods:
    types.append("mod")
if args.include_mod_packs:
    types.append("modpack")
if args.include_texture_packs:
    types.append("texturepack")
if args.include_worlds:
    types.append("world")

print(types)
if len(types) < 1:
    print("Nothing to do!")
    exit(1)

print("Loading DB, this may take a while...")
db = DB(loads(open(args.metafile).read()))

to_dl = list()
for ptype in types:
    to_dl += db.popular[ptype]

print("Found {} projects".format(len(to_dl)))

files = list()
file_types = dict()
for proj in to_dl:
    proj = db.get_project(proj)
    for f in proj["files"]:
        files.append(f)
        file_types[f] = proj["type"]

files = list(set(files))

print("Loading existing data")

if not isfile("data.json"):
    open("data.json", "w+").write("{}")

dat = loads(open("data.json").read())

files = [db.get_file(i) for i in files if str(i) not in dat.keys()]
lenf = len(files)

print("Found {} new files".format(lenf))

if not isdir("downloaded_files"):
    makedirs("downloaded_files")

for i in types:
    if not isdir(join("downloaded_files", i)):
        makedirs(join("downloaded_files", i))


def process(args):
    x, file = args
    fdr = file_types[file["id"]]
    tg = join("downloaded_files", fdr, file["filename"])
    print("Downloading file {}/{} ({}/{})".format(x + 1, lenf, fdr, file["filename"]))
    try:
        urllib.request.urlretrieve(file["url"], tg)
        with open(tg, 'rb') as f:
            d = f.read()
            dat[file["id"]] = {"hash": sha1(d).hexdigest(), "size": len(d)}
    except KeyboardInterrupt:
        if isfile(tg):  # avoid half-done files
            try:
                remove(tg)
            except:
                pass
        raise
    except:
        print("Error on downloading/hashing", file["id"])
        if isfile(tg):  # avoid half-done files
            try:
                remove(tg)
            except:
                pass


try:
    with multiprocessing.Pool(args.threads) as p:
        p.map(process, enumerate(files))
finally:
    open("data.json", "w").write(dumps(dat, separators=(",", ":")))
