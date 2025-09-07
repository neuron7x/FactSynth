from typer.testing import CliRunner
from factsynth_ultimate.cli import app


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "2.0.0"

