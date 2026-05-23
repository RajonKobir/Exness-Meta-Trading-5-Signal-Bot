import json
import os

SETTINGS_FILENAME = "settings.json"


def save_settings(data, path=None):
    try:
        if not path:
            path = os.path.join(os.getcwd(), SETTINGS_FILENAME)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return True

    except Exception as e:
        return False, str(e)


def load_settings(path=None):
    try:
        if not path:
            path = os.path.join(os.getcwd(), SETTINGS_FILENAME)

        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        return None
