import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([
        sys.executable, "-m", "celery",
        "-A", "app.core.celery_app", 
        "flower",
        "--port=5555",
        "--basic_auth=admin:admin"
    ])
