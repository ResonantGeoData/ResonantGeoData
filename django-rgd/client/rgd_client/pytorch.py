from typing import Callable, Union

from rgd_client.client import RgdClient
from torch.utils.data import Dataset


class RemoteDataset(Dataset):
    """
    Remote dataset interface for PyTorch.

    Parameters
    ----------
    collection : int, str
        ID of the Collection to source data from (can also be the name of the
        collection).
    client: RgdClient
        The client connected to an RGD instance.
    data_handler : Callable
        A callable that will handle converting the data from a ChecksumFile to
        something usable by PyTorch.

    """

    def __init__(
        self, collection: Union[int, str, dict], client: RgdClient, data_handler: Callable = None
    ):
        self._client = client
        self._collection_identifier = collection
        self._collection = None
        self._callback = data_handler
        # Prefetch collection to make sure valid
        self.collection

    @property
    def collection(self):
        if self._collection is None:
            if isinstance(self._collection_identifier, (int, dict)):
                collection = self._client.rgd.get_collection(self._collection_identifier)
            elif isinstance(self._collection_identifier, str):
                collection = self._client.rgd.get_collection_by_name(self._collection_identifier)
            else:
                raise ValueError(f'Collection {self._collection_identifier} not understood.')
            self._collection = collection
        return self._collection

    def __getitem__(self, index: str):
        item = self._client.rgd.get_collection_item(self.collection, index)
        if self._callback is not None:
            return self._callback(item)
        return item

    def __len__(self):
        return self.collection['len']

    def reset(self):
        """Clear the cached collection metadata."""
        self._collection = None
