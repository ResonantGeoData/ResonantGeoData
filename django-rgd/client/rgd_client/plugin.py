from typing import Dict, List, Optional, Tuple, Union

import validators

from .session import RgdClientSession
from .types import DATETIME_OR_STR_TUPLE, SEARCH_PREDICATE_CHOICE
from .utils import spatial_search_params


class RgdPlugin:
    """The base plugin that all other plugins must inherit from."""

    def __init__(self, session: RgdClientSession):
        self.session = session


class CorePlugin(RgdPlugin):
    """The core django-rgd client plugin."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session.base_url += 'rgd/'

    def search(
        self,
        query: Optional[Union[Dict, str]] = None,
        predicate: Optional[SEARCH_PREDICATE_CHOICE] = None,
        relates: Optional[str] = None,
        distance: Optional[Tuple[float, float]] = None,
        acquired: Optional[DATETIME_OR_STR_TUPLE] = None,
        instrumentation: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        time_of_day: Optional[DATETIME_OR_STR_TUPLE] = None,
    ) -> List[Dict]:
        """
        Search for geospatial entries based on various criteria.

        For Ranges (Tuples), an entry of `None` means that side of the range is unbounded.
        E.g. a range of (2, None) is 2 or more, (None, 5) is at most 5, (2, 5) is between 2 and 5.

        Args:
            query: Either a WKT GeoJSON representation, a GeoJSON string, or a GeoJSON dict.
            predicate: A named spatial predicate based on the DE-9IM. This spatial predicate will
                be used to filter data such that predicate(a, b) where b is the queried geometry.
            relates: Specify exactly how the queried geometry should relate to the data using a
                DE-9IM string code.
            distance: The min/max distance around the queried geometry in meters.
            acquired: The min/max date and time (ISO 8601) when data was acquired.
            instrumentation: The instrumentation used to acquire at least one of these data.
            limit: The maximum number of results to return.
            offset: The number of results to skip.

        Returns:
            A list of Spatial Entries.
        """
        params = spatial_search_params(
            query=query,
            predicate=predicate,
            relates=relates,
            distance=distance,
            acquired=acquired,
            instrumentation=instrumentation,
            limit=limit,
            offset=offset,
            time_of_day=time_of_day,
        )

        r = self.session.get('search', params=params)

        r.raise_for_status()

        return r.json()

    def create_collection(self, name: str):
        """Get or create collection by name."""
        payload = {'name': name}
        data = self.session.get('collection', params=payload).json()
        if isinstance(data, list) and data:
            # Test env returns list
            return data[0]
        elif isinstance(data, dict) and data['results']:
            # User env returns dict
            return data['results'][0]
        r = self.session.post('collection', json=payload)
        r.raise_for_status()
        return r.json()

    def create_file_from_url(
        self,
        url: str,
        name: Optional[str] = None,
        collection: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Dict:
        """
        Get or create a ChecksumFile from a URL.

        Args:
            url: The URL to retrieve the file from
            name: The name of the file
            collection: The integer collection ID to associate this ChecksumFile with
            description: The description of the file
        """
        # Verify that url is valid in shape, will raise error on failure
        validators.url(url)

        if isinstance(collection, str):
            collection = self.create_collection(collection)['id']

        # Check if url/collection combination already exists, and return it
        payload = {'url': url}
        if collection is not None:
            payload['collection'] = collection
        data = self.session.get('checksum_file', params=payload).json()
        # TODO: This is absolutely stumping me...
        if isinstance(data, list) and data:
            # Test env returns list
            return data[0]
        elif isinstance(data, dict) and data['results']:
            # User env returns dict
            return data['results'][0]

        # Create new checksum file
        # Construct payload, leaving out empty arguments
        payload['type'] = 2
        if name is not None:
            payload['name'] = name
        if collection is not None:
            payload['collection'] = collection
        if description is not None:
            payload['description'] = description

        r = self.session.post('checksum_file', json=payload)

        r.raise_for_status()
        return r.json()

    def file_tree_search(self, path: str = ''):
        """
        Search files in a hierarchical format, from a provided folder path.

        This endpoint returns all files and folders that are "within" the specified "folder" (the path argument).
        An example is

        Args:
            path: The path to apply to the search. This can be thought of as the folder path that you'd like to search.

        Returns:
            A dictionary, containing all direct subfolders (`folders`), and files (`files`) under the specified path.
        """
        return self.session.get('checksum_file/tree', params={'path_prefix': path}).json()
