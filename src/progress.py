import sys
from typing import Iterable, TypeVar, Generator, List, Tuple, Iterator, Union, Optional, Callable
from itertools import accumulate

T = TypeVar('T')


class ProgressHelper(object):
    # noinspection PyUnresolvedReferences
    """プログレス（進捗）管理クラス。

    Examples:

        >>> from logging import getLogger
        >>> logger = getLogger(__name__)
        >>>
        >>> def log(arg):
        >>>     logger.info('progress=%f', arg)
        >>>
        >>> p = ProgressHelper(func=log)
        >>> p1, p2, p3 = p.split([1, 3, 1])
        >>>
        >>> # do initialize process
        >>> p1.done()  # => 'progress=20.0'
        >>>
        >>> # do main process
        >>> for task, sub_p2 in p2.seq(['a', 'b', 'c']):  # => 'progress=40.0', 60.0, and 80.0
        >>>     logger.info('doing task %s', task)
        >>>
        >>> # do terminate process
        >>> p3.done()  # => 'progress=100.0'
    """

    __slots__ = ['_min', '_max', '_rate', '_func']

    @classmethod
    def null(cls):
        """何もしない ``ProgressHelper`` インスタンスを生成する。
        """
        return cls(func=None)

    @classmethod
    def dumb(cls, dest=sys.stdout):
        """:func:`print` するだけの ``ProgressHelper`` インスタンスを生成する。

        Args:
            dest: 出力先（デフォルト＝標準出力）
        """
        return cls(func=lambda *a, **kw: print(a, kw, file=dest))

    # noinspection PyShadowingBuiltins
    def __init__(self, min: float = 0, max: float = 100, func: Optional[Callable] = None):
        """
        Args:
            min: プログレス範囲始端（進捗率0.0に対応する位置、デフォルト＝0）
            max: プログレス範囲終端（進捗率1.0に対応する位置、デフォルト＝100）
            func: 通知関数（デフォルト＝無し）
        """
        assert min < max
        self._min = min
        self._max = max
        self._func = func
        self._rate = 0.0

    def __str__(self):
        return 'Progress(min={},max={},rate={},func={})'.format(self._min, self._max, self._rate, self._func)

    def _pos(self, rate: float) -> float:
        assert 0.0 <= rate <= 1.0
        return (self._max - self._min) * rate + self._min

    def _notify(self, rate: float, *args, **kwargs):
        if callable(self._func):
            self._func(self._pos(rate), *args, **kwargs)

    def set(self, rate: float, *args, **kwargs):
        # noinspection PyUnresolvedReferences
        """進捗率を通知する。

        *rate=0.0* は開始を意味し、*rate=1.0* は終了を意味する。

        「任意の引数」は ``ProgressHelper`` としては意味を持たない。
        通知関数呼び出し時の引数として適用される。

        Args:
            rate: 進捗率（0.0～1.0）
            *args: 任意の引数
            **kwargs: 任意の引数

        Examples:
            >>> def foo(arg):
            >>>    print(arg)
            >>>
            >>> p = ProgressHelper(min=-100, max=-100, func=foo)
            >>> p.set(0.0)  # => invoke foo(-100.0)
            >>> p.set(0.5)  # => invoke foo(0.0)
            >>> p.set(1.0)  # => invoke foo(100.0)

        Examples:

            * 「任意の引数」を使った場合

            >>> def foo(*args, **kwargs):
            >>>    print(args, kwargs)
            >>>
            >>> p = ProgressHelper(func=foo)
            >>> p.set(0.5, 123, x=456)  # => invoke foo(50.0, 123, x=456)
        """
        assert 0.0 <= rate <= 1.0
        self._rate = rate
        self._notify(self._rate, *args, **kwargs)

    def done(self, *args, **kwargs):
        """進捗率100%を通知する。

        ``set(1.0)`` と同じ。
        """
        self.set(1.0, *args, **kwargs)

    def sub(self, low: float, high: float) -> "ProgressHelper":
        # noinspection PyUnresolvedReferences
        """部分の進捗を管理する :class:`ProgressHelper` インスタンスを生成する。

        現在の範囲から、指定範囲を切り出す。

        Args:
            low: 範囲前端（0.0～1.0）
            high: 範囲後端（0.0～1.0）

        Examples:
            >>> def other_task(progress):
            >>>     progress.set(0.0)  # => invoke foo(25.0)
            >>>     progress.set(0.5)  # => invoke foo(50.0)
            >>>     progress.done()  # => invoke foo(75.0)
            >>>
            >>> def foo(arg):
            >>>     print(arg)
            >>>
            >>> p = ProgressHelper(func=foo)
            >>> p.set(0.0)
            >>> other_task(progress=p.sub(0.25, 0.75))

        Returns:
            指定範囲の進捗を管理する ``ProgressHelper`` インスタンス
        """
        assert 0.0 <= low < high <= 1.0
        return ProgressHelper(min=self._pos(low), max=self._pos(high), func=self._func)

    def split(self, v: Union[int, List, Tuple]) -> Iterator["ProgressHelper"]:
        # noinspection PyUnresolvedReferences
        """部分の進捗を管理する :class:`ProgressHelper` インスタンスを生成する。

        現在の範囲を、指定個数に分割する。

        Args:
            v: 分割個数、または割合の配列

        Examples:

            * 分割個数指定

            >>> def foo(arg):
            >>>     print(arg)
            >>>
            >>> progress = ProgressHelper(func=foo)
            >>>
            >>> p1, p2, p3 = progress.split(3)
            >>> p1.done()  # => invoke foo(33.33333333333333)
            >>> p2.done()  # => invoke foo(66.66666666666666)
            >>> p3.done()  # => invoke foo(100.0)

        Examples:

            * 割合指定

            >>> def foo(arg):
            >>>     print(arg)
            >>>
            >>> progress = ProgressHelper(func=foo)
            >>>
            >>> p1, p2, p3 = progress.split([1, 3, 1])
            >>> p1.done()  # => invoke foo(20.0)
            >>> p2.done()  # => invoke foo(80.0)
            >>> p3.done()  # => invoke foo(100.0)
        """
        if not isinstance(v, (list, tuple)):
            if v == 1:
                return iter([self])
            return self.split([1] * v)

        total = sum(v)
        b = [n/total for n in accumulate(v)]
        a = [0.0] + b[:-1]
        return (self.sub(*r) for r in zip(a, b))

    def seq(self, seq: Iterable[T], *args, **kwargs) -> Generator[Tuple[T, "ProgressHelper"], None, None]:
        """繰り返し要素に対応した進捗を管理する :class:`ProgressHelper` インスタンスを生成する。

        Args:
            seq: 繰り返し要素（listやtupleやiteratorなど）

        Examples:

            * **【BAD】** ``seq()`` を使わない場合

            >>> progress = ProgressHelper()
            >>> tasks = ['A', 'B', 'C']
            >>>
            >>> for n, task in enumerate(tasks):
            >>>     print('task {} start', task)
            >>>     progress.set((n + 0.5) / len(tasks))  # 進捗率を計算する必要がある
            >>>     print('task {} end', task)
            >>>     progress.set((n + 1) / len(tasks))  # 繰り返し要素終端の進捗も、自身で設定する必要がある

        Examples:

            * **【GOOD】** ``seq()`` を使う場合

            >>> progress = ProgressHelper()
            >>> tasks = ['A', 'B', 'C']
            >>>
            >>> for task, p in progress.seq(tasks):
            >>>    print('task {} start', task)
            >>>    p.set(0.5)  # 繰り返し要素単位での進捗率を設定すれば良い
            >>>    print('task {} end', task)
            >>>    # p.done()  # ループの最後で、繰り返し要素単位に進捗率1.0が自動設定される
        """
        seq = list(seq)  # expand iterable to list
        for e, p in zip(seq, self.split(len(seq))):
            yield e, p
            p.done(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.done()
