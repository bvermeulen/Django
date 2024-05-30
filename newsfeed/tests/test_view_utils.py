from django.test import TestCase
from howdimain.howdimain_vars import IMG_WIDTH_PERC
from ..views.views_utils import add_img_tag_adjust_width


class TestUtils(TestCase):

    def test_add_width_to_img_tag(self):
        self.maxDiff = None

        url_big_picture = (
            "https://a.espncdn.com/photo/2024/0528/r1338674_1296x729_16-9.jpg"
        )
        url_small_picture = 'https://i.imgur.com/rK5t5LP.png'

        # test big picture with style
        a = (
            f'123 <img style="color: red" src="{url_big_picture}" '
            f'something more >'
        )

        new_a = add_img_tag_adjust_width(a, None)
        self.assertEqual(new_a, (
            f'123 <img style="width: {IMG_WIDTH_PERC}; color: red" '
            f'src="{url_big_picture}" something more >'
        ))

        # test big picture without style
        a = (
            f'<img src="{url_big_picture}" '
            f'something more >'
        )

        new_a = add_img_tag_adjust_width(a, None)
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

        new_a = add_img_tag_adjust_width(a, None)
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
            '123 <img style="color: red" src="hihaho.jpg" '
            'something more >'
        )

        new_a = add_img_tag_adjust_width(a, None)
        self.assertEqual(new_a, a)

        # test total goobly cook
        a = (
            '123 <img src="hihaho.jpg" abcdefge 456 @@!! and '
            'something more '
        )

        new_a = add_img_tag_adjust_width(a, None)
        self.assertEqual(new_a, a)
