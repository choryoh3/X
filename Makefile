PY ?= python3

.PHONY: setup run validate test

setup:
	$(PY) -m pip install --upgrade yt-dlp
	$(PY) -c "import sys; sys.path.insert(0,'scripts'); import common; common.ensure_dirs()"
	@test -f .env || cp .env.example .env
	@echo "setup OK"

run:
	@test -n "$(URL)" || (echo "usage: make run URL=<YouTube URL>"; exit 2)
	$(PY) scripts/pipeline.py "$(URL)"

validate:
	$(PY) scripts/validate_posts.py --latest

test:
	$(PY) -m unittest discover -s tests -v
