"""Install the built wheel and run the sdist's tests in a separate directory."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


def main():
    dist = Path(__file__).resolve().parents[1] / "dist"
    wheel, = dist.glob("*.whl")
    archive, = dist.glob("*.tar.gz")
    with zipfile.ZipFile(wheel) as contents:
        for member in contents.namelist():
            top = member.split("/", 1)[0]
            if top != "wright_workflow" and top != wheel.name.split("-py", 1)[0] + ".dist-info":
                raise ValueError(f"Unexpected wheel member {member}")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        shutil.unpack_archive(archive, root)
        source, = root.iterdir()
        subprocess.run([sys.executable, "-m", "pip", "install", str(wheel)], check=True, cwd=root)
        subprocess.run(
            [sys.executable, "-I", "-m", "pytest", "-q", str(source / "tests")],
            check=True, cwd=root,
        )


if __name__ == "__main__":
    main()
