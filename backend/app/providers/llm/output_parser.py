import json
import re


class OutputParser:

    @staticmethod
    def parse_json(text: str):

        if not text:
            return None

        text = text.strip()

        # Remove markdown code fences
        text = re.sub(r"^```json", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)

        text = text.strip()

        try:
            return json.loads(text)

        except Exception:
            return None


output_parser = OutputParser()