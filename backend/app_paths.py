import os
import tempfile


APP_NAME = "Shreeji Ceramica"
LEGACY_DATA_DIR = os.path.join(os.path.expanduser("~"), ".quotation-ai")


def _candidate_data_dirs():
    for env_name in ("LOCALAPPDATA", "APPDATA"):
        root = str(os.getenv(env_name, "")).strip()
        if root:
            yield os.path.join(root, APP_NAME)

    yield LEGACY_DATA_DIR
    yield os.path.join(tempfile.gettempdir(), APP_NAME)


def resolve_data_dir(is_frozen: bool, module_dir: str) -> str:
    if not is_frozen:
        return module_dir

    for candidate in _candidate_data_dirs():
        try:
            os.makedirs(os.path.join(candidate, "static", "images"), exist_ok=True)
            os.makedirs(os.path.join(candidate, "static", "quotes"), exist_ok=True)
            os.makedirs(os.path.join(candidate, "uploads"), exist_ok=True)
            os.makedirs(os.path.join(candidate, "quotes_history"), exist_ok=True)
            probe_path = os.path.join(candidate, ".write_test.tmp")
            with open(probe_path, "w", encoding="utf-8") as probe_file:
                probe_file.write("ok")
            os.remove(probe_path)
            return candidate
        except OSError:
            continue

    fallback = os.path.join(tempfile.gettempdir(), APP_NAME)
    os.makedirs(os.path.join(fallback, "static", "images"), exist_ok=True)
    os.makedirs(os.path.join(fallback, "static", "quotes"), exist_ok=True)
    os.makedirs(os.path.join(fallback, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(fallback, "quotes_history"), exist_ok=True)
    return fallback
