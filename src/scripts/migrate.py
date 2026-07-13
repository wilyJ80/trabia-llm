"""Alembic migration runner.

Usage:
    uv run python -m src.scripts.migrate          # upgrade to head
    uv run python -m src.scripts.migrate --downgrade  # downgrade one step
"""

import sys

from alembic.config import CommandLine, Config


def main() -> None:
    cli = CommandLine()
    options = cli.parser.parse_args(sys.argv[1:] if len(sys.argv) > 1 else ["upgrade", "head"])

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "alembic")
    cli.run_cmd(cfg, options)


if __name__ == "__main__":
    main()
