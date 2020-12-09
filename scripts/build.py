#!/usr/bin/env python3

import os
import sys

from datetime import datetime
from misaka import HtmlRenderer, Markdown
from multiprocessing import Pool
from utils import ABS, MarkdownHeader, NULL_MARKDOWN_HEADER, parse_header, parse_post, READ, WRITE


# https://misaka.readthedocs.io/en/latest/ or https://docs.rs/hoedown/6.0.0/hoedown/
POST_RENDERER_FLAGS = [ ]
POST_RENDERER = HtmlRenderer(POST_RENDERER_FLAGS)

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
    'TITLE': 'TITLE',
    'CONTENT': 'PLACEHOLDER',
    'LIST_ITEM': 'LIST_ITEM',
    'POST_ID': 'SLUG',
    'POST_TITLE': 'TITLE',
    'POST_DYNAMIC_LINK': 'DYNAMIC_LINK',
    'POST_STATIC_LINK': 'STATIC_LINK',
    'POST_CONTENT': 'PLACEHOLDER',
    'POST_DATE': 'PUBLISH_DATE',
    'POST_EDIT_DATE': 'EDIT_DATE',
}

WORKERS=8
WORKER_CHUNKSIZE=1


def get_post_id(header):
    return header.slug.lower().strip().replace(' ', '-')


def convert_md(layout_fpath, src_fpath, dst_fpath):
    layout = READ(layout_fpath)

    (header, contents) = parse_post(src_fpath)

    dynamic_link = f'/posts.html#{get_post_id(header)}'
    static_link = f'/posts/{get_post_id(header)}.html'

    out = layout.\
        replace(PLACEHOLDERS['POST_ID'], get_post_id(header)).\
        replace(PLACEHOLDERS['POST_TITLE'], header.title).\
        replace(PLACEHOLDERS['POST_DYNAMIC_LINK'], dynamic_link).\
        replace(PLACEHOLDERS['POST_STATIC_LINK'], static_link).\
        replace(PLACEHOLDERS['POST_CONTENT'], POST_PARSER(contents)).\
        replace(PLACEHOLDERS['POST_DATE'], str(header.date)).\
        replace(PLACEHOLDERS['POST_EDIT_DATE'], str(header.edit))

    WRITE(dst_fpath, out)


def template(layout_fpath, placeholder_map, src_fpath, dst_fpath):
    layout = READ(layout_fpath)
    src = READ(src_fpath)

    out = layout.replace(PLACEHOLDERS['CONTENT'], src)

    for key, value in placeholder_map.items():
        out = out.replace(PLACEHOLDERS[key], value)

    WRITE(dst_fpath, out)


def template_list(src_fpath, item_src_fpaths, dst_fpath):
    src = READ(src_fpath)
    ITEM_PLACEHOLDER = PLACEHOLDERS['LIST_ITEM']

    for item_src_fpath in item_src_fpaths:
        item_src = READ(item_src_fpath)

        src = src.replace(
            ITEM_PLACEHOLDER, item_src + f'\n{ITEM_PLACEHOLDER}')

    out = src.replace(ITEM_PLACEHOLDER, '')

    WRITE(dst_fpath, out)


def process_post(packed_args):
    post_name, layout, post_dir, post_layout, tmp_dir, out_dir = packed_args
    post_fpath = ABS(post_dir, post_name)

    (header, _) = parse_post(post_fpath)

    if header == NULL_MARKDOWN_HEADER:
        return None
    
    slug = get_post_id(header) + '.html'
    mapped_slug = f'posts/{slug}'

    convert_md(post_layout, post_fpath, ABS(tmp_dir, mapped_slug))
    template(layout, {'TITLE': header.title},
            ABS(tmp_dir, mapped_slug),
            ABS(out_dir, mapped_slug))

    return (ABS(tmp_dir, mapped_slug), header.date)


if __name__ == '__main__':
    args, expected = sys.argv, 7

    if '-h' not in args and len(args) == expected:
        html_dir, layout, post_dir, post_layout, tmp_dir, out_dir = (*args[1:expected],)

        template(layout, {'TITLE': 'Index'},
                ABS(html_dir, 'index.html'),
                ABS(out_dir, 'index.html'))

        template(layout, {'TITLE': 'Post Index'},
                ABS(html_dir, 'posts.html'),
                ABS(tmp_dir, 'posts.html'))

        with Pool(WORKERS) as pool:
            def work(layout, post_dir, post_layout, tmp_dir, out_dir):
                for post_name in os.listdir(post_dir):
                    if os.path.isfile(os.path.join(post_dir, post_name)):
                        yield (post_name, layout, post_dir, post_layout, tmp_dir, out_dir)

            raw_posts = work(layout, post_dir, post_layout, tmp_dir, out_dir)

            all_posts = [t for t in pool.imap(process_post, raw_posts, WORKER_CHUNKSIZE) if t is not None]
            all_posts.sort(key=lambda t: t[1], reverse=True)

            template_list(
                    ABS(tmp_dir, 'posts.html'),
                    (slug for slug, date in all_posts),
                    ABS(out_dir, 'posts.html'))
    else:
        print(f'Usage: {__file__} <html_dir> <layout_html> <post_dir> <post_layout_html> <tmp_dir> <out_dir>')
        print(f'\t-h : Display this help information')

