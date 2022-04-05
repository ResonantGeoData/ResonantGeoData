from typing import Union

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
    data_handler : callable
        A callable that will handle converting the data from a ChecksumFile to
        something usable by PyTorch.

    """

    def __init__(
        self, collection: Union[int, str], client: RgdClient, data_handler: callable = None
    ):
        self._client = client
        self._len = None

        if isinstance(collection, int):
            collection = self._client.rgd.get_collection(collection)
        elif isinstance(collection, str):
            collection = self._client.rgd.get_collection_by_name(collection)
        else:
            raise ValueError(f'Collection {collection} not understood.')
        self._collection = collection
        self._callback = data_handler

    def __getitem__(self, index: str):
        item = self._client.rgd.get_collection_item(self._collection, index)
        if self._callback is not None:
            return self._callback(item)
        return item

    def __len__(self):
        if self._len is None:
            self._len = self._client.rgd.get_collection_len(self._collection)['len']
        return self._len

    @property
    def collection(self):
        return self._collection
