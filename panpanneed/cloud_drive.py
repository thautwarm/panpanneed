from __future__ import annotations
import typing
import typing_extensions
from panpanneed.fsutils import FsObject, File, Directory
from fs.osfs import OSFS
from fs.compress import write_zip
from panpanneed.declarative_ui import (
    DownloadSource,
    TreeView,
    Widget,
    Text,
    App,
    GroupBox,
    Button,
    Link,
    Window,
)
import flask
import logging
import pathlib
import tempfile


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BUFFER_SIZE = 1024


class CloudService(App):
    def __init__(self, name: str, filepath: str = ""):
        filepath = filepath or "."
        self.app = flask.Flask(name)
        self.rootdirpath = pathlib.Path(filepath).absolute()
        self.rootdir = OSFS(self.rootdirpath.as_posix())
        App.__init__(self)

    def serve(self, port: str | int | None = 8000):
        @self.app.route("/")
        def index():
            return self.create_page("page")

        @self.app.route("/<path:route>")
        def routing(route):
            logger.debug(f"routing [{route}]")
            return self.create_page(route)

        if port is not None:
            port = int(port)
        self.app.run(host="0.0.0.0", port=port)

    def _create_stream(self, fso: FsObject):
        """get a stream from a relative path"""
        mode: typing.Literal["file", "dir"]
        path: str
        logger.debug(f"creating stream from {fso}")
        if isinstance(fso, File):
            path = fso.secs
            mode = "file"
        elif isinstance(fso, Directory):
            path = fso.secs
            mode = "dir"
        else:
            typing_extensions.assert_never(fso)
        if mode == "file":

            def mk_stream(file: typing.IO[bytes]):
                while buffer := file.read(BUFFER_SIZE):
                    yield buffer

            return mk_stream(self.rootdir.open(path, "rb"))
        elif mode == "dir":
            fs_dir = self.rootdir.opendir(path)
            # TODO: check if exists
            name = (self.rootdirpath / path).name

            def mk_steam():
                # TODO: session-based cache
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmpdir = pathlib.Path(tmpdir)
                    zipfile = (tmpdir / name).as_posix() + ".zip"
                    write_zip(fs_dir, zipfile)
                    with open(zipfile, "rb") as file:
                        while buffer := file.read(BUFFER_SIZE):
                            yield buffer

            return mk_steam()
        else:
            typing_extensions.assert_never(mode)

    def _build_page(self, routes: list[str]):
        fspath = self.rootdirpath.joinpath(*routes)
        if not fspath.is_dir() or not fspath.is_relative_to(self.rootdirpath):
            sec = "/".join(routes)
            return Text(f"{sec}不存在。")

        window_contents: list[Widget] = []
        items: list[Widget] = []
        if fspath.parent.is_relative_to(self.rootdirpath):
            each = fspath.parent
            real_sec = each.relative_to(self.rootdirpath).as_posix()
            child_name = each.name + "/"
            window_contents.append(Button(True, "", Link("返回上一级", "/page/" + real_sec)))

        for each in fspath.iterdir():
            if each == fspath:
                continue
            real_sec = each.relative_to(self.rootdirpath).as_posix()
            if each.is_dir():
                child_name = each.name + "/"
                items.append(Link(child_name, "/page/" + real_sec))
            else:
                # TODO: view file and syntax highlighting
                child_name = each.name
                items.append(DownloadSource(child_name, real_sec, download=True))
        group_contents: list[Widget] = [TreeView(items)]
        if routes:
            directory_sections = fspath.relative_to(self.rootdirpath).as_posix()
            window_contents.append(
                Button(
                    True,
                    "",
                    DownloadSource(
                        fspath.name + ".zip",
                        directory_sections,
                        download=True,
                        text="下载当前文件夹",
                    ),
                )
            )
        else:
            directory_sections = "/"

        group = GroupBox(directory_sections, group_contents)
        window_contents.append(group)
        return Window(
            title="PanPanNeed文件树",
            body=window_contents,
            close_btn=Button(True, "", None),
        )

    def _build_download(self, routes: list[str]) -> Widget | flask.Response:
        *routes, _ = routes
        pso = self.rootdirpath.joinpath(*routes)
        if pso.is_file():
            return flask.Response(
                flask.stream_with_context(self._create_stream(File("/".join(routes))))
            )
        if pso.is_dir():
            return flask.Response(
                flask.stream_with_context(
                    self._create_stream(Directory("/".join(routes)))
                )
            )
        raise ValueError(f"{pso} is not a valid filesystem representation")

    def build(self, route: str) -> Widget | flask.Response:
        routes = list(filter(None, route.split("/")))
        if not routes:
            return self.build("page")
        category, *routes = routes
        if category == "page":
            return self._build_page(routes)
        elif category == "download":
            return self._build_download(routes)
        else:
            return Text(rf"未知的页面链接 ({route!r})，应该以'page/'或'download/'开头。")


def start_server(port: str | int | None = None, rootdir="."):
    import sys

    name = sys._getframe(1).f_globals["__name__"]
    cloud_service = CloudService(name, rootdir)
    cloud_service.serve(port=port)
