#!/usr/bin/env python3

import os
import sys

from datetime import datetime
from misaka import HtmlRenderer, Markdown
from multiprocessing import Pool
from utils import ABS, has_extension, MarkdownHeader, NULL_MARKDOWN_HEADER, parse_header, parse_post, READ, WRITE


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
    'POST_INDEX_NEXT': 'NEXT_YEAR',
    'POST_INDEX_PREV': 'PREV_YEAR',
}

WORKERS=8
WORKER_CHUNKSIZE=1


def convert_md(layout_fpath, src_fpath, index, dst_fpath):
    layout = READ(layout_fpath)

    (header, contents) = parse_post(src_fpath)

    dynamic_link = f'/{index}#{header.id}'
    static_link = f'/posts/{header.id}.html'

    out = layout.\
        replace(PLACEHOLDERS['POST_ID'], header.id).\
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
        out = out.replace(PLACEHOLDERS[key], str(value))

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


def create_post_index(layout_fpath, src_fpath, prev_index, year, next_index, post_fpaths, dst_fpath):
    placeholder_map = {
            'TITLE': f'Post Index ({year})',
            'POST_INDEX_PREV': prev_index if prev_index else '#',
            'POST_INDEX_NEXT': next_index if next_index else '#',
    }

    template(layout_fpath, placeholder_map,
            src_fpath, ABS(tmp_dir, f'{year}.html'))

    template_list(
            ABS(tmp_dir, f'{year}.html'),
            post_fpaths,
            dst_fpath)


def process_post(packed_args):
    post_fpath, layout, post_layout, tmp_dir, out_dir = packed_args

    (header, _) = parse_post(post_fpath)

    if header == NULL_MARKDOWN_HEADER:
        return None
    
    post_path = f'posts/{header.id}.html'

    current_year = datetime.now().year
    index = 'posts.html' if current_year == header.date.year else f'{header.date.year}.html'

    convert_md(post_layout, post_fpath, index, ABS(tmp_dir, post_path))
    template(layout, {'TITLE': header.title},
            ABS(tmp_dir, post_path),
            ABS(out_dir, post_path))

    return (ABS(tmp_dir, post_path), header.date)


if __name__ == '__main__':
    args, expected = sys.argv, 6

    if '-h' in args or len(args) != expected:
        print(f'Usage: {__file__} <html_dir> <layout_dir> <post_dir> <tmp_dir> <out_dir>')
        print(f'\t-h : Display this help information')

    html_dir, layout_dir, post_dir, tmp_dir, out_dir = (*args[1:expected],)

    page_layout = ABS(layout_dir, '_Layout.html')
    post_layout = ABS(layout_dir, '_PostLayout.html')
    post_index_layout = ABS(layout_dir, '_PostIndexLayout.html')

    template(page_layout, {'TITLE': 'Index'},
            ABS(html_dir, 'index.html'),
            ABS(out_dir, 'index.html'))

    with Pool(WORKERS) as pool:
        def get_posts(post_dir):
            for post_name in os.listdir(post_dir):
                if os.path.isfile(os.path.join(post_dir, post_name)) and has_extension(post_name, 'md'):
                    yield os.path.join(post_dir, post_name), page_layout, post_layout, tmp_dir, out_dir

        ## find all markdown posts and convert them to html
        all_posts = [t for t in pool.imap(process_post, get_posts(post_dir), WORKER_CHUNKSIZE) if t is not None]
        
        ## sort posts by date, from most recent to oldest
        all_posts.sort(key=lambda t: t[1], reverse=True)

        ## collect posts made in separate years into separate buckets
        years = {}
        for post_fpath, publish_date in all_posts:
            if publish_date.year not in years:
                years[publish_date.year] = [post_fpath]
            else:
                years[publish_date.year].append(post_fpath)

        ## create a new index page for each year, and template it with posts
        indices = list(years.items())

        ## create the default (latest) post index
        previous_index = f'{indices[1][0]}.html' if len(indices) - 1 else None
        create_post_index(page_layout,
                post_index_layout,
                previous_index, indices[0][0], None,
                indices[0][1],
                ABS(out_dir, 'posts.html'))

        ## create the remaining post indices and link them together
        for idx, (year, post_fpaths) in enumerate(indices[1:]):
            current_index = f'{year}.html'

            ## indices are in reverse chronological order (newest first)
            previous_index = f'{indices[idx+1][0]}.html' if idx < len(indices) - 1 else None
            next_index = f'{indices[idx-1][0]}.html' if idx > 0 else 'posts.html'

            create_post_index(page_layout,
                    post_index_layout,
                    previous_index, year, next_index,
                    post_fpaths,
                    ABS(out_dir, current_index))

