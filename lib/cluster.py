from math import sqrt, pow

from PIL import Image


class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, type):
        res = instance.__dict__[self.func.__name__] = self.func(instance)
        return res


class Cluster:
    def __init__(self):
        pass

    def get_palette(self, file: Image, color_count = 10, quality = 10):
        image = file.convert('RGB')
        pixels = image.getdata()
        valid_pixels = []
        for i in range(0, image.size[0] * image.size[1], quality):
            r, g, b = pixels[i]
            if not (r > 250 and g > 250 and b > 250):
                valid_pixels.append((r, g, b))

        cmap = MMCQ.quantize(valid_pixels, color_count)
        return cmap.palette


class MMCQ(object):
    SIGBITS = 5
    RSHIFT = 8 - SIGBITS
    MAX_ITERATION = 1000
    FRACT_BY_POPULATIONS = 0.75

    @staticmethod
    def get_color_index(r, g, b):
        return (r << (2 * MMCQ.SIGBITS)) + (g << MMCQ.SIGBITS) + b

    @staticmethod
    def get_histo(pixels):
        histo = dict()
        for pixel in pixels:
            index = MMCQ.get_color_index(
                pixel[0] >> MMCQ.RSHIFT, 
                pixel[1] >> MMCQ.RSHIFT, 
                pixel[2] >> MMCQ.RSHIFT
            )
            histo[index] = histo.setdefault(index, 0) + 1
        return histo

    @staticmethod
    def vbox_from_pixels(pixels, histo):
        rmin = 1000000
        rmax = 0
        gmin = 1000000
        gmax = 0
        bmin = 1000000
        bmax = 0
        for pixel in pixels:
            rval = pixel[0] >> MMCQ.RSHIFT
            gval = pixel[1] >> MMCQ.RSHIFT
            bval = pixel[2] >> MMCQ.RSHIFT
            rmin = min(rval, rmin)
            rmax = max(rval, rmax)
            gmin = min(gval, gmin)
            gmax = max(gval, gmax)
            bmin = min(bval, bmin)
            bmax = max(bval, bmax)
        return VBox(rmin, rmax, gmin, gmax, bmin, bmax, histo)

    @staticmethod
    def median_cut_apply(histo, vbox):
        if not vbox.count:
            return (None, None)

        rw = vbox.r2 - vbox.r1 + 1
        gw = vbox.g2 - vbox.g1 + 1
        bw = vbox.b2 - vbox.b1 + 1
        maxw = max([rw, gw, bw])
        
        if vbox.count == 1:
            return (vbox.copy, None)
        
        total = 0
        sum_ = 0
        partialsum = {}
        lookaheadsum = {}
        do_cut_color = None
        if maxw == rw:
            do_cut_color = 'r'
            for i in range(vbox.r1, vbox.r2+1):
                sum_ = 0
                for j in range(vbox.g1, vbox.g2+1):
                    for k in range(vbox.b1, vbox.b2+1):
                        index = MMCQ.get_color_index(i, j, k)
                        sum_ += histo.get(index, 0)
                total += sum_
                partialsum[i] = total
        elif maxw == gw:
            do_cut_color = 'g'
            for i in range(vbox.g1, vbox.g2+1):
                sum_ = 0
                for j in range(vbox.r1, vbox.r2+1):
                    for k in range(vbox.b1, vbox.b2+1):
                        index = MMCQ.get_color_index(j, i, k)
                        sum_ += histo.get(index, 0)
                total += sum_
                partialsum[i] = total
        else:
            do_cut_color = 'b'
            for i in range(vbox.b1, vbox.b2+1):
                sum_ = 0
                for j in range(vbox.r1, vbox.r2+1):
                    for k in range(vbox.g1, vbox.g2+1):
                        index = MMCQ.get_color_index(j, k, i)
                        sum_ += histo.get(index, 0)
                total += sum_
                partialsum[i] = total
        for i, d in partialsum.items():
            lookaheadsum[i] = total - d

        dim1 = do_cut_color + '1'
        dim2 = do_cut_color + '2'
        dim1_val = getattr(vbox, dim1)
        dim2_val = getattr(vbox, dim2)
        for i in range(dim1_val, dim2_val+1):
            if partialsum[i] > (total / 2):
                vbox1 = vbox.copy
                vbox2 = vbox.copy
                left = i - dim1_val
                right = dim2_val - i
                if left <= right:
                    d2 = min([dim2_val - 1, int(i + right / 2)])
                else:
                    d2 = max([dim1_val, int(i - 1 - left / 2)])
                while not partialsum.get(d2, False):
                    d2 += 1
                count2 = lookaheadsum.get(d2)
                while not count2 and partialsum.get(d2-1, False):
                    d2 -= 1
                    count2 = lookaheadsum.get(d2)
                setattr(vbox1, dim2, d2)
                setattr(vbox2, dim1, getattr(vbox1, dim2) + 1)
                return (vbox1, vbox2)
        return (None, None)

    @staticmethod
    def quantize(pixels, max_color):
        if not pixels:
            raise Exception('Empty pixels when quantize.')
        if max_color < 2 or max_color > 256:
            raise Exception('Wrong number of max colors when quantize.')

        histo = MMCQ.get_histo(pixels)

        if len(histo) <= max_color:
            pass

        vbox = MMCQ.vbox_from_pixels(pixels, histo)
        pq = PQueue(lambda x: x.count)
        pq.push(vbox)

        def iter_(lh, target):
            n_color = 1
            n_iter = 0
            while n_iter < MMCQ.MAX_ITERATION:
                vbox = lh.pop()
                if not vbox.count:
                    lh.push(vbox)
                    n_iter += 1
                    continue
                
                vbox1, vbox2 = MMCQ.median_cut_apply(histo, vbox)
                if not vbox1:
                    raise Exception("vbox1 not defined; shouldn't happen!")
                lh.push(vbox1)
                if vbox2:
                    lh.push(vbox2)
                    n_color += 1
                if n_color >= target:
                    return
                if n_iter > MMCQ.MAX_ITERATION:
                    return
                n_iter += 1

        iter_(pq, MMCQ.FRACT_BY_POPULATIONS * max_color)

        pq2 = PQueue(lambda x: x.count * x.volume)
        while pq.size():
            pq2.push(pq.pop())

        iter_(pq2, max_color - pq2.size())

        cmap = CMap()
        while pq2.size():
            cmap.push(pq2.pop())
        return cmap


class VBox(object):
    """3d color space box"""
    def __init__(self, r1, r2, g1, g2, b1, b2, histo):
        self.r1 = r1
        self.r2 = r2
        self.g1 = g1
        self.g2 = g2
        self.b1 = b1
        self.b2 = b2
        self.histo = histo

    @cached_property
    def volume(self):
        sub_r = self.r2 - self.r1
        sub_g = self.g2 - self.g1
        sub_b = self.b2 - self.b1
        return (sub_r + 1) * (sub_g + 1) * (sub_b + 1)

    @property
    def copy(self):
        return VBox(self.r1, self.r2, self.g1, self.g2,
                    self.b1, self.b2, self.histo)

    @cached_property
    def avg(self):
        ntot = 0
        mult = 1 << (8 - MMCQ.SIGBITS)
        r_sum = 0
        g_sum = 0
        b_sum = 0
        for i in range(self.r1, self.r2 + 1):
            for j in range(self.g1, self.g2 + 1):
                for k in range(self.b1, self.b2 + 1):
                    histoindex = MMCQ.get_color_index(i, j, k)
                    hval = self.histo.get(histoindex, 0)
                    ntot += hval
                    r_sum += hval * (i + 0.5) * mult
                    g_sum += hval * (j + 0.5) * mult
                    b_sum += hval * (k + 0.5) * mult

        if ntot:
            r_avg = int(r_sum / ntot)
            g_avg = int(g_sum / ntot)
            b_avg = int(b_sum / ntot)
        else:
            r_avg = int(mult * (self.r1 + self.r2 + 1) / 2)
            g_avg = int(mult * (self.g1 + self.g2 + 1) / 2)
            b_avg = int(mult * (self.b1 + self.b2 + 1) / 2)

        return r_avg, g_avg, b_avg

    def contains(self, pixel):
        rval = pixel[0] >> MMCQ.RSHIFT
        gval = pixel[1] >> MMCQ.RSHIFT
        bval = pixel[2] >> MMCQ.RSHIFT
        return all([
            rval >= self.r1,
            rval <= self.r2,
            gval >= self.g1,
            gval <= self.g2,
            bval >= self.b1,
            bval <= self.b2,
        ])

    @cached_property
    def count(self):
        npix = 0
        for i in range(self.r1, self.r2 + 1):
            for j in range(self.g1, self.g2 + 1):
                for k in range(self.b1, self.b2 + 1):
                    index = MMCQ.get_color_index(i, j, k)
                    npix += self.histo.get(index, 0)
        return npix


class CMap(object):
    def __init__(self):
        self.vboxes = PQueue(lambda x: x['vbox'].count * x['vbox'].volume)

    @property
    def palette(self):
        return self.vboxes.map(lambda x: x['color'])

    def push(self, vbox):
        self.vboxes.push({
            'vbox': vbox,
            'color': vbox.avg,
        })

    def size(self):
        return self.vboxes.size()

    def nearest(self, color):
        d1 = None
        p_color = None
        for i in range(self.vboxes.size()):
            vbox = self.vboxes.peek(i)
            d2 = sqrt(
                pow(color[0] - vbox['color'][0], 2) +
                pow(color[1] - vbox['color'][1], 2) +
                pow(color[2] - vbox['color'][2], 2)
            )
            if d1 is None or d2 < d1:
                d1 = d2
                p_color = vbox['color']
        return p_color

    def map(self, color):
        for i in range(self.vboxes.size()):
            vbox = self.vboxes.peek(i)
            if vbox['vbox'].contains(color):
                return vbox['color']
        return self.nearest(color)


class PQueue(object):
    def __init__(self, sort_key):
        self.sort_key = sort_key
        self.contents = []
        self._sorted = False

    def sort(self):
        self.contents.sort(key=self.sort_key)
        self._sorted = True

    def push(self, o):
        self.contents.append(o)
        self._sorted = False

    def peek(self, index=None):
        if not self._sorted:
            self.sort()
        if index is None:
            index = len(self.contents) - 1
        return self.contents[index]

    def pop(self):
        if not self._sorted:
            self.sort()
        return self.contents.pop()

    def size(self):
        return len(self.contents)

    def map(self, f):
        return list(map(f, self.contents))
