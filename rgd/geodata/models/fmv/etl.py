import os
import re
import shlex
import shutil
import subprocess
import tempfile

from celery.utils.log import get_task_logger
from django.contrib.gis.geos import MultiPoint, MultiPolygon, Point, Polygon
import docker
from girder_utils.files import field_file_to_local_path
import numpy as np

from .base import FMVEntry, FMVFile

logger = get_task_logger(__name__)


def _extract_klv_with_docker(fmv_file_entry):
    logger.info('Entered `_extract_klv_with_docker`')
    image_name = 'banesullivan/kwiver:dump-klv'
    video_file = fmv_file_entry.file
    try:
        client = docker.from_env(version='auto', timeout=3600)
        _ = client.images.pull(image_name)

        with field_file_to_local_path(video_file) as dataset_path:
            logger.info('Running dump-klv with data %s' % (dataset_path))
            tmpdir = tempfile.mkdtemp()
            output_path = os.path.join(tmpdir, os.path.basename(dataset_path) + '.klv')
            stderr_path = os.path.join(tmpdir, 'stderr.dat')
            cmd = [
                'docker',
                'run',
                '--rm',
                '-i',
                image_name,
            ]
            logger.info(
                'Running %s <%s >%s 2>%s'
                % (
                    ' '.join([shlex.quote(c) for c in cmd]),
                    shlex.quote(str(dataset_path)),
                    shlex.quote(output_path),
                    shlex.quote(stderr_path),
                )
            )
            try:
                subprocess.check_call(
                    cmd,
                    stdin=open(dataset_path, 'rb'),
                    stdout=open(output_path, 'wb'),
                    stderr=open(stderr_path, 'wb'),
                )
                result = 0
            except subprocess.CalledProcessError as exc:
                result = exc.returncode
                logger.info('Failed to successfully run image (%r)' % (exc))
                raise exc
            logger.info('Finished running image with result %r' % result)
            # Store result
            fmv_file_entry.klv_file.save(
                '%s.klv' % os.path.basename(dataset_path), open(output_path, 'rb')
            )
            # entry.log.save(
            #     '%s_log.dat' % os.path.basename(dataset_path), open(stderr_path, 'rb')
            # )
            fmv_file_entry.save(
                update_fields=[
                    'klv_file',
                ]
            )
            shutil.rmtree(tmpdir)
    except Exception as exc:
        logger.exception('Internal error running dump-klv')
        raise exc
    return


def _get_spatial_ref_of_frame(frame):
    """Get the sensor location and bounding box footprint for the given frame."""
    meta_regex = re.compile(r'---------------- Metadata from: (.+)')
    idxs = [m.start() for m in re.finditer(meta_regex, frame)]
    if len(idxs) > 1:
        meta_block = [frame[idxs[i] : idxs[i + 1]] for i in range(len(idxs) - 1)][-1]
    else:
        meta_block = frame[idxs[0] : :]

    # Sensor Geodetic Location
    loc_regex = re.compile(
        r'Metadata item: Sensor Geodetic Location (.+): geo_point.\[(.+)\] @ (\d+) (.+)'
    )
    _, loc, srida, _ = re.findall(loc_regex, meta_block)[0]

    # Corner points
    corners_regex = re.compile(r'Metadata item: Corner points (.+): {(.+)} @ (\d+)')
    _, corners, sridb = re.findall(corners_regex, meta_block)[0]

    # make usable
    srida = int(srida)
    sridb = int(sridb)
    if srida != sridb:
        raise ValueError()

    path = np.array([float(s) for s in loc.split(',')])
    bbox = np.array([float(v) for c in corners.split(',') for v in c.split('/')]).reshape((-1, 2))

    return path, bbox, srida


def _get_path_and_footprints(content):
    """Get the flight path and all footprints for entire video."""
    frame_regex = re.compile(r'========== Read frame (\d+) \(index (\d+)\) ==========')
    idxs = [m.start() for m in re.finditer(frame_regex, content)]
    frames = [content[idxs[i] : idxs[i + 1]] for i in range(len(idxs) - 1)]
    nf = [int(c[0]) for c in re.findall(frame_regex, content)]

    assert len(nf[:-1]) == len(frames)

    path = []
    polys = []
    union = None
    frame_numbers = []
    for i, f in enumerate(frames):
        try:
            sensor, bbox, srid = _get_spatial_ref_of_frame(f)
        except IndexError:
            # No data for that frame
            continue

        frame_numbers.append(nf[i])

        point = Point(*sensor[:2], srid=srid)
        path.append(point)

        box = np.insert(bbox, 0, bbox[-1], axis=0)
        p = Polygon(box, srid=srid)
        polys.append(p)
        if union is None:
            # Ony on first
            union = p
        else:
            union = union.union(p)

    logger.info('Created ({}) Polygons '.format(len(polys)))

    polys = MultiPolygon(polys)
    points = MultiPoint(path)

    if isinstance(union, Polygon):
        union = MultiPolygon(
            [
                union,
            ]
        )

    return points, polys, union, frame_numbers


def _get_frame_rate_of_video(file_path):
    import cv2  # NOTE: in project depends from kwcoco

    cap = cv2.VideoCapture(os.path.abspath(file_path))
    return cap.get(cv2.CAP_PROP_FPS)


def _convert_video_to_mp4(fmv_file_entry):
    video_file = fmv_file_entry.file
    with field_file_to_local_path(video_file) as dataset_path:
        logger.info('Converting video file: %s' % (dataset_path))
        tmpdir = tempfile.mkdtemp()
        output_path = os.path.join(tmpdir, os.path.basename(dataset_path) + '.mp4')

        cmd = [
            'ffmpeg',
            '-i',
            str(dataset_path),
            '-map_metadata',
            '-1',
            '-vcodec',
            'libx264',
            '-level',
            '30',
            '-maxrate',
            '1024k',
            '-movflags',
            'faststart',
            '-g',
            '15',
            '-an',
            output_path,
        ]
        logger.info('Running {}'.format(cmd))
        try:
            subprocess.check_call(cmd)
            result = 0
            # Store result
            fmv_file_entry.web_video_file.save(
                '%s.mp4' % os.path.basename(dataset_path), open(output_path, 'rb')
            )
            fmv_file_entry.frame_rate = _get_frame_rate_of_video(dataset_path)
            fmv_file_entry.save()
        except subprocess.CalledProcessError as exc:
            result = exc.returncode
            logger.info('Failed to successfully convert video (%r)' % (exc))
        logger.info('Finished running video conversion: %r' % result)


def _populate_fmv_entry(entry):
    # Open in text mode
    with entry.fmv_file.klv_file.open() as file_obj:
        content = file_obj.read().decode('utf-8')

    if not content:
        raise Exception('FLV file not created')

    # The returned `footprints` can have thoousands of Polygons which will not render well
    #   for now we just ignore those. If there is a need, we can use later.
    #   FYI: those footprints do not correspond to all frames, i.e. some are missing
    path, polys, union, nf = _get_path_and_footprints(content)

    entry.ground_frames = polys
    entry.ground_union = union
    entry.flight_path = path
    entry.frame_numbers = entry._array_to_blob(nf)

    entry.outline = union.envelope
    entry.footprint = union.convex_hull

    entry.save()
    return True


def read_fmv_file(fmv_file_id):
    fmv_file = FMVFile.objects.filter(id=fmv_file_id).first()

    validation = fmv_file.validate()
    # Only extraxt the KLV data if it does not exist or the checksum of the video has changed
    if not fmv_file.klv_file or not validation:
        _extract_klv_with_docker(fmv_file)
    if not fmv_file.web_video_file or not validation:
        _convert_video_to_mp4(fmv_file)

    # create a model entry for that shapefile
    entry_query = FMVEntry.objects.filter(fmv_file=fmv_file_id)
    if len(entry_query) < 1:
        entry = FMVEntry()
        # geometry_entry.creator = archive.creator
        entry.name = fmv_file.name
        entry.fmv_file = fmv_file
    elif len(entry_query) == 1:
        entry = entry_query.first()
    else:
        # This should never happen because it is a foreign key
        raise RuntimeError('multiple FMV entries found for this file.')  # pragma: no cover

    _populate_fmv_entry(entry)
    entry.save()

    return
