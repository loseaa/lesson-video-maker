"""Small helpers for native media commands and staged output files."""
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path


def run_command(args: list[str], timeout: float = 180) -> str:
    try:
        result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=timeout, check=True)
    except FileNotFoundError as error:
        raise ValueError(f"required executable not found: {args[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip()
        raise ValueError(f"{args[0]} failed: {detail or error.returncode}") from error
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"{args[0]} timed out") from error
    return result.stdout


@contextmanager
def staged_file(destination: Path):
    """Publish only after the writer exits successfully."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".new-", dir=destination.parent) as folder:
        scratch = Path(folder) / destination.name
        yield scratch
        os.replace(scratch, destination)
