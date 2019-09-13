# -*- coding: utf-8 -*-
'''Markdown Del_Ins Extension
    Extends the Python-Markdown library to support superscript text.
    Given the text:
        ~~hello~~
        ++goodbye++
    Will output:
        <del>hello</del> (Strikethrough)
        <ins>goodbye</ins> (underlined)
    :copyright: Copyright 2018 Bruno Vermeulen
    :license: MIT, see LICENSE for details.
    :use:
        from mxd_del_ins import DelInsExtension
        markdown_text = markdown.markdown(text, extensions = [DelInsExtension()])

'''
from markdown import Extension
from markdown.inlinepatterns import SimpleTagPattern

# match ^, at least one character that is not ^, and ^ again
DEL_RE = r"(\~\~)(.+?)(\~\~)"
INS_RE = r"(\+\+)(.+?)(\+\+)"


class DelInsExtension(Extension):
    '''Extension:
       text between ~~ characters will be deleted;
       text between ++ characters will be underlined;
    '''

    def extendMarkdown(self, md, md_globals):  # noqa: N802  #pylint: disable=arguments-differ
        """Insert 'del' pattern before 'not_strong' pattern."""
        md.inlinePatterns.add('del', SimpleTagPattern(DEL_RE, 'del'),
                              '<not_strong')

        md.inlinePatterns.add('ins', SimpleTagPattern(INS_RE, 'ins'),
                              '<not_strong')
