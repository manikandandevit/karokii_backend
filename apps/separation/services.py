import subprocess
import sys
from pathlib import Path

from django.conf import settings


def run_demucs(input_path: Path, output_root: Path) -> Path:
    """
    Run Demucs 4-stem separation and return job output directory.
    Uses the same Python interpreter as Django so ``demucs`` is found in the active venv.
    """
    output_root.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "demucs.separate",
        "--mp3",
        "-n",
        "htdemucs",
        "-o",
        str(output_root),
        str(input_path),
    ]
    subprocess.run(command, check=True)

    model_dir = output_root / "htdemucs"
    # Demucs output folder name usually equals source filename stem.
    job_dir = model_dir / input_path.stem
    _ensure_no_vocals_from_four_stems(job_dir)
    return job_dir


def _ensure_no_vocals_from_four_stems(job_output_dir: Path) -> None:
    """
    ``htdemucs`` writes vocals, drums, bass, other — not a single no_vocals track.
    Mix drums + bass + other into ``no_vocals.mp3`` so instrumental/music downloads work.
    """
    for ext in (".mp3", ".wav", ".flac"):
        if (job_output_dir / f"no_vocals{ext}").exists():
            return

    paths: list[Path] = []
    for stem in ("drums", "bass", "other"):
        found: Path | None = None
        for ext in (".mp3", ".wav", ".flac"):
            candidate = job_output_dir / f"{stem}{ext}"
            if candidate.exists():
                found = candidate
                break
        if found:
            paths.append(found)

    if len(paths) < 3:
        return

    out_file = job_output_dir / "no_vocals.mp3"
    command = ["ffmpeg", "-y"]
    for path in paths:
        command.extend(["-i", str(path)])
    command.extend(
        [
            "-filter_complex",
            "amix=inputs=3:normalize=0",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(out_file),
        ]
    )
    subprocess.run(command, check=True)


def _stem_path(job_output_dir: Path, stem: str) -> Path:
    mapped = "no_vocals" if stem in {"instrumental", "music"} else stem
    for ext in (".mp3", ".wav", ".flac"):
        candidate = job_output_dir / f"{mapped}{ext}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Stem file not found for '{stem}'")


def export_mix(job_output_dir: Path, stems: list[str], output_name: str | None = None) -> Path:
    output_name = output_name or "mix"
    selected = []
    for stem in stems:
        selected.append(_stem_path(job_output_dir, stem))

    output_file = job_output_dir / f"{output_name}.wav"
    command = ["ffmpeg", "-y"]
    for path in selected:
        command.extend(["-i", str(path)])

    if len(selected) == 1:
        command.extend(["-c:a", "pcm_s16le", str(output_file)])
    else:
        input_count = len(selected)
        command.extend(
            [
                "-filter_complex",
                f"amix=inputs={input_count}:normalize=0",
                "-c:a",
                "pcm_s16le",
                str(output_file),
            ]
        )

    subprocess.run(command, check=True)
    return output_file


def get_output_root() -> Path:
    return Path(settings.MEDIA_ROOT) / "outputs"
