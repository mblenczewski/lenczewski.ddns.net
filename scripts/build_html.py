#!/usr/bin/env python3

from misaka import HtmlRenderer, Markdown
from datetime import datetime
from pprint import pprint

import os


ROOT = os.path.abspath('./')


def HTML(path): return os.path.abspath(ROOT + f'/html/{path}')
def CSS(path): return os.path.abspath(ROOT + f'/css/{path}')
def MD(path): return os.path.abspath(ROOT + f'/posts/{path}')
def TMP(path): return os.path.abspath(ROOT + f'/tmp/{path}')
def OUT(path): return os.path.abspath(ROOT + f'/out/{path}')


HTML_LAYOUT_BASE = HTML('_Layout.html')

POST_METADATA_SEPARATOR = '---'


class MarkdownHeader:
    def __init__(self, slug: str, title: str, **kwargs):
        self.slug = slug
        self.title = title
        now = datetime.now()
        self.date = kwargs.get('date', f'{now.day}-{now.month}-{now.year}')
        self.edit = kwargs.get('edit', self.date)


NULL_MARKDOWN_HEADER = MarkdownHeader('', '')

POST_RENDERER = HtmlRenderer()
# https://misaka.readthedocs.io/en/latest/#extensions or https://docs.rs/hoedown/6.0.0/hoedown/
POST_PARSER_EXTENSIONS = [
    'autolink',
    'fenced-code',
    'footnotes',
    'highlight',
    'no-intra-emphasis',
    'quote',
    'space-headers',
    'strikethrough',
    'superscript',
    'tables'
]
POST_PARSER = Markdown(POST_RENDERER, POST_PARSER_EXTENSIONS)
PLACEHOLDERS = {
    'TITLE': '{{TITLE_PLACEHOLDER}}',
    'CONTENT': '{{CONTENT_PLACEHOLDER}}',
    'LIST_ITEM': '{{LIST_ITEM_PLACEHOLDER}}',
    'POST_ID': '{{POST_ID_PLACEHOLDER}}',
    'POST_TITLE': '{{POST_TITLE_PLACEHOLDER}}',
    'POST_DYNAMIC_LINK': '{{POST_DYNAMIC_LINK_PLACEHOLDER}}',
    'POST_STATIC_LINK': '{{POST_STATIC_LINK_PLACEHOLDER}}',
    'POST_CONTENT': '{{POST_CONTENT_PLACEHOLDER}}',
    'POST_DATE': '{{POST_DATE_PLACEHOLDER}}',
    'POST_EDIT_DATE': '{{POST_EDIT_DATE_PLACEHOLDER}}',
}


def get_post_id(post_header: MarkdownHeader):
    return post_header.slug.lower().strip().replace(' ', '-')


def post_layout_binder(layout_contents: str, header: MarkdownHeader, contents: str):
    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_ID'], get_post_id(header))

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_TITLE'], header.title)

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_DYNAMIC_LINK'], f'/posts.html#{get_post_id(header)}')

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_STATIC_LINK'], f'/posts/{get_post_id(header)}.html')

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_CONTENT'], POST_PARSER(contents))

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_DATE'], header.date)

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_EDIT_DATE'], header.edit)

    return layout_contents


def parse_post(path) -> (MarkdownHeader, str):
    def parse_header(file, header_separator) -> MarkdownHeader:
        def hit_metadata_separator(line, separator) -> bool:
            return line[:len(separator)] == separator

        if not hit_metadata_separator(file.readline(), header_separator):
            print(f'Metadata for post at {path} lacks beginning separator ({header_separator})! Skipping file')
            return NULL_MARKDOWN_HEADER

        header = {}
        header['slug'] = path[path.rfind('/')+1:path.rfind('.')]
        try:
            while True:
                line = file.readline()

                if hit_metadata_separator(line, header_separator):
                    break
                else:
                    (arg, value) = line.split(':')
                    header[arg] = value

            return MarkdownHeader(**header)

        except (TypeError, KeyError) as err:
            print(f'Metadata for post at {path} lacks certain fields! Check spelling? Skipping file')
            return NULL_MARKDOWN_HEADER

    with open(path) as file:
        header = parse_header(file, POST_METADATA_SEPARATOR)

        contents = file.readlines()

        return (header, ''.join(contents))


def write_md_file(layout_file, layout_binder, src_file, dest_file):
    """
    layout_binder: labmda layout_contents, MarkdownHeader, src_contents: return mapped_layout_contents
    """
    layout = ''
    with open(layout_file) as file:
        layout = ''.join(file.readlines())

    (header, contents) = parse_post(src_file)

    out = layout_binder(layout, header, contents)

    with open(dest_file, mode='w') as file:
        file.write(out)


def write_html_file(layout_file, layout_placeholder_map, src_file, dest_file):
    layout = ''
    with open(layout_file) as file:
        layout = ''.join(file.readlines())

    src = ''
    with open(src_file) as file:
        src = ''.join(file.readlines())

    out = layout.replace(PLACEHOLDERS['CONTENT'], src)

    for key, value in layout_placeholder_map.items():
        out = out.replace(PLACEHOLDERS[key], value)

    with open(dest_file, mode='w') as file:
        file.write(out)


def write_html_files(layout_file, src_files, dest_file):
    layout = ''
    with open(layout_file) as file:
        layout = ''.join(file.readlines())

    for src_file in src_files:
        src = ''
        with open(src_file) as file:
            src = ''.join(file.readlines())

        layout = layout.replace(
            PLACEHOLDERS['LIST_ITEM'], src + f"\n{PLACEHOLDERS['LIST_ITEM']}")

    out = layout.replace(PLACEHOLDERS['LIST_ITEM'], '')

    with open(dest_file, mode='w') as file:
        file.write(out)


if __name__ == '__main__':
    write_html_file(HTML_LAYOUT_BASE, {'TITLE': 'Index'}, HTML(
        'index.html'), OUT('index.html'))

    write_html_file(HTML_LAYOUT_BASE, {'TITLE': 'Posts'}, HTML(
        'posts.html'), TMP('posts.html'))

    mapped_posts = {}  # Stores mapped posts and the date of their posting
    for post in [f for f in os.listdir(ROOT + '/posts/') if os.path.isfile(ROOT + '/posts/' + f)]:
        post = ROOT + '/posts/' + post
        (header, _) = parse_post(post)

        if header == NULL_MARKDOWN_HEADER:
            continue  ## ignore posts with corrupted headers
        
        mapped_post_name = get_post_id(header) + '.html'

        write_md_file(HTML('_PostLayout.html'), post_layout_binder,
                      post, TMP(f'posts/{mapped_post_name}'))

        mapped_posts[TMP(f'posts/{mapped_post_name}')] = header.date

        write_html_file(HTML('_Layout.html'), {'TITLE': header.title}, TMP(
            f'posts/{mapped_post_name}'), OUT(f'posts/{mapped_post_name}'))

    posts = list(mapped_posts.keys())
    posts.sort(key=lambda path: mapped_posts[path], reverse=True)

    write_html_files(TMP('posts.html'), posts, OUT('posts.html'))

