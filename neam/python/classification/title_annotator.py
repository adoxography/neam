import os
import pickle
import random
import re
from neam.python.classification.processing import NEAMProcessor
from nltk import MaxentClassifier, word_tokenize, pos_tag
from nltk.classify import accuracy
from bs4 import BeautifulSoup, NavigableString

class TitleAnnotator(NEAMProcessor):
    _DEFAULT_MODEL = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'title_tag_model.pickle')
    _TAG_PATTERN = re.compile('<[^>]+>')

    def __init__(self, model=_DEFAULT_MODEL, inside='I', outside='O'):
        self._classifier = TitleClassifier(model)
        self._inside = inside
        self._outside = outside
        super().__init__(BeautifulSoup, BeautifulSoup)

    def run(self, soup):
        builder = []
        last_tag = self._outside
        text = str(soup.body.string)
        soup.body.clear()
        #soup.body.new_tag('a')

        for line in text.split('\n'):
            curr_tag = self._classifier.classify(self._remove_tags(line))
            if last_tag == self._outside and curr_tag == self._inside:
                soup.body.append(NavigableString('\n'.join(builder)))
                builder = []
            elif last_tag == self._inside and curr_tag == self._outside:
                tag = soup.new_tag('title')
                soup.body.append(tag)
                tag.string = '\n'.join(builder)
                builder = []
            builder.append(line)
            last_tag = curr_tag

        if last_tag == self._inside:
            tag = soup.new_tag('title')
            soup.body.append(tag)
            tag.string = '\n'.join(builder)
        else:
            soup.body.append(NavigableString('\n'.join(builder)))

        return soup

    def _remove_tags(self, line):
        return self._TAG_PATTERN.sub('', line)


class TitleClassifier:
    def __init__(self, model):
        if isinstance(model, MaxentClassifier):
            self._classifier = model
        else:
            with open(model, 'rb') as pickle_file:
                self._classifier = pickle.load(pickle_file)

        self.clear()

    def clear(self):
        self._prevTag = 'O'
        self._prev2Tag = 'O'

    def classify(self, line, clear=False):
        if clear:
            self.clear()

        features = extract(line)
        features['prevTag'] = self._prevTag
        features['prev2Tag'] = self._prev2Tag

        tag = self._classifier.classify(features)
        self._prev2Tag = self._prevTag
        self._prevTag = tag

        return tag

    @staticmethod
    def train(file_name, max_iter=20, train_ratio=1.0, dump=None):
        data = []
        with open(file_name) as input_file:
            for item in input_file:
                label, line = item.split('%%%')
                features = extract(line)

                features['prevTag'] = data[-1][1] if len(data) > 0 else 'O'
                features['prev2Tag'] = data[-2][1] if len(data) > 1 else 'O'

                data.append((features, label))

        random.shuffle(data)
        threshold = int(len(data) * train_ratio)
        train, text = [data[:threshold], data[threshold:]]

        classifier = MaxentClassifier.train(train, max_iter=max_iter)

        if train_ratio < 1:
            print(accuracy(classifier, test))

        if dump:
            with open(dump, 'wb') as model_file:
                pickle.dump(classifier, model_file)

        return TitleClassifier(classifier)


def extract(line):
    tokens = word_tokenize(line)
    penn_tags = []
    univ_tags = []

    if tokens:
        penn_tagged = pos_tag(tokens)
        univ_tagged = pos_tag(tokens, tagset='universal')

        _, penn_tags = zip(*penn_tagged)
        _, univ_tags = zip(*univ_tagged)

    features = {'numTokens': len(tokens)}

    for token in set(tokens):
        features["token({})".format(token)] = 1

    for tag in set(penn_tags + univ_tags):
        features["tags({})".format(tag)] = 1

    return features

