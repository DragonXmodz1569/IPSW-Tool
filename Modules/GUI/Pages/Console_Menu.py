import datetime
from functools import partial

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit


class ConsolePage(QWidget):
    log_signal = Signal(str, str)  # page_name, message

    def __init__(self):
        super().__init__()
        self.logs = {}
        self.current_log = None
        layout = QVBoxLayout(self)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)
        self.log_signal.connect(self._append_text)

    def get_logger(self, log_state):
        return partial(self.console_print, Log_State=log_state)

    def console_print(self, Print_Message, Log_State='General'):
        if Log_State not in self.logs:
            self.logs[Log_State] = []
        time = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{time}] | [{Log_State}] {Print_Message}"
        self.logs[Log_State].append(formatted)
        self.log_signal.emit(Log_State, formatted)

    def _append_text(self, Log_State, Print_Message):
        if self.current_log is None or self.current_log == Log_State:
            self.output.append(Print_Message)

    def show_log(self, log_state):
        self.current_log = log_state
        self.output.clear()
        for line in self.logs.get(log_state, []):
            self.output.append(line)