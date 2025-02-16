def rgb_to_xyz(r, g, b):
    r, g, b = [v / 255.0 for v in (r, g, b)]

    def gamma_correct(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = map(gamma_correct, (r, g, b))

    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    return (x, y, z)

def xyz_to_lab(x, y, z):
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883  
    x, y, z = x / Xn, y / Yn, z / Zn  

    def f(t):
        return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16 / 116)

    fx, fy, fz = f(x), f(y), f(z)

    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    return (L, a, b)

def rgb_to_lab(r, g, b):
    x, y, z = rgb_to_xyz(r, g, b)
    return xyz_to_lab(x, y, z)

# ------------ LAB TO RGB ----------

def lab_to_xyz(L, a, b):
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883  

    def f_inv(t):
        return t ** 3 if t > 0.206893 else (t - 16 / 116) / 7.787

    fy = (L + 16) / 116
    fx = fy + (a / 500)
    fz = fy - (b / 200)

    x = f_inv(fx) * Xn
    y = f_inv(fy) * Yn
    z = f_inv(fz) * Zn

    return (x, y, z)

def xyz_to_rgb(x, y, z):
    r = x *  3.2404542 + y * -1.5371385 + z * -0.4985314
    g = x * -0.9692660 + y *  1.8760108 + z *  0.0415560
    b = x *  0.0556434 + y * -0.2040259 + z *  1.0572252

    def gamma_correct(v):
        return 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1/2.4)) - 0.055

    r, g, b = map(gamma_correct, (r, g, b))

    r, g, b = [max(0, min(255, int(round(v * 255)))) for v in (r, g, b)]

    return (r, g, b)

def lab_to_rgb(L, a, b):
    x, y, z = lab_to_xyz(L, a, b)
    return xyz_to_rgb(x, y, z)
