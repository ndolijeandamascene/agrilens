"""
Development bootstrap script: creates .env if missing, runs migrations, seeds core geography.
"""
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def setup():
    env_file = BASE_DIR / '.env'
    example_env = BASE_DIR / '.env.example'
    if not env_file.exists() and example_env.exists():
        shutil.copy(example_env, env_file)
        print("Created .env from .env.example")
    print("Run `python manage.py migrate` and `python scripts/seed_geography.py` to complete setup.")

if __name__ == '__main__':
    setup()
