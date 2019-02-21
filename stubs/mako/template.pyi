from typing import Any


class Template:
    source = ...  # type: str
    def __init__(self, filename: str, input_encoding: str,
                 strict_undefined: bool): ...

    def render_unicode(self, **data: Any) -> str: ...
