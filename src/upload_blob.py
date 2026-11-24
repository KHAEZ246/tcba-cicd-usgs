"""
upload_blob.py
Modul integrasi Azure Blob Storage untuk menyimpan hasil batch ingestion dan transformasi data USGS.
Mendukung mode riil (Azure SDK) dan mode Dry-Run/Mock untuk keperluan testing dan CI/CD.
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_blob_service_client(connection_string: Optional[str] = None):
    """
    Menginisialisasi Azure BlobServiceClient menggunakan connection string.
    Jika azure-storage-blob tidak terinstall atau connection string kosong, mengembalikan None.
    """
    conn_str = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        logger.warning("AZURE_STORAGE_CONNECTION_STRING tidak diset.")
        return None

    try:
        from azure.storage.blob import BlobServiceClient
        client = BlobServiceClient.from_connection_string(conn_str)
        return client
    except ImportError:
        logger.warning("Package 'azure-storage-blob' belum terinstall.")
        return None
    except Exception as e:
        logger.error("Gagal menginisialisasi BlobServiceClient: %s", e)
        return None


def upload_file_to_blob(
    local_file_path: str,
    container_name: Optional[str] = None,
    blob_name: Optional[str] = None,
    connection_string: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mengunggah file lokal ke Azure Blob Storage.
    Jika credentials tidak tersedia, akan berjalan dalam mode DRY-RUN/MOCK
    sehingga tidak mematahkan alur CI/testing pipeline.
    """
    container = container_name or os.getenv("AZURE_STORAGE_CONTAINER_NAME", "usgs-earthquake")
    target_blob_name = blob_name or os.path.basename(local_file_path)

    if not os.path.exists(local_file_path):
        raise FileNotFoundError(f"File lokal tidak ditemukan: {local_file_path}")

    client = get_blob_service_client(connection_string)

    if client is None:
        logger.info(
            "[DRY-RUN / MOCK] Upload ke Azure Blob Storage disimulasikan: '%s' -> Container '%s', Blob '%s'",
            local_file_path, container, target_blob_name
        )
        return {
            "status": "simulated",
            "local_file": local_file_path,
            "container": container,
            "blob_name": target_blob_name,
            "url": f"https://mockstorageaccount.blob.core.windows.net/{container}/{target_blob_name}"
        }

    try:
        container_client = client.get_container_client(container)
        if not container_client.exists():
            logger.info("Membuat container baru: %s", container)
            container_client.create_container()

        blob_client = container_client.get_blob_client(target_blob_name)
        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        logger.info("Berhasil mengunggah file ke Azure: %s", blob_client.url)
        return {
            "status": "uploaded",
            "local_file": local_file_path,
            "container": container,
            "blob_name": target_blob_name,
            "url": blob_client.url
        }
    except Exception as e:
        logger.error("Gagal mengunggah file '%s' ke Azure: %s", local_file_path, e)
        raise e
