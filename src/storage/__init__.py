"""Storage module for persistent data"""
from .gcs_storage import GCSStorage, get_storage

__all__ = ['GCSStorage', 'get_storage']
