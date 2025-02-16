import gzip
from glob import glob
from typing import Generator


class Caching:
    def __init__(self) -> None:
        self.cache_file: str = "cache.psort"

        self.cache = {}
        self.open_file()

    def cached(self, filename: str) -> bool:
        return filename in self.cache
    
    def get(self, filename: str) -> tuple[float]:
        return self.cache[filename]
    
    def set(self, filename: str, value: tuple[float]) -> None:
        self.cache[filename] = value

    def compressing_process(self) -> Generator[bytes, None, None]:
        for obj in self.cache.keys():
            yield "{}\x07{}\n".format(obj, str(self.cache[obj])\
                                      .replace(" ", "")).encode()

    def uncompressing_process(self, iterator: Generator) -> \
            Generator[list[str, tuple[float]], None, None]:
        for line in iterator:
            line = line.decode().strip(")\n").split("\x07(")
            yield (line[0], tuple([float(x) for x in line[1].split(",")]))

    def open_file(self) -> None:
        if self.cache_file not in glob("*"):
            return

        with gzip.open(self.cache_file, "rb") as _file:
            for line in self.uncompressing_process(_file):
                self.cache[line[0]] = line[1]
            _file.close()

    def write_file(self) -> None:
        with gzip.open(self.cache_file, "wb") as _file:
            for obj in self.compressing_process():
                _file.write(obj)
            _file.close()


if __name__ == "__main__":
    cache = Caching()
    print(cache.cache)
    print(cache.cached("10"))
