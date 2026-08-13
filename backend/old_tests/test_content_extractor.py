from app.search.content_extractor import (
    content_extractor,
)

text = content_extractor.extract(
    "https://www.ibm.com/think/topics/langgraph"
)

print(len(text))
print()
print(text[:1000])