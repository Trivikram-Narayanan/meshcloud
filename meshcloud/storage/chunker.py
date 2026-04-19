import hashlib
import os

CHUNK_SIZE = 4 * 1024 * 1024  # 4MB


def split_file(filepath, outdir):
    chunks = []

    with open(filepath, "rb") as f:
        while True:
            data = f.read(CHUNK_SIZE)

            if not data:
                break

            # Content Addressing: Use SHA256 of content as filename (CID)
            cid = hashlib.sha256(data).hexdigest()
            chunk_path = os.path.join(outdir, cid)

            # Deduplication: Only write if chunk doesn't exist
            if not os.path.exists(chunk_path):
                with open(chunk_path, "wb") as c:
                    c.write(data)

            chunks.append(cid)

    return chunks
