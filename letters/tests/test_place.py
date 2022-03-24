from django.test import TestCase

from letters.tests.factories import PlaceFactory


class PlaceTestCase(TestCase):
    """
    Test Place model
    """

    def test___str__(self):
        """
        Place.__str__() should return Place.name + state and country if filled
        """

        # Place with only name
        place = PlaceFactory(name='Barbecue')
        self.assertEqual(str(place), place.name, 'Place.__str__() should return Place.name if only name filled')

        # Place with name and state
        place = PlaceFactory(name='Barbecue', state='North Carolina')
        self.assertIn(place.name, str(place), 'Place.__str__() should contain name')
        self.assertIn(place.state, str(place), 'Place.__str__() should contain state if filled')

        # Place.__str__() should contain country if it's not DEFAULT_COUNTRY ("US")
        place.country = 'Spain'
        self.assertIn(place.country, str(place),
                      'Place.__str__() should contain country if filled and not DEFAULT_COUNTRY')

        # Place.__str__() shouldn't contain country if it's DEFAULT_COUNTRY ("US")
        place.country = 'US'
        self.assertNotIn(place.country, str(place),
                      "Place.__str__() shouldn't contain country if it's DEFAULT_COUNTRY")
