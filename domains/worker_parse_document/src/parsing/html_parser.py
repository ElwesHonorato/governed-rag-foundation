
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_stack: list[str] = []
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs):
        if tag in {"script", "style", "nav"}:
            self._skip_stack.append(tag)
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str):
        if tag in {"script", "style", "nav"} and self._skip_stack:
            self._skip_stack.pop()
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str):
        if self._skip_stack:
            return
        normalized = " ".join(data.split())
        if not normalized:
            return
        if self._in_title:
            self.title_parts.append(normalized)
        self.text_parts.append(normalized)


class HtmlParser:
    def parse(self, content: str) -> dict[str, str]:
        extractor = _TextExtractor()
        extractor.feed(content)
        title = " ".join(extractor.title_parts).strip() or "Untitled"
        text = "\n".join(extractor.text_parts).strip()
        return {"title": title, "text": text}
