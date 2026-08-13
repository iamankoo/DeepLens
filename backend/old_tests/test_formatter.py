from app.citations.schemas import Citation
from app.citations.formatter import citation_formatter


citation = Citation(
    title="What is LangGraph?",
    url="https://www.ibm.com/think/topics/langgraph",
    source="IBM",
)

print()

print("APA")
print(citation_formatter.apa(citation))

print()

print("IEEE")
print(citation_formatter.ieee(citation, 1))

print()

print("MLA")
print(citation_formatter.mla(citation))