"""
processing.py

Defines processes that NEAM data can be run through, and a Pipeline class to
run them with. A processor should inherit from NEAMProcessor and adhere to its
contract. Once defined, add an instance of the processor to the a pipeline and
call the pipeline's *run* method. The pipeline will pipe the data given to
*run* through each process defined in the pipeline, in order.
"""
import re
from abc import ABC
from bs4 import BeautifulSoup
from neam.python.util import multi_sub

class NEAMProcessor(ABC):
    """
    Defines the interface for neam processes.

    A NEAMProcessor should implement a method called "run", which accepts an
    str and returns an str.
    """
    def run(self, text):
        raise NotImplemented


class Pipeline:
    """
    Stores a list of NEAMProcessor objects and passes data through them
    """
    def __init__(self, processes = None):
        """
        Initializes the Pipeline

        :param processes: The processes to use in the pipeline
        :type processes: list of NEAMProcessor or callable
        """
        self._processes = processes or []

    def run(self, data):
        """
        Consumes some data and passes it sequentially through each processor
        in the pipeline.

        Each processor receives as input the output of the previous processor.

        :param data: The data to pass into the first processor
        :return: The output from the final processor
        """
        for process in self._processes:
            process.run(data)
            try:
                data = process.run(data)
            except AttributeError:
                data = process(data)
        return data

    def add(self, process):
        """
        Adds a processor to the end of the pipeline

        :param process: The process to add
        :type process: NEAMProcessor or callable
        """
        self._processes.append(process)


class ASCIIifier(NEAMProcessor):
    """
    Replaces non-ascii characters with ascii equivalents
    """
    _CHARMAP = {
        "\u2018": "'",
        "\u2019": "'",
        "\ufeff": ""
    }

    def __init__(self, map = None):
        """
        Initializes the processor

        :param map: Correspondances between UTF-8 characters and ASCII
                    characters
        :type map: dict of str: str
        """
        self._map = map or self._CHARMAP

    def run(self, text):
        return multi_sub(self._map, text)


class PageReplacer(NEAMProcessor):
    """
    Replaces page numbers with the corresponding TEI tag
    """
    def run(self, text):
        return re.sub('page (\d+)', '<pb n="\g<1>"/>', text, flags=re.I)


class SicReplacer(NEAMProcessor):
    """
    Replaces [sic] items with the corresponding TEI tag
    """
    def run(self, text):
        return re.sub('\[sic; (\S+)\]', '<sic>\g<1></sic>', text)


class SpaceNormalizer(NEAMProcessor):
    """
    Normalizes spaces in XML text
    """
    def run(self, text):
        text = re.sub('\n', ' ', text)
        text = re.sub('(<[^/>]*>) +', '\g<1>', text)
        text = re.sub(' +(?=</)', '', text)
        return re.sub('(?<= ) ', '', text)


class PossessionFixer(NEAMProcessor):
    """
    Moves possession markers inside tags
    """
    def run(self, text):
        text =re.sub("(<[^/>]+>[^<]+)(<[^>]+>)'s", "\g<1>'s\g<2>", text)
        return re.sub("(?<!')(<[^/>]+>[^<]*s)(<[^>]+>)'", "\g<1>'\g<2>", text)


class TagExpander(NEAMProcessor):
    _SPACE_PATTERN = re.compile(' +')

    def __init__(self, tags, words):
        self._tags = tags
        self._words = words
        self._pattern = re.compile('((?:(?:{})\s+)+)<({})>'.format('|'.join(words), '|'.join(tags)), flags=re.I)

    def run(self, text):
        return self._pattern.sub(self._format, text)

    def _format(self, match_object):
        words = match_object.group(1).strip()
        tag = match_object.group(2)

        words = self._SPACE_PATTERN.sub(' ', words)

        return '<{}>{} '.format(tag, words)


class JournalShaper(NEAMProcessor):
    """
    Shapes journal text into TEI format by finding titles and paragraphs
    """
    _MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'oct', 'nov', 'dec']
    _ORDINALS = ['st', 'd', 'nd', 'rd', 'th']

    def __init__(self, author, year = 0, month = 1, day = 1):
        """
        Initializes the processor

        :param author: An ID for the author, to use in title tags
        :type author: str
        :param year: The year of the first entry
        :type year: int
        :param month: The 1-based integer corresponding to the month of the
                      first entry
        :type month: int
        :param day: The day of the first entry
        :type day: int
        """
        self._author = author
        self._year = year
        self._month = month
        self._day = day

    @property
    def formatted_year(self):
        """
        :return: The current year, as far as journal parsing is concerned
        :rtype: str
        """
        return str(self._year)

    @property
    def formatted_month(self):
        """
        :return: The current month, as far as journal parsing is concerned
        :rtype: str
        """
        return self._pad(self._month, 2)

    @property
    def formatted_day(self):
        """
        :return: The current day, as far as journal parsing is concerned
        :rtype: str
        """
        return self._pad(self._day, 2)

    def run(self, text):
        text = re.sub('(<title>)(.*?)(</title>)(.*?)(?=<title>)', self._format, text, flags=re.S)
        text = re.sub('(?<!<p>)(<title>)(.*?)(</title>)(.*?)$', self._format, text, flags=re.S)
        return '<body>' + text + '</body>'

    def _format(self, match_data):
        open_tag  = match_data.group(1)
        title     = match_data.group(2)
        close_tag = match_data.group(3)
        body      = match_data.group(4)

        code = self._make_code(re.search('({})(?:\.|[a-z]+)? +(\d+)(?:{})?\.?(?: +(\d+)\.?)?'.format('|'.join(self._MONTHS), '|'.join(self._ORDINALS)), title.lower()))

        return '<div xml:id="' + code + '" type="Entry"><p>' + open_tag + title + close_tag + '</p><p>' + body + '</p></div>'

    def _make_code(self, match_data):
        """
        Translates match data into a TEI title

        :param match_data: The result from a regular expression search
        """
        month = day = year = None

        if match_data:
            month = match_data.group(1)
            day   = match_data.group(2)
            year  = match_data.group(3)

        if day:
            day = int(day)
            if day < self._day:
                self._month += 1
            self._day = int(day)

        if month:
            month = self._MONTHS.index(month.lower()) + 1
            if month < self._month:
                self._year += 1
            self._month = month

        if year:
            self._year = int(year)

        return self._author + self.formatted_year + self.formatted_month + self.formatted_day

    def _tag_bodies(self, text):
        """
        Fills in the paragraphs based on the position of the titles

        :param text: The partially processed text
        :return: The text with bodies filled in
        """
        return re.sub('(</p><p>[\S\s]*?)(<div)', '\g<1></p></div>\g<2>', text)

    def _pad(self, n, size):
        """
        Adds 0s to the beginning of a number until the number is *size*
        characters long.

        :param n: The number to pad
        :param size: The size to pad until
        :return: The padded number
        :rtype: str
        """
        return '0' * (size - len(str(n))) + str(n)


class Beautifier(NEAMProcessor):
    """
    Adds indentation to XML text
    """
    def __init__(self, tab = '  ', parser = 'xml', ignore = None):
        """
        Initializes the processor

        :param tab: The string to use as a tab. Defaults to two spaces.
        :type tab: str
        :param parser: The parser BeautifulSoup should use to load the soup
        :type parser: str
        :ignore: The tags that should not be formatted. Defaults to P tags.
        :type ignore: list of str
        """
        self._tab = tab
        self._parser = parser
        self._ignore_tags = ignore or ['p']

    def run(self, text):
        soup = BeautifulSoup(text, self._parser).contents[0]
        return '\n'.join(self._beautify(soup, 0, []))

    def _beautify(self, soup, depth, builder):
        """
        Adds a BeautifulSoup tag to the builder recursively

        If the tag is in the IGNORE_TAGS list, it will be printed out without formatting.

        :param soup: A BeautifulSoup tag
        :param depth: The current indentation depth
        """
        indent = self._tab * depth

        if isinstance(soup, str) or soup.name in self._ignore_tags:
            builder.append(indent + str(soup))
        else:
            builder.append(indent + self._open_tag(soup))

            for child in soup.children:
                self._beautify(child, depth + 1, builder)

            builder.append(indent + self._close_tag(soup))

        return builder

    def _open_tag(self, tag):
        """
        Generates an opening tag string for a given tag

        :param tag: A BeautifulSoup tag
        :return: The string that would open the tag, including any attributes
        :rtype: str
        """
        attrs = ' '.join(['{}="{}"'.format(id, value) for id, value in tag.attrs.items()])
        if attrs:
            attrs = ' ' + attrs
        return '<{}{}>'.format(tag.name, attrs)

    def _close_tag(self, tag):
        """
        Generates a closing tag string for a given tag
        :param tag: A BeautifulSoup tag
        :return: The string that would close the tag
        :rtype: str
        """
        return '</{}>'.format(tag.name)


__all__ = ['ASCIIifier', 'PageReplacer', 'SicReplacer', 'SpaceNormalizer', 'JournalShaper', 'Beautifier', 'Pipeline', 'PossessionFixer', 'TagExpander']

