"""Routes for the mock API"""

import typing as tp

from fastapi import APIRouter

from . import _instruments, _login, _observable


def all_routers() -> tp.Iterable[APIRouter]:
    """Get all route routers for registration

    Returns:
        Iterable of APIRouter instances
    """
    yield _login.router
    yield _instruments.router
    yield _observable.router
