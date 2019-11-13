from django.test import TestCase
from howdimain.howdimain_vars import IMG_WIDTH_PERC
from ..views.views_utils import add_width_to_img_tag


class TestUtils(TestCase):

    def test_add_width_to_img_tag(self):
        self.maxDiff = None

        url_big_picture = 'https://i.imgur.com/p5KmtdF.jpg'
        url_small_picture = 'https://i.imgur.com/rK5t5LP.png'

        # test big picture with style
        a = (
            f'123 <img style="color: red" src="{url_big_picture}" '
            f'something more >'
        )

        new_a = add_width_to_img_tag(a)
        self.assertEqual(new_a, (
            f'123 <img style="width: {IMG_WIDTH_PERC}; color: red" '
            f'src="{url_big_picture}" something more >'
        ))

        new_a = add_width_to_img_tag(a)

        # test big picture without style
        a = (
            f'<img src="{url_big_picture}" '
            f'something more >'
        )

        new_a = add_width_to_img_tag(a)
        self.assertEqual(new_a, (
            f'<img style="width: {IMG_WIDTH_PERC}" '
            f'src="{url_big_picture}" something more >'
        ))

        # test big and small pictures combined
        a = (
            f'<img style="color: red" src="{url_big_picture}" alright> '
            f'something more and another tag '
            f'<img style="color: blue" src="{url_small_picture}"> and'
            f'basta and <img src="{url_big_picture}" again>'
        )

        new_a = add_width_to_img_tag(a)
        self.assertEqual(new_a, (
            f'<img style="width: {IMG_WIDTH_PERC}; color: red" '
            f'src="{url_big_picture}" alright> '
            f'something more and another tag '
            f'<img style="color: blue" src="{url_small_picture}"> and'
            f'basta and <img style="width: {IMG_WIDTH_PERC}" '
            f'src="{url_big_picture}" again>'
        ))

        # test non valid url
        a = (
            f'123 <img style="color: red" src="hihaho.jpg" '
            f'something more >'
        )

        new_a = add_width_to_img_tag(a)
        self.assertEqual(new_a, a)

        # test total goobly cook
        a = (
            f'123 <img src="hihaho.jpg" abcdefge 456 @@!! and '
            f'something more '
        )

        new_a = add_width_to_img_tag(a)
        self.assertEqual(new_a, a)
