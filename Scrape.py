from argparse import ArgumentParser
from CurseMetaDB.DB import DB

parser = ArgumentParser()

parser.add_argument("metafile", help="Path to latest cursemeta json file", type=str)

parser.add_argument("-m", "--include-mods", action="store_true")
parser.add_argument("-p", "--include-mod-packs", action="store_true")
parser.add_argument("-t", "--include-texture-packs", action="store_true")
parser.add_argument("-w", "--include-worlds", action="store_true")

args = parser.parse_args()