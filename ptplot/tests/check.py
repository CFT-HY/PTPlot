"""Checks of the responses of the views for the tests."""

import typing as tp

from django.forms import Form
from django.http import HttpResponseBase
from django.test import TestCase
from django.urls import reverse

ALLOW_CODES: tp.Iterable[int] = (200, 302)


def check_status_code(
        response: HttpResponseBase,
        allow_codes: tp.Iterable[int] | None = None,
        url: str | None = None) -> int:
    """Check the status code of a HttpResponse."""
    allow_codes2 = ALLOW_CODES if allow_codes is None else (*ALLOW_CODES, *allow_codes)
    if response.status_code not in allow_codes2:
        raise AssertionError(
            f"Invalid status code {response.status_code}, expected one of {allow_codes2}" +
            ("." if url is None else f' for url "{url}".')
        )
    return response.status_code


def check_url(
        test: TestCase,
        url: str,
        form: Form | None = None,
        data: dict[str, tp.Any] | None = None,
        allow_codes: tp.Iterable[int] | None = None) -> int:
    """Test whether the given url returns a valid status code."""
    data2 = {
        key: value for key, value in (
            ({} if data is None else data) if form is None
            else form.cleaned_data if data is None
            else {**form.cleaned_data, **data}
        ).items()
        # Remove None values, as they cannot be encoded in the query string
        if value is not None
    }
    return check_status_code(test.client.get(url, data=data2), allow_codes=allow_codes, url=url)


def check_view(
        test: TestCase,
        view: str,
        view_args: tp.Sequence[tp.Any] | None = None,
        view_kwargs: dict[str, tp.Any] | None = None,
        form: Form | None = None,
        data: dict[str, tp.Any] | None = None,
        allow_codes: tp.Iterable[int] | None = None) -> int:
    """Test whether the given view returns a valid status code."""
    return check_url(
        test=test,
        url=reverse(view, args=view_args, kwargs=view_kwargs),
        form=form, data=data, allow_codes=allow_codes
    )
