# PanPanNeed

一行代码的自建云盘。

从Python启动:

```python
from panpanneed import start_server
start_server(port=2992)
```

命令行启动:

```bash
python -m panpanneed --port=2992
```


## Features

可以被视为支持文件夹下载的http.server模块。

## Known Bugs

1. 文件夹较大时，等待服务器进行压缩的时间较长。请耐心等待。
