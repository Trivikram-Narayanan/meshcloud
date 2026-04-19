import os


def assemble(chunk_hashes, chunk_dir, output):
    with open(output, "wb") as out:
        for cid in chunk_hashes:
            chunk_path = os.path.join(chunk_dir, cid)
            if not os.path.exists(chunk_path):
                raise FileNotFoundError(f"Chunk missing: {cid}")

            with open(chunk_path, "rb") as f:
                out.write(f.read())
