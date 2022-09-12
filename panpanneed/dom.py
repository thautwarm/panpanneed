from __future__ import annotations

from dataclasses import dataclass
from xml.sax.saxutils import escape
import pretty_doc as PD
import io


def _create_tag_contents(tagname, attrs: dict[str, str | None]):
    sio = io.StringIO()
    sio.write(f"{tagname}")
    for k, v in attrs.items():
        if v is None:
            sio.write(f" {k}")
        else:
            sio.write(rf' {k}="{escape(v)}"')
    return sio.getvalue()


@dataclass
class X:
    tagname: str
    attrs: dict[str, str | None]
    children: list[X | str]

    def render(self) -> PD.Doc:
        if not self.children:
            return PD.angle(
                PD.seg(_create_tag_contents(self.tagname, self.attrs)) * PD.seg("/")
            )
        return PD.vsep(
            [
                PD.angle(PD.seg(_create_tag_contents(self.tagname, self.attrs))),
                PD.vsep(
                    [
                        PD.seg(escape(child))
                        if isinstance(child, str)
                        else child.render()
                        for child in self.children
                    ]
                )
                >> 4,
                PD.angle(PD.seg("/") * PD.seg(self.tagname)),
            ]
        )


if __name__ == "__main__":
    dom = X(
        "div",
        {"class": "container"},
        [
            X("h1", {"class": "title"}, ["Hello, world!"]),
            X("p", {"class": "content"}, ["This is a paragraph."]),
            X(
                "ul",
                {"class": "list"},
                [
                    "&a<a>",
                    X("li", {"class": "item"}, ["Item 1"]),
                    X("li", {"class": "item"}, ["Item 2"]),
                    X("li", {"class": "item"}, ["Item 3"]),
                ],
            ),
        ],
    ).render()
    dom.render(lambda x: print(x, end=""))
