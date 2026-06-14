"""Entry point for the Academic PDF Processor.

Run with: python app.py

Opens the Tkinter window. The Run button is wired to a background worker thread
in issue #18.
"""

import tkinter as tk

from apdf.progress import ProgressReporter
from apdf.ui.main_window import MainWindow


def main() -> None:
    root = tk.Tk()
    reporter = ProgressReporter()
    MainWindow(root, reporter)
    root.mainloop()


if __name__ == "__main__":
    main()
