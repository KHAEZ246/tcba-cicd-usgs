"""
upload_blob.py
Modul integrasi Azure Blob Storage untuk menyimpan hasil batch ingestion dan transformasi data USGS.
Mendukung:
1. Autentikasi Azure Identity / OIDC (DefaultAzureCredential) menggunakan nama Storage Account (AZURE_STORAGE_ACCOUNT).
2. Autentikasi Connection String (AZURE_STORAGE_CONNECTION_STRING).
3. Dry-Run / Mock mode untuk testing lokal atau CI tanpa credential.
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_blob_service_client(
    connection_string: Optional[str] = None,
    storage_account: Optional[str] = None
):
    """
    Menginisialisasi Azure BlobServiceClient menggunakan DefaultAzureCredential (OIDC)
    atau Connection String.
    """
    conn_str = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    account_name = storage_account or os.getenv("AZURE_STORAGE_ACCOUNT")

    # 1. Coba menggunakan Connection String jika disediakan
    if conn_str:
        try:
            from azure.storage.blob import BlobServiceClient
            logger.info("Menggunakan autentikasi Azure via Connection String")
            return BlobServiceClient.from_connection_string(conn_str)
        except Exception as e:
            logger.error("Gagal inisialisasi BlobServiceClient dari connection string: %s", e)

    # 2. Coba menggunakan Azure Identity (DefaultAzureCredential / OIDC)
    if account_name:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobServiceClient
            account_url = f"https://{account_name}.blob.core.windows.net"
            logger.info("Menggunakan autentikasi Azure Identity (OIDC/DefaultAzureCredential) ke: %s", account_url)
            credential = DefaultAzureCredential()
            return BlobServiceClient(account_url=account_url, credential=credential)
        except ImportError:
            logger.warning("Package 'azure-identity' atau 'azure-storage-blob' belum terinstall.")
        except Exception as e:
            logger.error("Gagal inisialisasi BlobServiceClient via DefaultAzureCredential: %s", e)

    logger.warning("Tidak ada credential Azure (AZURE_STORAGE_ACCOUNT / AZURE_STORAGE_CONNECTION_STRING) yang aktif.")
    return None


def upload_file_to_blob(
    local_file_path: str,
    container_name: Optional[str] = None,
    blob_name: Optional[str] = None,
    connection_string: Optional[str] = None,
    storage_account: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mengunggah file lokal ke Azure Blob Storage.
    Jika credentials tidak tersedia, akan berjalan dalam mode DRY-RUN/MOCK
    sehingga tidak mematahkan alur CI/testing pipeline.
    """
    container = (
        container_name
        or os.getenv("AZURE_STORAGE_CONTAINER")
        or os.getenv("AZURE_STORAGE_CONTAINER_NAME", "usgs-data")
    )
    target_blob_name = blob_name or os.path.basename(local_file_path)

    if not os.path.exists(local_file_path):
        raise FileNotFoundError(f"File lokal tidak ditemukan: {local_file_path}")

    client = get_blob_service_client(connection_string, storage_account)

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
        blob_client = client.get_blob_client(container=container, blob=target_blob_name)
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
        logger.warning("Upload via Azure SDK gagal (%s). Mencoba fallback menggunakan Azure CLI...", e)
        account = storage_account or os.getenv("AZURE_STORAGE_ACCOUNT", "tcbacicd")
        try:
            import subprocess
            cmd = [
                "az", "storage", "blob", "upload",
                "--account-name", account,
                "--container-name", container,
                "--file", local_file_path,
                "--name", target_blob_name,
                "--overwrite"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                logger.info("Berhasil mengunggah file via Azure CLI fallback: %s", target_blob_name)
                return {
                    "status": "uploaded_via_cli",
                    "local_file": local_file_path,
                    "container": container,
                    "blob_name": target_blob_name
                }
            else:
                logger.error("Fallback Azure CLI juga gagal:\nSTDOUT: %s\nSTDERR: %s", res.stdout, res.stderr)
        except Exception as cli_err:
            logger.error("Eksekusi fallback Azure CLI mengalami exception: %s", cli_err)

        logger.error("Gagal mengunggah file '%s' ke Azure: %s", local_file_path, e)
        raise e
