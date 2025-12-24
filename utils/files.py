import os
from typing import List

def get_account_files(folder: str, ext: str = ".env") -> List[str]:
    """Return list of all account files in a folder"""
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.startswith(ext)
    ]