"""compete - Competitive Intelligence Platform pipeline package."""

import warnings

# `instructor` eagerly imports the deprecated `google.generativeai` provider,
# which emits a noisy FutureWarning on every import. Functionality is
# unaffected; silence it at the package boundary (before instructor loads).
warnings.filterwarnings("ignore", category=FutureWarning, module=r"instructor.*")

__version__ = "0.1.0"
