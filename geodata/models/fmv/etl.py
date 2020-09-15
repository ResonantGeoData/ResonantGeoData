import os
import re
import shlex
import shutil
import subprocess
import tempfile

from celery.utils.log import get_task_logger
from django.contrib.gis.geos import MultiPoint, MultiPolygon, Point, Polygon
import docker
import numpy as np

from rgd.utility import _field_file_to_local_path

from .base import FMVEntry, FMVFile

logger = get_task_logger(__name__)


def _extract_klv_with_docker(fmv_file_entry, entry):
    logger.info('Entered `_extract_klv_with_docker`')
    image_name = 'banesullivan/kwiver:dump-klv'
    video_file = fmv_file_entry.file
    try:
        client = docker.from_env(version='auto', timeout=3600)
        _ = client.images.pull(image_name)

        with _field_file_to_local_path(video_file) as dataset_path:
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
                fmv_file_entry.failure_reason = None
            except subprocess.CalledProcessError as exc:
                result = exc.returncode
                logger.info('Failed to successfully run image (%r)' % (exc))
                fmv_file_entry.failure_reason = 'Return code: %s\nException:\n%r' % (result, exc)
            logger.info('Finished running image with result %r' % result)
            # Store result
            entry.klv_file.save('%s.klv' % os.path.basename(dataset_path), open(output_path, 'rb'))
            # entry.log.save(
            #     '%s_log.dat' % os.path.basename(dataset_path), open(stderr_path, 'rb')
            # )
            entry.save(
                update_fields=[
                    'klv_file',
                ]
            )
            shutil.rmtree(tmpdir)
    except Exception as exc:
        logger.exception('Internal error running dump-klv')
        try:
            fmv_file_entry.failure_reason = exc.args[0]
        except Exception:
            pass
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

    locations = {}
    for i, f in enumerate(frames):
        try:
            s = _get_spatial_ref_of_frame(f)
        except IndexError:
            # s = "No data"
            continue
        locations[i + 1] = s

    path = []
    polys = []
    union = None
    for meta in locations.values():
        sensor, bbox, srid = meta

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

    return points, polys, union


def _convert_video_to_mp4(fmv_entry):
    video_file = fmv_entry.fmv_file.file
    with _field_file_to_local_path(video_file) as dataset_path:
        logger.info('Converting video file: %s' % (dataset_path))
        tmpdir = tempfile.mkdtemp()
        output_path = os.path.join(tmpdir, os.path.basename(dataset_path) + '.mp4')

        cmd = [
            'ffmpeg',
            '-i',
            str(dataset_path),
            '-c',
            'copy',
            '-an',
            output_path,
        ]
        logger.info('Running {}'.format(cmd))
        try:
            subprocess.check_call(cmd)
            result = 0
            # Store result
            fmv_entry.web_video_file.save('%s.mp4' % os.path.basename(dataset_path), open(output_path, 'rb'))
        except subprocess.CalledProcessError as exc:
            result = exc.returncode
            logger.info('Failed to successfully convert video (%r)' % (exc))
        logger.info('Finished running video conversion: %r' % result)


def read_fmv_file(fmv_file_id):
    fmv_file = FMVFile.objects.filter(id=fmv_file_id).first()

    # create a model entry for that shapefile
    entry_query = FMVEntry.objects.filter(fmv_file=fmv_file_id)
    if len(entry_query) < 1:
        entry = FMVEntry()
        # geometry_entry.creator = archive.creator
        entry.name = fmv_file.name
        entry.fmv_file = fmv_file
        entry.save()
    elif len(entry_query) == 1:
        entry = entry_query.first()
    else:
        # This should never happen because it is a foreign key
        raise RuntimeError('multiple FMV entries found for this file.')  # pragma: no cover

    # Only extraxt the KLV data if it does not exist or the checksum of the video has changed
    if not entry.klv_file or not fmv_file.validate():
        _extract_klv_with_docker(fmv_file, entry)

    with _field_file_to_local_path(entry.klv_file) as file_path:
        with open(file_path, 'r') as f:
            content = f.read()

    if not content:
        raise Exception('FLV file not created')

    # The returned `footprints` can have thoousands of Polygons which will not render well
    #   for now we just ignore those. If there is a need, we can use later.
    #   FYI: those footprints do not correspond to all frames, i.e. some are missing
    path, _, union = _get_path_and_footprints(content)

    entry.ground_frame = union
    entry.flight_path = path

    entry.outline = union.envelope
    entry.footprint = union.convex_hull

    _convert_video_to_mp4(entry)

    entry.save()

    return
