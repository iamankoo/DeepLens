from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.sentence_segmenter import sentence_segmenter

text = content_extractor.extract(
    "https://www.ibm.com/think/topics/langgraph"
)

text = document_normalizer.normalize(text)

sentences = sentence_segmenter.segment(text)

print("Sentences:", len(sentences))
print()

for i in range(5):
    print(f"{i+1}. {sentences[i]}")
    print()