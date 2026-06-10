from subprocess import CalledProcessError, TimeoutExpired, run


def convert_to(path, timeout=120):
	try:
		run(["unoconv", "-f", "pdf", str(path)], check=True, timeout=timeout)
	except TimeoutExpired as exc:
		raise OSError(f"PDF conversion timed out after {timeout} seconds") from exc
	except CalledProcessError as exc:
		raise OSError(f"PDF conversion failed with exit code {exc.returncode}") from exc
