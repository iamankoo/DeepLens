import spacy

nlp = spacy.load("en_core_web_sm")


class SentenceSegmenter:

    def segment(
        self,
        text: str,
    ) -> list[str]:

        doc = nlp(text)

        return [
            sent.text.strip()
            for sent in doc.sents
            if sent.text.strip()
        ]


sentence_segmenter = SentenceSegmenter()