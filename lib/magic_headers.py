magic_bytes: dict[bytes, bool] = {
    b"\x89PNG\r\n\x1a\n":                    True, # PNG
    b"\x00\x00\x00\x0cjP  \r\n\x87\n":       True, # JPEG 2000
    b"\xffO\xffQ":                           True, # JPEG 2000 x2
    b"\xff\xd8\xff\xdb":                     True, # JPEG RAW or EXIF
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01": True, # JPEG or JFIF
    b"RIFF":           lambda x: x[-4:] == "WEBP", # ?? - file size RIFF ?? ?? ?? ?? WEBP
    b"BM":                                   True, # WINDOWS BITMAP, DIB
    b"GIF87a":                               True, # GIF 87
    b"GIF89a":                               True, # GIF 89
    b"P3\n":                                 True, # PPM, PBM, PGM, PPM, PNM
    # also there should be tga
    b"MM\x00*":                              True, # TIFF
    b"MM\x00+":                              True, # BigTIFF
    b"II+\x00":                              True, # BigTIFF (l-endian)
}

def is_supported(file_name) -> bool:
    magic = b''
    with open(file_name, "rb") as _file:
        magic = _file.read(12)
        _file.close()
    
    # i know that sucks, but that what my brain can make
    for key in magic_bytes.keys():
        if magic.startswith(key):
            obj = magic_bytes[key]
            if type(obj) != bool: # webp
                return obj(magic)
            return obj
    return False
