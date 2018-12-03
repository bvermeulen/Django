import markdown
from utils.mdx_del_ins import DelInsExtension
from django.utils.html import mark_safe


def get_markdown_text(text):
    markdown_text = mark_safe(markdown.markdown(text, extensions = ['tables', 'fenced_code', DelInsExtension()], safe_mode='escape'))
    return markdown_text


text = \
'''
# H1
## H2
### H3
#### H4
##### H5
###### H6

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------

2^10^ is 1024.

Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Underline ++uses++ two ++ and two tildes ~~Scratch this.~~

| First Header  | Second Header |
| ------------- | ------------- |
| Content Cell  | Content Cell  |
| Content Cell  | Content Cell  |

This is a paragraph introducing:

~~~~~~~~~~~~~~~~~~~~~
a one-line code block
~~~~~~~~~~~~~~~~~~~~~


~~~{.python}
with open('try_this.html', 'tw') as html_object:
    html_text = '<html>'
    html_text += get_markdown_text(text)
    html_text += '</html>'
    print(html_text)
    html_object.write(html_text)
~~~
'''

with open('try_this.html', 'tw') as html_object:
    html_text = '<html>\n'
    html_text += get_markdown_text(text)
    html_text += '\n</html>\n'
    print(html_text)
    html_object.write(html_text)
