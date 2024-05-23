import spacy


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
