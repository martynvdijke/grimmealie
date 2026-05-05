"""Invoke tasks — run via `inv <task>`."""
from invoke import task


@task
def fmt(c):
    """Run ruff formatter"""
    c.run("uv run ruff format src/grimmealie tests")


@task
def lint(c):
    """Run ruff linter"""
    c.run("uv run ruff check src/grimmealie tests")


@task
def ty(c):
    """Run type checker"""
    c.run("uv run ty check src/grimmealie tests")


@task
def test(c):
    """Run pytest"""
    c.run("uv run pytest tests/ -v")


@task(pre=[fmt, lint, ty, test], default=True)
def all(c):
    """Format, lint, typecheck, and test"""
    pass
