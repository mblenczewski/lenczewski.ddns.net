#!/usr/bin/python3

from misaka import HtmlRenderer, Markdown
from pprint import pprint

import os

ROOT = os.path.abspath('./')


def HTML(path): return os.path.abspath(ROOT + f'/html/{path}')
def CSS(path): return os.path.abspath(ROOT + f'/styles/{path}')
def MD(path): return os.path.abspath(ROOT + f'/posts/{path}')
def TMP(path): return os.path.abspath(ROOT + f'/tmp/{path}')
def OUT(path): return os.path.abspath(ROOT + f'/out/{path}')


HTML_LAYOUT_BASE = HTML('_Layout.html')

POST_METADATA_SEPARATOR = '---'


class MarkdownHeader:
    def __init__(self, title: str, date: str):
        self.title = title
        self.date = date


NULL_MARKDOWN_HEADER = MarkdownHeader('', '')

POST_RENDERER = HtmlRenderer()
POST_PARSER = Markdown(POST_RENDERER)
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
}


def get_post_id(title: str):
    return title.lower().strip().replace(' ', '-')


def post_layout_binder(layout_contents: str, header: MarkdownHeader, contents: str):
    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_ID'], get_post_id(header.title))

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_TITLE'], header.title)

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_DYNAMIC_LINK'], f'/posts.html#{get_post_id(header.title)}')

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_STATIC_LINK'], f'/posts/{get_post_id(header.title)}.html')

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_CONTENT'], contents)

    layout_contents = layout_contents.replace(
        PLACEHOLDERS['POST_DATE'], header.date)

    return layout_contents


def parse_post(path) -> (MarkdownHeader, str):
    def parse_header(file, header_separator) -> MarkdownHeader:
        def hit_metadata_separator(line, separator) -> bool:
            return line[:len(separator)] == separator

        if not hit_metadata_separator(file.readline(), header_separator):
            print(
                f'Post at {path} lacks metadata separator ({header_separator}) on first line; skipping file!')
            return NULL_MARKDOWN_HEADER

        header = {}

        while True:
            line = file.readline()

            if hit_metadata_separator(line, header_separator):
                break
            else:
                (arg, value) = line.split(':')
                header[arg] = value

        if 'title' not in header or 'date' not in header:
            print(
                f'Could not find both \'title\' and \'date\' field in metadata for post at {path}. Check spelling?')

            return NULL_MARKDOWN_HEADER

        return MarkdownHeader(header['title'], header['date'])

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

    if not os.path.isdir(TMP('posts/')):
        os.mkdir(TMP('posts/'))

    if not os.path.isdir(OUT('posts/')):
        os.mkdir(OUT('posts/'))

    mapped_posts = []
    for post in [f for f in os.listdir(ROOT + '/posts/') if os.path.isfile(ROOT + '/posts/' + f)]:
        post = ROOT + '/posts/' + post
        (header, _) = parse_post(post)
        mapped_post_name = get_post_id(header.title) + '.html'

        write_md_file(HTML('_PostLayout.html'), post_layout_binder,
                      post, TMP(f'posts/{mapped_post_name}'))

        mapped_posts.append(TMP(f'posts/{mapped_post_name}'))

        write_html_file(HTML('_Layout.html'), {'TITLE': header.title}, TMP(
            f'posts/{mapped_post_name}'), OUT(f'posts/{mapped_post_name}'))

    write_html_files(TMP('posts.html'), mapped_posts, OUT('posts.html'))
