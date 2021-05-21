from django.urls import path

from . import api, views

urlpatterns = [
    # Pages
    path(r'', views.SpatialEntriesListView.as_view(), name='index'),
    path(
        'geodata/spatial_entries/<int:pk>/',
        views.spatial_entry_redirect_view,
        name='spatial-entry-detail',
    ),
    path(
        'geodata/raster/<int:pk>/',
        views.RasterEntryDetailView.as_view(),
        name='raster-entry-detail',
    ),
    path(
        'geodata/fmv/<int:pk>/',
        views.FMVEntryDetailView.as_view(),
        name='fmv-entry-detail',
    ),
    path(
        'geodata/geometry/<int:pk>/',
        views.GeometryEntryDetailView.as_view(),
        name='geometry-entry-detail',
    ),
    path(
        'geodata/point_cloud/<int:pk>/',
        views.PointCloudEntryDetailView.as_view(),
        name='point-cloud-entry-detail',
    ),
    #############
    # Search
    path('api/geosearch/near_point', api.search.search_near_point),
    path('api/geosearch/raster/near_point', api.search.search_near_point_raster),
    path('api/geosearch/geometry/near_point', api.search.search_near_point_geometry),
    path('api/geosearch/near_point/extent', api.search.search_near_point_extent),
    path('api/geosearch/raster/near_point/extent', api.search.search_near_point_extent_raster),
    path('api/geosearch/geometry/near_point/extent', api.search.search_near_point_extent_geometry),
    path('api/geosearch/bounding_box', api.search.search_bounding_box),
    path('api/geosearch/raster/bounding_box', api.search.search_bounding_box_raster),
    path('api/geosearch/geometry/bounding_box', api.search.search_bounding_box_geometry),
    path('api/geosearch/bounding_box/extent', api.search.search_bounding_box_extent),
    path('api/geosearch/raster/bounding_box/extent', api.search.search_bounding_box_extent_raster),
    path(
        'api/geosearch/geometry/bounding_box/extent', api.search.search_bounding_box_extent_geometry
    ),
    path('api/geosearch/geojson', api.search.search_geojson),
    path('api/geosearch/raster/geojson', api.search.search_geojson_raster),
    path('api/geosearch/geometry/geojson', api.search.search_geojson_geometry),
    path('api/geosearch/geojson/extent', api.search.search_geojson_extent),
    path('api/geosearch/raster/geojson/extent', api.search.search_geojson_extent_raster),
    path('api/geosearch/geometry/geojson/extent', api.search.search_geojson_extent_geometry),
    path('api/geosearch', api.search.SearchSpatialEntryView.as_view()),
    #############
    # Other
    path(
        'api/geodata/status/<model>/<int:pk>',
        api.download.get_status,
        name='get-status',
    ),
    path(
        'api/geodata/common/spatial_entry/<int:spatial_id>',
        api.get.GetSpatialEntry.as_view(),
        name='spatial-entry',
    ),
    path(
        'api/geodata/common/checksum_file/<int:pk>',
        api.get.GetChecksumFile.as_view(),
        name='checksum-file',
    ),
    path(
        'api/geodata/common/checksum_file/<int:pk>/data',
        api.download.download_checksum_file,
        name='checksum-file-data',
    ),
    path(
        'api/geodata/geometry/<int:pk>',
        api.get.GetGeometryEntry.as_view(),
        name='geometry-entry',
    ),
    path(
        'api/geodata/geometry/<int:pk>/data',
        api.get.GetGeometryEntryData.as_view(),
        name='geometry-entry-data',
    ),
    path(
        'api/geodata/imagery/<int:pk>',
        api.get.GetImageEntry.as_view(),
        name='image-entry',
    ),
    path(
        'api/geodata/imagery/<int:pk>/data',
        api.download.download_image_entry_file,
        name='image-entry-data',
    ),
    path(
        'api/geodata/imagery/image_set/<int:pk>',
        api.get.GetImageSet.as_view(),
        name='image-set',
    ),
    path(
        'api/geodata/imagery/raster/<int:pk>',
        api.get.GetRasterMetaEntry.as_view(),
        name='raster-meta-entry',
    ),
    path(
        'api/geodata/imagery/raster/<int:pk>/stac',
        api.get.GetRasterMetaEntrySTAC.as_view(),
        name='raster-meta-entry-stac',
    ),
    path(
        'api/geodata/fmv/<int:pk>',
        api.get.GetFMVEntry.as_view(),
        name='fmv-entry',
    ),
    path(
        'api/geodata/fmv/<int:pk>/data',
        api.get.GetFMVDataEntry.as_view(),
        name='fmv-entry-data',
    ),
    path(
        'api/geodata/point_cloud/<int:pk>',
        api.get.GetPointCloudEntry.as_view(),
        name='point-cloud-entry',
    ),
    path(
        'api/geodata/point_cloud/<int:pk>/base64',
        api.get.GetPointCloudEntryData.as_view(),
        name='point-cloud-entry-data',
    ),
    #############
    # Geoprocessing
    path(
        'api/geoprocess/imagery/<int:pk>/tiles',
        api.tiles.TileMetadataView.as_view(),
        name='image-tile-metadata',
    ),
    path(
        'api/geoprocess/imagery/<int:pk>/tiles/<int:z>/<int:x>/<int:y>.png',
        api.tiles.TileView.as_view(),
        name='image-tiles',
    ),
    path(
        'api/geoprocess/imagery/<int:pk>/thumbnail',
        api.tiles.TileThumnailView.as_view(),
        name='image-thumbnail',
    ),
    path('api/geoprocess/imagery/cog', api.post.CreateConvertedImageFile.as_view()),
    path(
        'api/geoprocess/imagery/cog/<int:pk>',
        api.get.GetConvertedImageStatus.as_view(),
        name='cog',
    ),
    path(
        'api/geoprocess/imagery/cog/<int:pk>/data',
        api.download.download_cog_file,
        name='cog-data',
    ),
    path(
        'api/geoprocess/imagery/subsample',
        api.post.CreateSubsampledImage.as_view(),
    ),
    path(
        'api/geoprocess/imagery/subsample/<int:pk>',
        api.get.GetSubsampledImage.as_view(),
        name='subsampled',
    ),
    path(
        'api/geoprocess/imagery/subsample/<int:pk>/status',
        api.download.get_status_subsampled_image,
        name='subsampled-status',
    ),
]
