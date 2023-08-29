from pathlib import Path

basedir = Path(__file__).parent.parent

class BaseConfig:
    UPLOAD_FOLDER = str(Path(basedir, "apps", "images"))