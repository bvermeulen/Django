import re
import html

def convert_string_to_html(a_string):
    return html.escape(a_string, quote=True)

    # return re.sub(r'&#(x[\dA-F]+);',
    #               lambda m: '&#' + str(int('0' + m.group(1), 16)) + ';',
    #               html.escape(a_string, quote=True))