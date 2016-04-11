import unittest

from vixen.vixen import Pager


class TestPager(unittest.TestCase):

    def test_next(self):
        # Given.
        p = Pager(limit=2)

        # When.
        p.data = list(range(10))

        # Then
        self.assertEqual(len(p.view), 2)
        self.assertEqual(p.total, 10)
        self.assertEqual(p.total_pages, 5)
        self.assertEqual(p.view, list(range(2)))
        self.assertEqual(p.selected, None)
        self.assertEqual(p.index, 0)

        # When.
        p.next()
        # Then.
        self.assertEqual(p.view, list(range(2)))
        self.assertEqual(p.index, 1)
        self.assertEqual(p.selected, None)

        # When.
        p.next(); p.next(); p.select()
        # Then.
        self.assertEqual(p.index, 3)
        self.assertEqual(p.view, list(range(2,4)))
        self.assertEqual(p.page, 2)
        self.assertEqual(p.selected, 3)

        # When.
        for i in range(8):
            p.next()
        p.select()
        # Then.
        self.assertEqual(p.index, 9)
        self.assertEqual(p.page, 5)
        self.assertEqual(p.view, list(range(8,10)))
        self.assertEqual(p.selected, 9)

        p.next()
        self.assertEqual(p.index, 9)


    def test_prev(self):
        # Given.
        p = Pager(limit=2)

        # When.
        p.data = list(range(10))
        p.prev()
        p.prev()

        # Then.
        self.assertEqual(p.index, 0)
        self.assertEqual(p.view, list(range(2)))
        self.assertEqual(p.selected, None)

        # When
        p.select()
        self.assertEqual(p.selected, 0)

        # When.
        for i in range(10):
            p.next()
        p.prev()
        p.select()

        # Then.
        self.assertEqual(p.index, 8)
        self.assertEqual(p.page, 5)
        self.assertEqual(p.view, list(range(8,10)))
        self.assertEqual(p.selected, 8)

    def test_next_page(self):
        # Given
        p = Pager(limit=2)

        # When.
        p.data = list(range(10))
        p.next_page()
        p.select(0)

        # Then
        self.assertEqual(p.start, 2)
        self.assertEqual(p.index, 2)
        self.assertEqual(p.view, list(range(2,4)))
        self.assertEqual(p.page, 2)
        self.assertEqual(p.selected, 2)

        # When.
        p.next_page()

        # Then
        self.assertEqual(p.start, 4)
        self.assertEqual(p.index, 4)
        self.assertEqual(p.view, list(range(4,6)))
        self.assertEqual(p.page, 3)
        self.assertEqual(p.selected, 2)

    def test_prev_page(self):
        # Given
        p = Pager(limit=2)

        # When.
        p.data = list(range(10))
        p.prev_page()
        p.select(0)

        # Then
        self.assertEqual(p.start, 0)
        self.assertEqual(p.index, 0)
        self.assertEqual(p.view, list(range(2)))
        self.assertEqual(p.page, 1)
        self.assertEqual(p.selected, 0)

        # When.
        for i in range(4):
            p.next_page()
        p.prev_page()
        p.select(0)

        # Then
        self.assertEqual(p.start, 6)
        self.assertEqual(p.index, 6)
        self.assertEqual(p.view, list(range(6,8)))
        self.assertEqual(p.page, 4)
        self.assertEqual(p.selected, 6)

    def test_odd_size(self):
        # Given
        p = Pager(limit=2)

        # When.
        p.data = list(range(11))
        p.next_page()
        # Then.
        self.assertEqual(p.total, 11)
        self.assertEqual(p.total_pages, 6)
        self.assertEqual(p.index, 2)
        self.assertEqual(p.view, list(range(2,4)))
        self.assertEqual(p.page, 2)
        self.assertEqual(p.selected, None)

        # When
        p.select(0)
        # Then
        self.assertEqual(p.index, 2)
        self.assertEqual(p.view, list(range(2,4)))
        self.assertEqual(p.page, 2)
        self.assertEqual(p.selected, 2)

    def test_when_data_is_empty(self):
        # Given
        p = Pager(limit=2)
        # When.
        p.data = list()
        # Then.
        self.assertEqual(p.selected, None)
        self.assertEqual(p.index, -1)
        self.assertEqual(p.total, 0)
        self.assertEqual(p.total_pages, 1)


if __name__ == '__main__':
    unittest.main()
