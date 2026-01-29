"""Pytest configuration for pymrio tests."""

import matplotlib

# Use a non-interactive backend, e.g. on Windows CI workers without Tcl/Tk.
matplotlib.use("Agg", force=True)
