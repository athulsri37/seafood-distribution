"""Shared settings for paginated list endpoints.

Lists are newest first and paged with a cursor: the client passes `before_id` (the id of
the last item it has) to get the next page. Unlike page numbers, a cursor doesn't shift
when new rows arrive. Every list sets X-Total-Count so clients can show "50 of 120".
"""
from fastapi import Query, Response
from sqlalchemy.orm import Query as SqlQuery

PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
TOTAL_COUNT_HEADER = "X-Total-Count"

LimitParam = Query(PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="How many items to return.")
BeforeIdParam = Query(None, ge=1, description="Return items older than this id: the last id of the previous page.")


def set_total_count(response: Response, query: SqlQuery) -> None:
    """Report how many rows match the filters, ignoring the page limit and cursor."""
    response.headers[TOTAL_COUNT_HEADER] = str(query.count())
