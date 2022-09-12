from __future__ import annotations
from dataclasses import dataclass
from panpanneed.dom import X
from panpanneed.fsutils import Directory, File, FsObject
import flask
import typing_extensions
import typing
import abc
import io


@dataclass(frozen=True)
class ActionId:
    id: int

    def to_download_url(self, src: str, filename: str):
        return rf"/action/{self.id}/{src}/{filename}"


def to_download_url(src: str, filename: str):
    return rf"/download/{src}/{filename}"


UsedActionKind = typing.Literal["download", "jump"]
ContentProvider = typing.Callable[[FsObject], typing.Generator[bytes, None, None]]


@dataclass
class RenderCtx:
    is_in_tree_view: bool


class Widget(abc.ABC):
    @abc.abstractmethod
    def render(self, ctx: RenderCtx) -> X | str:
        raise NotImplementedError


@dataclass
class Text(Widget):
    text: str

    def render(self, _: RenderCtx):
        return self.text


@dataclass
class Button(Widget):
    enabled: bool
    text: str
    on_click: Widget | None

    def render(self, ctx: RenderCtx):
        if not self.on_click:
            return X("button", {}, [self.text])
        return X("button", {}, [self.text, self.on_click.render(ctx)])


@dataclass
class Link(Widget):
    text: str
    link: str

    def render(self, _: RenderCtx):
        return X("a", {"href": self.link}, [self.text])


@dataclass
class DownloadSource(Widget):
    filename: str
    src: str
    download: bool
    text: str | None = None

    def render(self, ctx: RenderCtx):
        text = self.text or self.filename
        attrs: dict[str, str | None] = {
            "href": to_download_url(self.src, self.filename)
        }
        if self.download:
            attrs["download"] = None
        # dict(attrs) to pass typecheck
        return X("a", attrs, [text])


@dataclass
class Tab(Widget):
    title: str
    selected: str
    contents: list[tuple[str, list[Widget]]]

    def render(self, ctx: RenderCtx):
        return X(
            "section",
            {"class": "tabs"},
            [
                X(
                    "menu",
                    {"role": "tablist", "aria-label": f"{self.title}@{id(self)}"},
                    [
                        X(
                            "button",
                            {"role": "tab", "aria-controls": f"tab-{id(wids)}"},
                            [tabName],
                        )
                        for tabName, wids in self.contents
                    ],
                ),
                *[
                    X(
                        "article",
                        {"role": "tabpanel", "id": f"tab-{id(wids)}"},
                        [wid.render(ctx) for wid in wids],
                    )
                    for _, wids in self.contents
                ],
            ],
        )


@dataclass
class Header(Widget):
    text: str
    level: int

    def render(self, _: RenderCtx):
        return X("h" + str(self.level), {}, [self.text])


@dataclass
class GroupBox(Widget):
    legend: str
    rows: list[Widget]

    def render(self, ctx: RenderCtx):
        return X(
            "fieldset",
            {},
            [X("div", {"class": "field-row"}, [row.render(ctx)]) for row in self.rows],
        )


@dataclass
class TreeView(Widget):
    children: list[Widget]

    def render(self, ctx: RenderCtx):
        attrs: dict[str, None | str]
        if not ctx.is_in_tree_view:
            attrs = {"class": "tree-view"}
        else:
            attrs = {}

        old = ctx.is_in_tree_view
        ctx.is_in_tree_view = True
        try:
            return X(
                "ul",
                attrs,
                [X("li", {}, [child.render(ctx)]) for child in self.children],
            )
        finally:
            ctx.is_in_tree_view = old


@dataclass
class Window(Widget):
    title: str

    body: list[Widget]

    minimize_btn: Button | None = None
    maximize_btn: Button | None = None
    close_btn: Button | None = None

    def render(self, ctx: RenderCtx):
        controls = []
        if self.minimize_btn:
            btn = self.minimize_btn.render(ctx)
            btn.attrs["aria-label"] = "Minimize"
            controls.append(btn)
        if self.maximize_btn:
            btn = self.maximize_btn.render(ctx)
            btn.attrs["aria-label"] = "Maximize"
            controls.append(btn)
        if self.close_btn:
            btn = self.close_btn.render(ctx)
            btn.attrs["aria-label"] = "Close"
            controls.append(btn)

        return X(
            "div",
            {"class": "window"},
            [
                X(
                    "div",
                    {"class": "title-bar"},
                    [
                        X("div", {"class": "title-bar-text"}, [self.title]),
                        X("div", {"class": "title-bar-controls"}, controls),
                    ],
                ),
                X(
                    "div",
                    {"class": "window-body"},
                    [wid.render(ctx) for wid in self.body],
                ),
            ],
        )


class App(abc.ABC):

    ctx: RenderCtx

    def __init__(self):
        self.ctx = RenderCtx(False)

    @abc.abstractmethod
    def build(self, route: str) -> Widget | flask.Response:
        raise NotImplementedError

    def create_page(self, route: str) -> str | flask.Response:
        widget = self.build(route)
        if isinstance(widget, flask.Response):
            # response, etc.
            return widget
        html = X(
            "html",
            {},
            [
                X(
                    "head",
                    {},
                    [
                        X("meta", {"charset": "utf-8"}, []),
                        X(
                            "link",
                            {"rel": "stylesheet", "href": r"https://unpkg.com/7.css"},
                            [],
                        ),
                        X("body", {}, [widget.render(self.ctx)]),
                    ],
                )
            ],
        )

        buf = io.StringIO()

        def write(s: str):
            buf.write(s)

        html.render().render(write)
        return buf.getvalue()
