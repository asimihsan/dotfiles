from inscriptis import get_annotated_text, ParserConfig
import spacy
from intervaltree import IntervalTree
import numpy as np


def bytes_to_numpy_array(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


class HTMLToText:
    def __init__(self, model_name="en_core_web_trf"):
        self.spacy_model = SpacyModel(model_name)

    def html_to_sentences(self, html: str) -> list[str]:
        annotation_rules = {"pre": ["pre"]}
        config = ParserConfig(annotation_rules=annotation_rules)
        annotated_text = get_annotated_text(html, config)
        text = annotated_text["text"]

        annotations = annotated_text["label"]
        pre_intervals = self.build_interval_tree(annotations)

        doc = self.spacy_model.process_text(text)
        sentences = self.merge_sentences_with_pre(doc, pre_intervals)

        return sentences

    def build_interval_tree(self, annotations) -> IntervalTree:
        tree = IntervalTree()
        for start, end, label in annotations:
            if label == "pre":
                tree[start:end] = label
        return tree

    def merge_sentences_with_pre(self, doc, pre_intervals) -> list[str]:
        sentences = []
        current_sentence = []

        sents = (sent for sent in doc.sents if len(sent.text.strip()) > 0)

        for sent in sents:
            if not pre_intervals.overlaps(sent.start_char, sent.end_char):
                if current_sentence:
                    sentences.append(" ".join(current_sentence))
                    current_sentence = []

                sentences.append(sent.text.strip())
                continue

            current_sentence.append(sent.text.strip())

        if current_sentence:
            sentences.append(" ".join(current_sentence))

        return sentences


class SpacyModel:
    def __init__(self, model_name="en_core_web_trf"):
        self.model_name = model_name
        self.nlp = None
        self.load_model()

    def load_model(self):
        if self.nlp is None:
            self.nlp = spacy.load(self.model_name)
        return self.nlp

    def process_text(self, text):
        nlp = self.load_model()
        return nlp(text)
