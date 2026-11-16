from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Model, QuerySet
from django.test.utils import CaptureQueriesContext

from apps.blog.models import Post
from apps.blog.queries import QUERIES

PREVIEW_ROWS = 5
FIRST_MUTATING_NUMBER = 40
LAST_MUTATING_NUMBER = 44
SAMPLE_PAGE = 2


def sample_arguments() -> dict[int, dict[str, Any]]:
    """Sample argument values for queries that take arguments."""
    post_slug = Post.objects.values_list("slug", flat=True).first()
    return {
        4: {"slug": post_slug},
        7: {"page": SAMPLE_PAGE},
    }


class Command(BaseCommand):
    help = "Run ORM queries and show the result and the number of SQL queries."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--number", type=int, help="Run only the query with this number")
        parser.add_argument("--sql", action="store_true", help="Also print the SQL of every query")

    def handle(self, *args: Any, **options: Any) -> None:
        number: int | None = options["number"]
        if number is not None and number not in QUERIES:
            raise CommandError(f"Query #{number} does not exist.")

        if number is not None:
            numbers = [number]
        else:
            numbers = [n for n in sorted(QUERIES) if not FIRST_MUTATING_NUMBER <= n <= LAST_MUTATING_NUMBER]

        arguments = sample_arguments()
        for current in numbers:
            self._run(current, arguments.get(current, {}), show_sql=options["sql"])

    def _run(self, number: int, arguments: dict[str, Any], *, show_sql: bool) -> None:
        function = QUERIES[number]
        annotation_names: list[str] = []
        with CaptureQueriesContext(connection) as context:
            result = function(**arguments)
            if isinstance(result, QuerySet):
                annotation_names = list(result.query.annotations)
                result = list(result)

        count = len(context.captured_queries)
        unit = "query" if count == 1 else "queries"
        self.stdout.write(self.style.SUCCESS(f"#{number} {function.__name__} — {count} SQL {unit}"))
        if show_sql:
            for captured in context.captured_queries:
                self.stdout.write(captured["sql"])
        self._print_result(result, annotation_names)

    def _print_result(self, result: Any, annotation_names: list[str]) -> None:
        if not isinstance(result, list):
            self.stdout.write(f"  {result}")
            return
        for row in result[:PREVIEW_ROWS]:
            self.stdout.write(f"  {self._format_row(row, annotation_names)}")
        self.stdout.write(f"  ({len(result)} rows)")

    def _format_row(self, row: Any, annotation_names: list[str]) -> str:
        if annotation_names and isinstance(row, Model):
            values = {name: getattr(row, name) for name in annotation_names}
            return f"{row} {values}"
        return str(row)
