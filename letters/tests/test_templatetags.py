from django.core.paginator import Paginator
from django.test import TestCase

from letters.templatetags.utils_tags import get_proper_elided_page_range


class GetProperElidedPageRangeTestCase(TestCase):
    """
    get_proper_elided_page_range() should return get_elided_page_range(number, on_each_side, on_ends) for paginator
    """

    def test_get_proper_elided_page_range(self):
        paginator = Paginator(object_list=['x' for i in range(15)], per_page=1)
        # get_proper_elided_page_range() returns a generator object, so make it a list here
        elided_page_range = list(get_proper_elided_page_range(paginator, 8, on_each_side=3, on_ends=2))

        # If there are 15 pages and the current page number is 8, the first 2 and last 2 page numbers (1-2 and 14-15),
        # and page numbers within 3 pages of current page (5-7 and 9-11) should be listed in the elided page range
        # All other pages (3-4 and 12-13) should not be listed, and there should be 2 "..."
        for page_number in [1, 2, 5, 6, 7, 9, 10, 11, 14, 15]:
            self.assertIn(page_number, elided_page_range, 'Page {} should be in elided page range'.format(page_number))

        for page_number in [3, 4, 12, 13]:
            self.assertNotIn(page_number, elided_page_range,
                             'Page {} should not be in elided page range'.format(page_number))

        self.assertEqual(elided_page_range.count(str(Paginator.ELLIPSIS)), 2)
