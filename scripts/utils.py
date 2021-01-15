from datetime import date, datetime
from os.path import abspath


def unpack_date(packed):
    segments = [int(seg.strip()) for seg in packed.split('-')]
    unpacked = date(segments[0], segments[1], segments[2])
    return unpacked


class MarkdownHeader:
    SEPARATOR='---'

    def __init__(self, slug: str, title: str, **kwargs):
        self.slug = slug
        self.id = slug.lower().strip().replace(' ', '-')
        self.title = title
        now = datetime.now()
        date = kwargs.get('date', f'{now.year}-{now.month}-{now.day}')
        self.date = unpack_date(date)
        edit = kwargs.get('edit', date)
        self.edit = unpack_date(edit)


NULL_MARKDOWN_HEADER = MarkdownHeader('', '')


def ABS(root, path):
    return abspath(root + path)


def READ(fpath):
    with open(fpath) as f:
        return ''.join(f.readlines())


def WRITE(fpath, contents):
    with open(fpath, mode='w') as f:
        f.write(contents)


def has_extension(fpath, ext):
    return fpath.split('.')[-1] == ext


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

