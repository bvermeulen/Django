from django.test import TestCase
from howdimain.howdimain_vars import IMG_WIDTH
from ..views.views_utils import add_width_to_img_tag


class TestUtils(TestCase):

    def test_add_width_to_img_tag(self):

        a = ('aaaa <img s> bbbb <img style="color: red"> cccc '
             '<img src="a.jpg&aa"> dddd <img >'
            )

        new_a = add_width_to_img_tag(a)

        self.assertEqual(new_a, (
            f'aaaa <img style="width: {IMG_WIDTH}" s> '
            f'bbbb <img style="width: {IMG_WIDTH}; color: '
            f'red"> cccc <img src="a.jpg&aa"> dddd <img style="width: {IMG_WIDTH}" >'
        ))
