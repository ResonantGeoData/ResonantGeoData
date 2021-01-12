"""Views for the API.

Views routed under `/api/geodata`. The primary `Content-Type` recieved and served
by these views ought to be `application/json`.
"""

__all__ = ['download', 'get', 'post', 'search']

from . import download, get, post, search
