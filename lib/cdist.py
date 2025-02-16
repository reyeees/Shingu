import numpy as np


class CDist:
    # NOTE copied from scipy.spatial.distance and adaptated under program
    def __init__(self) -> None:
        pass

    def _prepare_out_argument(self, out, dtype, expected_shape):
        if out is None:
            return np.empty(expected_shape, dtype = dtype)

        if out.shape != expected_shape:
            raise ValueError("Output array has incorrect shape.")
        if not out.flags.c_contiguous:
            raise ValueError("Output array must be C-contiguous.")
        if out.dtype != np.float64:
            raise ValueError("Output array must be double type.")
        return out

    def _cdist_callable(self, XA, XB, *, out, metric, **kwargs):
        mA = XA.shape[0]
        mB = XB.shape[0]
        dm = self._prepare_out_argument(out, np.float64, (mA, mB))
        for i in range(mA):
            for j in range(mB):
                dm[i, j] = metric(XA[i], XB[j], **kwargs)
        return dm

    def cdist(self, XA, XB, metric, *, out = None, **kwargs):
        XA = np.asarray(XA)
        XB = np.asarray(XB)

        s = XA.shape
        sB = XB.shape

        if len(s) != 2:
            raise ValueError('XA must be a 2-dimensional array.')
        if len(sB) != 2:
            raise ValueError('XB must be a 2-dimensional array.')
        if s[1] != sB[1]:
            raise ValueError('XA and XB must have the same number of columns '
                            '(i.e. feature dimension.)')

        return self._cdist_callable(XA, XB, metric = metric, out = out, **kwargs)
