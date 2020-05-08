from celery import shared_task
from celery.utils.log import get_task_logger
from contextlib import contextmanager
from django.core.files import File
from django.db.models.fields.files import FieldFile
import docker
import os
from pathlib import Path, PurePath
import shutil
from storages.backends.s3boto3 import S3Boto3StorageFile
import subprocess
import tempfile
import time
from typing import Generator

from .models import AlgorithmJob, AlgorithmResult, ScoreJob, ScoreResult
# enum for result type
from enum import Enum

logger = get_task_logger(__name__)


@contextmanager
def _field_file_to_local_path(field_file: FieldFile) -> Generator[Path, None, None]:
    with field_file.open('rb'):
        file_obj: File = field_file.file

        if isinstance(file_obj, S3Boto3StorageFile):
            field_file_basename = PurePath(field_file.name).name
            with tempfile.NamedTemporaryFile('wb', suffix=field_file_basename) as dest_stream:
                shutil.copyfileobj(file_obj, dest_stream)
                dest_stream.flush()

                yield Path(dest_stream.name)
        else:
            yield Path(file_obj.name)


def _run_algorithm(algorithm_job):
    algorithm_file: FieldFile = algorithm_job.algorithm.data
    dataset_file: FieldFile = algorithm_job.dataset.data
    try:
        with _field_file_to_local_path(algorithm_file) as algorithm_path, \
                _field_file_to_local_path(dataset_file) as dataset_path:
            client = docker.from_env(version='auto', timeout=3600)
            image = None
            if algorithm_job.algorithm.docker_image_id:
                try:
                    image = client.images.get(algorithm_job.algorithm.docker_image_id)
                    logger.info('Loaded existing docker image %r' % algorithm_job.algorithm.docker_image_id)
                except docker.errors.ImageNotFound:
                    pass
            if not image:
                logger.info('Loading docker image %s' % algorithm_path)
                image = client.images.load(open(algorithm_path, 'rb'))
                if len(image) != 1:
                    raise Exception('tar file contains more than one image')
                image = image[0]
                algorithm_job.algorithm.docker_image_id = image.attrs['Id']
                algorithm_job.algorithm.save(update_fields=['docker_image_id'])
                logger.info('Loaded docker image %r' % algorithm_job.algorithm.docker_image_id)
            logger.info('Running image %s with data %s' % (algorithm_path, dataset_path))
            tmpdir = tempfile.mkdtemp()
            output_path = os.path.join(tmpdir, 'output.dat')
            stderr_path = os.path.join(tmpdir, 'stderr.dat')
            try:
                subprocess.check_call(
                    ['docker', 'run', '--rm', '-i', '--name',
                     'algorithm_job_%s_%s' % (algorithm_job.id, time.time()),
                     str(algorithm_job.algorithm.docker_image_id)],
                    stdin=open(dataset_path, 'rb'),
                    stdout=open(output_path, 'wb'),
                    stderr=open(stderr_path, 'wb'))
                result = 0
                algorithm_job.fail_reason = None
            except subprocess.CalledProcessError as exc:
                result = exc.returncode
                logger.info('Failed to successfully run image %s (%r)' % (algorithm_path, exc))
                algorithm_job.fail_reason = 'Return code: %s\nException:\n%r' % (result, exc)
            logger.info('Finished running image with result %r' % result)
            # Store result
            algorithm_result = AlgorithmResult(
                algorithm_job=algorithm_job)
            algorithm_result.data.save(
                'algorithm_job_%s.dat' % algorithm_job.id, open(output_path, 'rb'))
            algorithm_result.log.save(
                'algorithm_job_%s_log.dat' % algorithm_job.id, open(stderr_path, 'rb'))
            algorithm_result.save()
            shutil.rmtree(tmpdir)
            algorithm_job.status = AlgorithmJob.Status.SUCCEEDED if not result else AlgorithmJob.Status.FAILED
    except Exception as exc:
        logger.exception(f'Internal error run algorithm {algorithm_job.id}: {exc}')
        algorithm_job.status = AlgorithmJob.Status.INTERNAL_FAILURE
        try:
            algorithm_job.fail_reason = exc.args[0]
        except Exception:
            pass
    return algorithm_job


@shared_task(time_limit=86400)
def run_algorithm(algorithm_job_id, dry_run=False):
    algorithm_job = AlgorithmJob.objects.get(pk=algorithm_job_id)
    if not dry_run:
        algorithm_job.status = AlgorithmJob.Status.RUNNING
        algorithm_job.save(update_fields=['status'])
    algorithm_job = _run_algorithm(algorithm_job)
    if not dry_run:
        algorithm_job.save()
        # Notify


def _run_scoring(score_job):
    score_algorithm_file: FieldFile = score_job.score_algorithm.data
    algorithm_result_file: FieldFile = score_job.algorithm_result.data
    groundtruth_file: FieldFile = score_job.groundtruth.data
    try:
        with _field_file_to_local_path(score_algorithm_file) as score_algorithm_path, \
                _field_file_to_local_path(algorithm_result_file) as algorithm_result_path, \
                _field_file_to_local_path(groundtruth_file) as groundtruth_path:
            client = docker.from_env(version='auto', timeout=3600)
            image = None
            if score_job.score_algorithm.docker_image_id:
                try:
                    image = client.images.get(score_job.score_algorithm.docker_image_id)
                    logger.info('Loaded existing docker image %r' % score_job.score_algorithm.docker_image_id)
                except docker.errors.ImageNotFound:
                    pass
            if not image:
                logger.info('Loading docker image %s' % score_algorithm_path)
                image = client.images.load(open(score_algorithm_path, 'rb'))
                if len(image) != 1:
                    raise Exception('tar file contains more than one image')
                image = image[0]
                score_job.score_algorithm.docker_image_id = image.attrs['Id']
                score_job.score_algorithm.save(update_fields=['docker_image_id'])
                logger.info('Loaded docker image %r' % score_job.score_algorithm.docker_image_id)
            logger.info('Running image %s with groundtruth %s and results %s' % (
                score_algorithm_path, groundtruth_path, algorithm_result_path))
            tmpdir = tempfile.mkdtemp()
            output_path = os.path.join(tmpdir, 'output.dat')
            stderr_path = os.path.join(tmpdir, 'stderr.dat')
            try:
                subprocess.check_call(
                    ['docker', 'run', '--rm', '-i', '--name',
                     'score_job_%s_%s' % (score_job.id, time.time()),
                     '-v', '%s:%s:ro' % (groundtruth_path, '/groundtruth.dat'),
                     str(score_job.score_algorithm.docker_image_id)],
                    stdin=open(algorithm_result_path, 'rb'),
                    stdout=open(output_path, 'wb'),
                    stderr=open(stderr_path, 'wb'))
                result = 0
                score_job.fail_reason = None
            except subprocess.CalledProcessError as exc:
                result = exc.returncode
                logger.info('Failed to successfully run image %s (%r)' % (score_algorithm_path, exc))
                score_job.fail_reason = 'Return code: %s\nException:\n%r' % (result, exc)
            logger.info('Finished running image with result %r' % result)
            score_result = ScoreResult(
                score_job=score_job)
            score_result.data.save(
                'score_job_%s.dat' % score_job.id, open(output_path, 'rb'))
            score_result.log.save(
                'score_job_%s_log.dat' % score_job.id, open(stderr_path, 'rb'))
            score_result.overall_score, score_result.result_type = _overall_score_and_result_type(score_result.data)
            # score_result.overall_score = float(0.92)
            # score_result.result_type = 'SIMPLE'
            score_result.save()
            shutil.rmtree(tmpdir)
            score_job.status = ScoreJob.Status.SUCCEEDED if not result else ScoreJob.Status.FAILED
    except Exception as exc:
        logger.exception(f'Internal error run score_algorithm {score_job.id}: {exc}')
        score_job.status = ScoreJob.Status.INTERNAL_FAILURE
        try:
            score_job.fail_reason = exc.args[0]
        except Exception:
            pass
    return score_job


@shared_task(time_limit=86400)
def run_scoring(score_job_id, dry_run=False):
    score_job = ScoreJob.objects.get(pk=score_job_id)
    if not dry_run:
        score_job.status = ScoreJob.Status.RUNNING
        score_job.save(update_fields=['status'])
    score_job = _run_scoring(score_job)
    if not dry_run:
        score_job.save()
        # Notify

def _overall_score_and_result_type(datafile):
    # In the future, inspect the data to determine the result type.  For now, just extract a float from the data file
    result_type = ScoreResult.ResultType.SIMPLE
    # overall_score = float([line.strip() for line in datafile][0])
    overall_score = float(datafile.readline())
    # float([line.strip() for line in score_result.data][0]
    # result_type = 'SIMPLE'
    # overall_score = float(0.90)
    return overall_score, result_type
