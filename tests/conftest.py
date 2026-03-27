from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


if "PyQt5" not in sys.modules:
    class _BoundSignal:
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args, **kwargs):
            for cb in list(self._callbacks):
                cb(*args, **kwargs)

    class _SignalDescriptor:
        def __init__(self):
            self._name = None

        def __set_name__(self, _owner, name):
            self._name = f"__sig_{name}"

        def __get__(self, instance, _owner):
            if instance is None:
                return self
            signal = getattr(instance, self._name, None)
            if signal is None:
                signal = _BoundSignal()
                setattr(instance, self._name, signal)
            return signal

    class QObject:
        def __init__(self, _parent=None):
            pass

    class QProcess:
        NotRunning = 0

        def __init__(self, _parent=None):
            pass

    def pyqtSignal(*_args, **_kwargs):
        return _SignalDescriptor()

    qtcore = types.ModuleType("PyQt5.QtCore")
    qtcore.QObject = QObject
    qtcore.QProcess = QProcess
    qtcore.pyqtSignal = pyqtSignal
    qtcore.QSettings = type("QSettings", (), {})

    qtwidgets = types.ModuleType("PyQt5.QtWidgets")
    qtwidgets.QCheckBox = type("QCheckBox", (), {})
    qtwidgets.QLineEdit = type("QLineEdit", (), {})


    pyqt5 = types.ModuleType("PyQt5")
    pyqt5.QtCore = qtcore
    pyqt5.QtWidgets = qtwidgets

    sys.modules["PyQt5"] = pyqt5
    sys.modules["PyQt5.QtCore"] = qtcore
    sys.modules["PyQt5.QtWidgets"] = qtwidgets
