import pathlib
import PySimpleGUI as sg
from pathlib import Path
from panpanneed import start_server

def get_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    try:
        return s.getsockname()[0]
    finally:
        s.close()

SelectedFolderKey = "SelectedFolder"
SelectedPortKey = "SelectedPort"

layout = [
    [
        sg.Text("服务器文件夹"),
        sg.In(size=(25, 1), enable_events=True, key=SelectedFolderKey),
        sg.FolderBrowse(key=SelectedFolderKey),
        sg.Text("端口号"),
        sg.In(
            size=(8, 1),
            enable_events=True,
            key=SelectedPortKey,
            default_text="2992",
        ),
    ]
]

window = sg.Window("CanCanNeed启动器", layout)

while True:
    signal = window.read()
    if isinstance(signal, tuple):
        event, values = signal
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        else:
            selected_folder = values[SelectedFolderKey]
            if not pathlib.Path(selected_folder).exists():
                sg.popup(rf"文件夹 '{selected_folder}' 不存在")
                continue
            selected_port: str = values[SelectedPortKey]
            if not selected_port.isdigit():
                sg.popup(rf"端口号 '{selected_port}' 不是数字")
                continue
            port = int(selected_port)
            sg.popup(rf"请在局域网访问 'http://{get_ip()}:{port}'")
            start_server(port, selected_folder)

