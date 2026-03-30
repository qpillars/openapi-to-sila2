"""Routes for the mock API"""
from . import _login, _instruments, _observable
import typing as tp
from fastapi import APIRouter


def all_routers() -> tp.Iterable[APIRouter]:
    """Get all route routers for registration
    
    Returns:
        Iterable of APIRouter instances
    """
    yield _login.router
    yield _instruments.router
    yield _observable.router
