# rgdc - ResonantGeoDataClient

The **rgdc** Python package allows users to make web requests to a ResonantGeoData instance within a Python script.

# Usage
```
from rgdc import Rgdc

client = Rgdc(username='yourusername', password='yourpassword')

# Get image entry tile metadata
tile_metadata = client.list_image_entry_tiles("image_entry_id")

# Download ImageFile data from an ImageEntry
file_bytes = client.download_image_entry_file("202")
with open('./download.tif', 'wb') as write_file:
    while True:
        chunk = next(file_bytes, None)
        if chunk is None:
            break

        write_file.write(chunk)
```
