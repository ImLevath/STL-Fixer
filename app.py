from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from mesh_pipeline import process_stl_file


class MeshWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, source_path: str) -> None:
        super().__init__()
        self.source_path = source_path

    def run(self) -> None:
        try:
            mesh = process_stl_file(self.source_path, progress=self.progress.emit)
            self.finished.emit(mesh)
        except Exception as exc:  # pragma: no cover - GUI error path
            self.failed.emit(str(exc))


class DropLabel(QLabel):
    file_dropped = Signal(str)

    def __init__(self) -> None:
        super().__init__("Drop an STL file here")
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px dashed #8a8a8a; border-radius: 8px; padding: 24px;")

    def dragEnterEvent(self, event):  # type: ignore[override]
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(".stl"):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):  # type: ignore[override]
        urls = event.mimeData().urls()
        if urls:
            local_path = urls[0].toLocalFile()
            if local_path.lower().endswith(".stl"):
                self.file_dropped.emit(local_path)


from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("STL Fixer")
        self.setMinimumWidth(520)

        self.drop_area = DropLabel()
        self.drop_area.file_dropped.connect(self.process_file)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)

        self.status_label = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        layout = QVBoxLayout()
        layout.addWidget(self.drop_area)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._worker_thread: QThread | None = None

    def browse_file(self) -> None:
        source_path, _ = QFileDialog.getOpenFileName(self, "Select STL", "", "STL Files (*.stl)")
        if source_path:
            self.process_file(source_path)

    def process_file(self, source_path: str) -> None:
        self.progress.setValue(0)
        self.status_label.setText(f"Processing {Path(source_path).name}")
        self.browse_button.setEnabled(False)

        thread = QThread(self)
        worker = MeshWorker(source_path)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(self.update_progress)
        worker.finished.connect(self.on_processed)
        worker.failed.connect(self.on_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.browse_button.setEnabled(True))

        self._worker_thread = thread
        thread.start()

    def update_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.status_label.setText(message)

    def on_processed(self, mesh) -> None:
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Repaired STL", "repaired.stl", "STL Files (*.stl)")
        if not output_path:
            self.status_label.setText("Processing finished; save cancelled")
            return

        if not output_path.lower().endswith(".stl"):
            output_path = f"{output_path}.stl"

        mesh.export(output_path)
        self.status_label.setText("Saved repaired STL")
        QMessageBox.information(self, "Done", f"Saved repaired STL to:\n{output_path}")

    def on_failed(self, error_message: str) -> None:
        self.progress.setValue(0)
        self.status_label.setText("Processing failed")
        QMessageBox.critical(self, "Error", error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
