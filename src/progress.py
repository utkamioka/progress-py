class ProgressHelper:
    # noinspection PyShadowingBuiltins
    def __init__(self, min: float=0, max: float=100, notify_on_init: bool=False, func: callable=None):
        assert min < max
        self.min = min
        self.max = max
        self.func = func

        self.rate = 0.0

        if notify_on_init:
            self._notify(self.rate)

    def __str__(self):
        return 'ProgressHelper(min={},max={},rate={},func={})'.format(self.min, self.max, self.rate, self.func)

    def _pos(self, rate: float) -> float:
        return (self.max - self.min) * rate + self.min

    def _notify(self, rate, *args, **kwargs):
        if callable(self.func):
            self.func(self._pos(rate), *args, **kwargs)

    def set(self, rate: float, *args, **kwargs):
        self.rate = rate
        self._notify(rate, *args, **kwargs)

    def done(self, *args, **kwargs):
        self.set(1.0, *args, **kwargs)

    def sub(self, low: float=0.0, high: float=1.0):
        assert low < high
        return ProgressHelper(min=self._pos(low), max=self._pos(high), func=self.func)

    def remain(self):
        return ProgressHelper(min=self._pos(self.rate), max=self._pos(1.0), func=self.func)

    def split(self, v: tuple or list or int):
        if not isinstance(v, (list, tuple)):
            return self.split([1] * v)

        def sum_range(index, ary):
            """
            :return: 配列先頭からindex番目までの和
            """
            return sum(ary[0:index+1])

        ranged_sum = [sum_range(i, v) for i in range(len(v))]

        total = sum(v)
        b = [n/total for n in ranged_sum]
        a = [0.0] + b[:-1]
        return (self.sub(*r) for r in zip(a, b))

    def seq(self, seq, *args, **kwargs):
        lst = list(seq)  # type: list
        sub_p = self.split(len(lst))
        for (e, p) in zip(lst, sub_p):
            yield e
            p.done(*args, **kwargs)


