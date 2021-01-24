import os, sys
from pathlib import Path

def share_dir():
    """
    This will resolve to the shared data dir under the current PYTHONPATH or CONDA_PREFIX if it exists.
    Note this has to work on window as well as linux/osx
    """
    mod_path = Path(__file__)
    share_path = mod_path.parent.parent.parent / "share"
    if share_path.is_dir():
        return share_path
    try:
        mod_path.relative_to(os.environ.get("CONDA_PREFIX"))
        share_path = mod_path.parent.parent / "share"
        if share_path.is_dir():
            return share_path
    except:
        pass # this module is not under CONDA_PREFIX
    raise FileNotFoundError("share directory not found, set your PYTHONPATH or activate your conda environment")
