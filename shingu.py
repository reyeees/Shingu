from sys import executable as PYTHON
from os import system
from importlib.util import find_spec

# installing packages if user is 怠け者
missing = []
for package in ("pillow", "numpy", "networkx"):
    if find_spec(package) is None:
        missing.append(package)
if missing != []:
    system(f"\"{PYTHON}\" -m pip install {' '.join(missing)}")
del PYTHON, system, find_spec, missing

# Actual code starts here

from lib import (
    PathFinder, Cluster, Caching,
    rgb_to_lab, lab_to_rgb, is_supported
)

import numpy as np
from sys import argv
from os import (
    walk, mkdir, path
)
from shutil import copy2 as copy
from datetime import datetime
from PIL import Image


class Core:
    def __init__(self, dir_input: str, dir_output: str) -> None:
        self.path: str = dir_input
        self.output_dir: str = "out"
        if dir_output.strip() != "":
            self.output_dir = dir_output.strip()
        
        self.cache: Caching = Caching()
        self.cluster: Cluster = Cluster()
        self.path_finder: PathFinder = PathFinder()

        self.files: list[tuple[str]] = []
        self.dominants: list[tuple[int]] = []
        self.orders: list[int] = {}

    def percents(self, ln, ind) -> str:
        return "{}/{} {}%".format(
            ind, ln, round(ind / ln * 100, 2)
        )

    def get_dominants(self) -> None:
        for obj in self.files:
            print(self.percents(len(self.files), self.files.index(obj)), end = "\r")
            if obj[1]:
                dom = self.cache.get(obj[0])
            else:
                img = Image.open(obj[0])
                dom = self.cluster.get_palette(img, 3, 10)[0]
                dom = tuple(map(lambda x: x / 255, rgb_to_lab(*dom)))
                img.close()
                self.cache.set(obj[0], dom)
            self.dominants.append(dom)

    def get_files(self) -> None:
        obj = walk(self.path)
        for ls in obj:
            for file in ls[2]:
                tail_file = path.join(ls[0], file)
                if is_supported(tail_file):
                    self.files.append((tail_file, self.cache.cached(tail_file)))

    def get_orders(self) -> None:
        orders = self.path_finder.find_shortest_tour(np.array(self.dominants))
        self.orders = list(dict.fromkeys(orders)) # this removes dups and saving the order, since the `set` also sorting things.

    def move_things(self) -> None:
        if self.output_dir not in walk(".").__next__()[1]:
            mkdir(self.output_dir)

        for num, file in enumerate(np.array(self.files)[self.orders]):
            print(self.percents(len(self.files), num + 1), end = "\r")
            _, head = path.split(file[0])
            out_file = path.join(self.output_dir, f"{num}_{head}")
            copy(file[0], out_file)
        print()

    def create_palette(self) -> None:
        colors = map(lambda x: lab_to_rgb(*tuple(i * 255 for i in x)), self.dominants)
        colors = np.array(list(colors))[self.orders]
        obj = np.tile(colors, (100, 1, 1)).astype(np.uint8)
        Image.fromarray(obj).save(f"{datetime.now().strftime('%d%m%Y%H%M%S')}_palette.png")

    def init(self) -> None:
        self.get_files()
        print("Got files")
        self.get_dominants()
        print("\nGot dominants")
        self.cache.write_file()
        print("Caching things")
        self.get_orders()
        print("Got the order")
        self.move_things()
        print("Things are sorted")
        self.create_palette()
        print("Served you a palette.")


if __name__ == "__main__":
    i_nput, output = ("", "")
    if len(argv) < 2:
        exit(
            f"Using: \"{argv[0]}\" [directory] (output directory)"
            "\n\t--------------------------------------"
            "\n\tdirectory -> Folder with images to sort"
            "\n\toutput directory -> output directory in which images will be moved"
        )
    if len(argv) >= 2:
        i_nput = argv[1]
    if len(argv) >= 3:
        output = argv[2]

    Core(i_nput, output).init()
