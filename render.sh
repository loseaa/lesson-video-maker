#!/bin/sh
# Resolve dependencies before moving from the caller's project to the Skill.
set -eu
skill_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
path_python=$(command -v python3 || true)
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
    PATH="$PATH:/opt/homebrew/bin:/usr/local/bin"
    export PATH
fi
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
    printf '%s\n' 'lesson-video-maker requires ffmpeg and ffprobe.' >&2
    exit 1
fi
for candidate in "$path_python" /opt/homebrew/bin/python3 /usr/local/bin/python3 \
    "$HOME"/.workbuddy/binaries/python/versions/*/bin/python3
do
    [ -x "$candidate" ] || continue
    case "$candidate" in
        /*) ;;
        *) candidate="$(pwd)/$candidate" ;;
    esac
    if "$candidate" -B -c 'import sys; from PIL import __version__; sys.exit(not (sys.version_info >= (3, 10) and int(__version__.split(".")[0]) >= 10))' >/dev/null 2>&1; then
        cd "$skill_dir"
        exec "$candidate" -B -m lesson_video_maker.cli "$@"
    fi
done
printf '%s\n' 'lesson-video-maker requires Python 3.10+ with Pillow 10+ in the same interpreter.' >&2
exit 1
