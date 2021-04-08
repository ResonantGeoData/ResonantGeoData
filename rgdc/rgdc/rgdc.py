from base64 import b64encode
import json
from json.decoder import JSONDecodeError
from pathlib import Path
import tempfile
from typing import Dict, Iterator, List, Optional, Tuple, Union

from geomet import wkt

from .session import RgdcSession
from .types import DATETIME_OR_STR_TUPLE, SEARCH_DATATYPE_CHOICE, SEARCH_PREDICATE_CHOICE
from .utils import DEFAULT_RGD_API, datetime_to_str, iterate_response_bytes, results


class Rgdc:
    def __init__(
        self,
        api_url: str = DEFAULT_RGD_API,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize a RGD Client.

        Args:
            api_url: The base url of the RGD API instance.
            username: The username to authenticate to the instance with, if any.
            password: The password associated with the provided username.

        Returns:
            A new Rgdc instance.
        """
        auth_header = None
        if username and password:
            encoded_credentials = b64encode(f'{username}:{password}'.encode('utf-8')).decode()
            auth_header = f'Basic {encoded_credentials}'

        self.session = RgdcSession(base_url=api_url, auth_header=auth_header)

    def list_image_entry_tiles(self, image_entry_id: str) -> Dict:
        """List geodata imagery image_entry tiles."""
        r = self.session.get(f'geodata/imagery/{image_entry_id}/tiles')
        r.raise_for_status()

        return r.json()

    def download_image_entry_file(
        self, image_entry_id: str, chunk_size: int = 1024 * 1024
    ) -> Iterator[bytes]:
        """
        Download the associated ImageFile data for this ImageEntry directly from S3.

        Args:
            image_entry_id: The ID of the ImageEntry to download.
            chunk_size: The size (in bytes) of each item in the returned iterator (defaults to 1MB).

        Returns:
            An iterator of byte chunks.
        """
        r = self.session.get(f'geodata/imagery/{image_entry_id}/data', stream=True)
        r.raise_for_status()

        return r.iter_content(chunk_size=chunk_size)

    def download_raster_entry(
        self,
        raster_meta_entry_id: Union[str, int],
        pathname: Optional[str] = None,
        nest_with_name: bool = False,
    ):
        """
        Download the image set associated with a raster entry to disk.

        Args:
            raster_meta_entry_id: The id of the RasterMetaEntry, which is a child to the desired raster entry.
            pathname: The directory to download the image set to. If not supplied, a temporary directory will be used.
            nest_with_name: If True, nests the download within an additional directory, using the raster entry name.

        Returns:
            A dictionary of the paths to all files downloaded under the directory.
        """
        r = self.session.get(f'geodata/imagery/raster/{raster_meta_entry_id}')
        r.raise_for_status()
        parent_raster = r.json().get('parent_raster', {})

        # Create dirs after request to avoid empty dirs if failed
        if pathname is None:
            pathname = tempfile.mkdtemp()

        # Handle optional nesting with raster entry name
        path = Path(pathname)
        parent_raster_name: Optional[str] = parent_raster.get('name')

        if nest_with_name and parent_raster_name:
            path = path / parent_raster_name

        # Ensure base download directory exists
        if not path.exists():
            path.mkdir()

        def download_file_from_url(file):
            filepath = file.get('name')
            file_download_url = file.get('download_url')

            # Skip image if some fields are missing
            if not (file and filepath and file_download_url):
                # TODO: throw a warning to let user know this file failed
                return

            # Parse file path to identifiy nested directories
            filepath: str = filepath.lstrip('/')
            split_filepath: List[str] = filepath.split('/')
            parent_dirname = '/'.join(split_filepath[:-1])
            filename = split_filepath[-1]

            # Create nested directory if necessary
            parent_path = path / parent_dirname if parent_dirname else path
            parent_path.mkdir(parents=True, exist_ok=True)

            # Download contents to file
            file_path = parent_path / filename
            with open(file_path, 'wb') as open_file_path:
                for chunk in iterate_response_bytes(file_download_url):
                    open_file_path.write(chunk)
            return file_path

        images = []
        ancillary = []

        images = parent_raster.get('image_set', {}).get('images', [])
        for image in images:
            file = image.get('image_file', {}).get('file', {})
            file_path = download_file_from_url(file)
            if file_path:
                images.append(file_path)

        ancillary = parent_raster.get('ancillary_files', [])
        for file in ancillary:
            file_path = download_file_from_url(file)
            if file_path:
                ancillary.append(file_path)

        files = {
            'path': path,
            'images': images,
            'ancillary': ancillary,
        }

        return files

    def search(
        self,
        query: Optional[Union[Dict, str]] = None,
        predicate: Optional[SEARCH_PREDICATE_CHOICE] = None,
        relates: Optional[str] = None,
        distance: Optional[Tuple[float, float]] = None,
        acquired: Optional[DATETIME_OR_STR_TUPLE] = None,
        created: Optional[DATETIME_OR_STR_TUPLE] = None,
        modified: Optional[DATETIME_OR_STR_TUPLE] = None,
        datatype: Optional[SEARCH_DATATYPE_CHOICE] = None,
        instrumentation: Optional[str] = None,
        num_bands: Optional[Tuple[int, int]] = None,
        resolution: Optional[Tuple[int, int]] = None,
        cloud_cover: Optional[Tuple[float, float]] = None,
        frame_rate: Optional[Tuple[int, int]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Iterator[Dict]:
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
            created: The min/max date and time (ISO 8601) when data was created.
            modified: The min/max date and time (ISO 8601) when data was modified.
            datatype: The datatype to provide.
            instrumentation: The instrumentation used to acquire at least one of these data.
            num_bands: The min/max number of bands in the raster.
            resolution: The min/max resolution of the raster.
            cloud_cover: The min/max cloud coverage of the raster.
            frame_rate: The min/max frame rate of the video.
            limit: The maximum number of results to return.
            offset: The number of results to skip.

        Returns:
            An iterator of Spatial Entries.
        """
        # The dict that will be used to store params.
        # Initialize with queries that won't be additionally processed.
        params = {
            'predicate': predicate,
            'relates': relates,
            'datatype': datatype,
            'instrumentation': instrumentation,
            'limit': limit,
            'offset': offset,
        }

        if query:
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except JSONDecodeError:
                    pass

            if isinstance(query, dict):
                # Allow failure on invalid format
                query = wkt.dumps(query)

            params['q'] = query

        # Process range params

        if distance and len(distance) == 2:
            dmin, dmax = distance
            params['distance_min'] = dmin
            params['distance_max'] = dmax

        # TODO: Determine if the before/after param order needs to be swapped?
        if acquired and len(acquired) == 2:
            amin, amax = acquired
            params['acquired_before'] = datetime_to_str(amax)
            params['acquired_after'] = datetime_to_str(amin)

        if created and len(created) == 2:
            cmin, cmax = created
            params['created_before'] = datetime_to_str(cmax)
            params['created_after'] = datetime_to_str(cmin)

        if modified and len(modified) == 2:
            mmin, mmax = modified
            params['modified_before'] = datetime_to_str(mmax)
            params['modified_after'] = datetime_to_str(mmin)

        if num_bands and len(num_bands) == 2:
            nbmin, nbmax = num_bands
            params['num_bands_min'] = nbmin
            params['num_bands_max'] = nbmax

        if resolution and len(resolution) == 2:
            rmin, rmax = resolution
            params['resolution_min'] = rmin
            params['resolution_max'] = rmax

        if cloud_cover and len(cloud_cover) == 2:
            ccmin, ccmax = cloud_cover
            params['cloud_cover_min'] = ccmin
            params['cloud_cover_max'] = ccmax

        if frame_rate and len(frame_rate) == 2:
            frmin, frmax = frame_rate
            params['frame_rate_min'] = frmin
            params['frame_rate_max'] = frmax

        return results([self.session.get('geosearch', params=params)])
