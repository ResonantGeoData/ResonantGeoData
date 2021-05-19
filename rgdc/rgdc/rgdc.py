from base64 import b64encode
from dataclasses import dataclass
import getpass
from pathlib import Path
import tempfile
from typing import Dict, Iterator, List, Optional, Tuple, Union

from tqdm import tqdm

from .session import RgdcSession
from .types import DATETIME_OR_STR_TUPLE, SEARCH_PREDICATE_CHOICE
from .utils import (
    DEFAULT_RGD_API,
    download_checksum_file_to_path,
    limit_offset_pager,
    spatial_search_params,
    spatial_subentry_id,
)


@dataclass
class RasterDownload:
    path: Path
    images: List[Path]
    ancillary: List[Path]


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
            password: The password associated with the provided username. If None, a prompt will be provided.

        Returns:
            A new Rgdc instance.
        """
        auth_header = None

        # Prompt for password if not provided
        if username is not None and password is None:
            password = getpass.getpass()

        if username and password:
            encoded_credentials = b64encode(f'{username}:{password}'.encode('utf-8')).decode()
            auth_header = f'Basic {encoded_credentials}'

        self.session = RgdcSession(base_url=api_url, auth_header=auth_header)

    def list_image_tiles(self, image_id: Union[str, int]) -> Dict:
        """List geodata imagery tiles."""
        r = self.session.get(f'geoprocess/imagery/{image_id}/tiles')
        return r.json()

    def download_image_file(
        self, image_id: Union[str, int], chunk_size: int = 1024 * 1024
    ) -> Iterator[bytes]:
        """
        Download the associated ImageFile data for this ImageEntry directly from S3.

        Args:
            image_id: The ID of the ImageEntry to download.
            chunk_size: The size (in bytes) of each item in the returned iterator (defaults to 1MB).

        Returns:
            An iterator of byte chunks.
        """
        r = self.session.get(f'geodata/imagery/{image_id}/data', stream=True)
        return r.iter_content(chunk_size=chunk_size)

    def download_image_thumbnail(
        self,
        image_id: Union[str, int],
    ) -> bytes:
        """
        Download the generated thumbnail for this ImageEntry.

        Args:
            image_id: The ID of the ImageEntry to download.

        Returns:
            Thumbnail bytes.
        """
        r = self.session.get(f'geoprocess/imagery/{image_id}/thumbnail')
        return r.content

    def download_raster_thumbnail(
        self,
        raster_meta_id: Union[str, int, dict],
        band: int = 0,
    ) -> bytes:
        """
        Download the generated thumbnail for this ImageEntry.

        Args:
            raster_meta_id: The id of the RasterMetaEntry, which is a child to the desired raster entry, or search result.
            band: The index of the image in the raster's image set to produce thumbnail from.

        Returns:
            Thumbnail bytes.
        """
        if isinstance(raster_meta_id, dict):
            raster_meta_id = spatial_subentry_id(raster_meta_id)

        r = self.session.get(f'geodata/imagery/raster/{raster_meta_id}')
        parent_raster = r.json().get('parent_raster', {})
        images = parent_raster.get('image_set', {}).get('images', [])
        try:
            return self.download_image_thumbnail(images[band]['id'])
        except IndexError:
            raise IndexError(f'Band index ({band}) out of range.')

    def get_raster(self, raster_meta_id: Union[str, int, dict], stac: bool = False) -> Dict:
        """Get raster entry detail.

        Args:
            stac: Optionally return as STAC Item dictionary/JSON.

        Returns:
            Serialized object representation.
        """
        if isinstance(raster_meta_id, dict):
            raster_meta_id = spatial_subentry_id(raster_meta_id)

        if stac:
            r = self.session.get(f'geodata/imagery/raster/{raster_meta_id}/stac')
        else:
            r = self.session.get(f'geodata/imagery/raster/{raster_meta_id}')
        return r.json()

    def download_raster(
        self,
        raster_meta_id: Union[str, int, dict],
        pathname: Optional[str] = None,
        nest_with_name: bool = False,
        keep_existing: bool = True,
    ) -> RasterDownload:
        """
        Download the image set associated with a raster entry to disk.

        Args:
            raster_meta_id: The id of the RasterMetaEntry, which is a child to the desired raster entry, or search result.
            pathname: The directory to download the image set to. If not supplied, a temporary directory will be used.
            nest_with_name: If True, nests the download within an additional directory, using the raster entry name.
            keep_existing: If False, replace files existing on disk. Only valid if `pathname` is given.

        Returns:
            A dictionary of the paths to all files downloaded under the directory.
        """
        if isinstance(raster_meta_id, dict):
            raster_meta_id = spatial_subentry_id(raster_meta_id)

        r = self.session.get(f'geodata/imagery/raster/{raster_meta_id}')
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

        # Initialize dataclass
        raster_download = RasterDownload(path, [], [])

        # Download images
        images = parent_raster.get('image_set', {}).get('images', [])
        for image in tqdm(images, desc='Downloading image files'):
            file = image.get('image_file', {}).get('file', {})
            file_path = download_checksum_file_to_path(file, path, keep_existing=keep_existing)
            if file_path:
                raster_download.images.append(file_path)

        # Download ancillary files
        ancillary = parent_raster.get('ancillary_files', [])
        for file in tqdm(ancillary, desc='Downloading ancillary files'):
            file_path = download_checksum_file_to_path(file, path, keep_existing=keep_existing)
            if file_path:
                raster_download.ancillary.append(file_path)

        return raster_download

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
        )
        return list(limit_offset_pager(self.session, 'geosearch', params=params))

    def search_raster_stac(
        self,
        query: Optional[Union[Dict, str]] = None,
        predicate: Optional[SEARCH_PREDICATE_CHOICE] = None,
        relates: Optional[str] = None,
        distance: Optional[Tuple[float, float]] = None,
        acquired: Optional[DATETIME_OR_STR_TUPLE] = None,
        instrumentation: Optional[str] = None,
        num_bands: Optional[Tuple[int, int]] = None,
        resolution: Optional[Tuple[int, int]] = None,
        cloud_cover: Optional[Tuple[float, float]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict]:
        """
        Search for raster entries based on various criteria.

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
            num_bands: The min/max number of bands in the raster.
            resolution: The min/max resolution of the raster.
            cloud_cover: The min/max cloud coverage of the raster.
            limit: The maximum number of results to return.
            offset: The number of results to skip.

        Returns:
            A list of Spatial Entries in STAC Item format.
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
        )

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

        return list(limit_offset_pager(self.session, 'geosearch/raster', params=params))
