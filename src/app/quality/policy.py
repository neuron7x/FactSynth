from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Tuple

import yaml


def load_quality_policy(path: str | Path) -> Tuple[dict[str, Any], str]:
    """Load a quality policy YAML file and return its data and SHA-256 hash.

    Parameters
    ----------
    path: str | Path
        Path to the YAML policy file.

    Returns
    -------
    Tuple[dict[str, Any], str]
        A tuple containing the loaded policy as a dictionary and the
        SHA-256 hex digest of the file contents.
    """
    policy_path = Path(path)
    data = policy_path.read_bytes()
    policy = yaml.safe_load(data) or {}
    digest = hashlib.sha256(data).hexdigest()
    return policy, digest
