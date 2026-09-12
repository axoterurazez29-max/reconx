#!/usr/bin/env python3
"""
ReconX - Terminal UI with Rich
Progress bars, status tables, colored output.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich import box

console = Console()


def info(message):
    console.print(f"[cyan][*][/cyan] {message}")


def success(message):
    console.print(f"[green][+][/green] {message}")


def warn(message):
    console.print(f"[yellow][!][/yellow] {message}")


def error(message):
    console.print(f"[red][-][/red] {message}")


def header(title):
    console.print()
    console.rule(f"[bold cyan]{title}[/bold cyan]")
    console.print()


def module_start(name):
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]{name}[/bold cyan]",
            border_style="cyan",
            padding=(0, 2),
        )
    )


def module_done(name, found, duration):
    console.print(
        f"[green]  ✓[/green] [bold]{name}[/bold] complete — "
        f"[yellow]{found}[/yellow] result(s) in "
        f"[magenta]{duration:.2f}s[/magenta]"
    )


def show_tool_status(tool_status):
    table = Table(
        title="Tool Status",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Tool", style="white", no_wrap=True)
    table.add_column("Status", justify="center")

    for tool, available in sorted(tool_status.items()):
        if available:
            table.add_row(tool, "[green]OK[/green]")
        else:
            table.add_row(tool, "[red]MISSING[/red]")

    console.print(table)


def show_summary_table(title, rows, columns):
    table = Table(
        title=title,
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
    )
    for col in columns:
        table.add_column(col, style="white", overflow="fold")

    for row in rows:
        table.add_row(*[str(c) for c in row])

    console.print(table)


def show_module_summary(results):
    """
    results: list of dicts with keys:
      module, found, duration, status
    """
    table = Table(
        title="Module Summary",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Module", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Results", justify="right", style="yellow")
    table.add_column("Duration", justify="right", style="magenta")

    for r in results:
        status = r.get("status", "ok")
        if status == "ok":
            status_str = "[green]OK[/green]"
        elif status == "empty":
            status_str = "[yellow]EMPTY[/yellow]"
        elif status == "skip":
            status_str = "[dim]SKIP[/dim]"
        else:
            status_str = "[red]FAIL[/red]"

        table.add_row(
            r.get("module", "?"),
            status_str,
            str(r.get("found", 0)),
            f"{r.get('duration', 0):.2f}s",
        )

    console.print(table)


def make_progress():
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[yellow]{task.completed}[/yellow]/[yellow]{task.total}[/yellow]"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )


def print_banner(banner_text, version):
    console.print(f"[cyan]{banner_text}[/cyan]")
    console.print(
        f"  [bold]ReconX[/bold] v{version} — Modular Reconnaissance Framework"
    )
    console.print("  " + "=" * 55)
    console.print()


def print_report_path(path):
    console.print()
    console.print(
        Panel.fit(
            f"[bold green]HTML Report[/bold green]\n[white]{path}[/white]",
            border_style="green",
            padding=(0, 2),
        )
    )
