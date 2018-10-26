import traceback
import logging

from celery import shared_task
from redis_store import redis
from django.db import transaction

from .models import Book
from .extractor import csv, xlsx


logger = logging.getLogger(__name__)


def _tabular_extract_book(book):
    if book.file_type == Book.CSV:
        csv.extract(book)
    if book.file_type == Book.XLSX:
        xlsx.extract(book)
    return True


def _tabular_meta_extract_book(book):
    if book.file_type == Book.XLSX:
        xlsx.extract_meta(book)
    return True


@shared_task
def tabular_extract_book(book_id):
    key = 'tabular_extract_book_{}'.format(book_id)
    lock = redis.get_lock(key, 60 * 60 * 24)  # Lock lifetime 24 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    book = Book.objects.get(id=book_id)
    try:
        with transaction.atomic():
            return_value = _tabular_extract_book(book)
        book.status = Book.SUCCESS
    except Exception:
        logger.error(traceback.format_exc())
        book.status = Book.FAILED
        book.error = Book.UNKNOWN_ERROR  # TODO: handle all type of error
        return_value = False

    book.save()

    lock.release()
    return return_value


@shared_task
def tabular_meta_extract_book(book_id):
    key = 'tabular_meta_extract_book_{}'.format(book_id)
    lock = redis.get_lock(key, 60 * 60 * 24)  # Lock lifetime 24 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    book = Book.objects.get(id=book_id)
    try:
        with transaction.atomic():
            return_value = _tabular_meta_extract_book(book)
        book.meta_status = Book.SUCCESS
    except Exception:
        logger.error(traceback.format_exc())
        book.meta_status = Book.FAILED
        book.error = Book.UNKNOWN_ERROR  # TODO: handle all type of error
        return_value = False

    book.save()

    lock.release()
    return return_value
