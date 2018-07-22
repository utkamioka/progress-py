from unittest import TestCase
from src import ProgressHelper


class TestProgressHelper(TestCase):

    def test_construct(self):
        with self.assertRaises(AssertionError):
            ProgressHelper(10, 10)

        with self.assertRaises(AssertionError):
            ProgressHelper(100, 0)

        p = ProgressHelper(-100, 100)
        self.assertEqual(p.min, -100)
        self.assertEqual(p.max, 100)
        self.assertEqual(p.rate, 0.0)

    def test_set(self):
        pool = []

        def f(rate, *args, **kwargs):
            pool.append((rate, args, kwargs))

        p = ProgressHelper(-100, 100, func=f)
        p.set(0)
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool.pop(), (-100, tuple(), dict()))

        p.set(0.5, 'a', msg='alpha')
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool.pop(), (0.0, ('a',), {'msg': 'alpha'}))

        p.done('b', msg='bravo')
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool.pop(), (100.0, ('b',), {'msg': 'bravo'}))

    def test_seq(self):
        pool = []

        def f(rate, *args, **kwargs):
            pool.append((rate, args, kwargs))

        p = ProgressHelper(-100, 100, func=f)

        for n in p.seq(range(4), 'c', msg='charlie'):
            pool.append(n)

        self.assertEqual(len(pool), 8)
        self.assertEqual(pool.pop(0), 0)
        self.assertEqual(pool.pop(0), (-50.0, ('c',), {'msg': 'charlie'}))
        self.assertEqual(pool.pop(0), 1)
        self.assertEqual(pool.pop(0), (0.0, ('c',), {'msg': 'charlie'}))
        self.assertEqual(pool.pop(0), 2)
        self.assertEqual(pool.pop(0), (50.0, ('c',), {'msg': 'charlie'}))
        self.assertEqual(pool.pop(0), 3)
        self.assertEqual(pool.pop(0), (100.0, ('c',), {'msg': 'charlie'}))
