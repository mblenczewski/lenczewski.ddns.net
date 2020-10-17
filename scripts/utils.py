from datetime import datetime
from os.path import abspath

class MarkdownHeader:
    SEPARATOR='---'

    def __init__(self, slug: str, title: str, **kwargs):
        self.slug = slug
        self.title = title
        now = datetime.now()
        self.date = kwargs.get('date', f'{now.day}-{now.month}-{now.year}')
        self.edit = kwargs.get('edit', self.date)


NULL_MARKDOWN_HEADER = MarkdownHeader('', '')


def ABS(root, path):
    return abspath(root + path)


def READ(fpath):
    with open(fpath) as f:
        return ''.join(f.readlines())


def WRITE(fpath, contents):
    with open(fpath, mode='w') as f:
        f.write(contents)


def parse_header(fpath, f) -> MarkdownHeader:
    def hit_header_separator(line):
        return line[:len(MarkdownHeader.SEPARATOR)] == MarkdownHeader.SEPARATOR

    if not hit_header_separator(f.readline()):
        print(f'Post header at {fpath} lacks beginning separator! Skipping')
        return NULL_MARKDOWN_HEADER

    header = {}
    header['slug'] = fpath[fpath.rfind('/') + 1:fpath.rfind('.')]
    try:
        while True:
            line = f.readline()
            if hit_header_separator(line):
                break
            else:
                (arg, value) = line.split(':')
                header[arg] = value
        return MarkdownHeader(**header)

    except (TypeError, KeyError) as err:
        print(f'Post header at {fpath} is incomplete! Check spelling? Skipping')
        return NULL_MARKDOWN_HEADER


def parse_post(fpath) -> (MarkdownHeader, str):
    with open(fpath) as f:
        header = parse_header(fpath, f)
        contents = f.readlines()
        return (header, ''.join(contents))

