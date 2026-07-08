"""
VORTEX index builder — creates sentence-level FAISS index from chunks.

Usage:
    python scripts/build_index.py \
        --chunks data/chunks.json \
        --output data/index \
        --model sentence-transformers/all-MiniLM-L6-v2 \
        --device cpu

Requires: pip install sentence-transformers faiss-cpu
"""

import argparse
import json
import os
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def load_chunks(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "chunks" in data:
        return data["chunks"]
    raise ValueError(f"Cannot parse chunks from {path}")


def main():
    parser = argparse.ArgumentParser(description="VORTEX index builder")
    parser.add_argument("--chunks", required=True, help="Path to chunks JSON")
    parser.add_argument("--output", default="data/index", help="Output directory")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model name")
    parser.add_argument("--device", default="cpu", help="Device: cpu or cuda")
    args = parser.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: Install sentence-transformers: pip install sentence-transformers")
        sys.exit(1)

    try:
        import numpy as np
        import faiss
    except ImportError:
        print("ERROR: Install faiss: pip install faiss-cpu")
        sys.exit(1)

    print(f"Loading chunks from {args.chunks}...")
    chunks = load_chunks(args.chunks)
    print(f"  {len(chunks)} chunks loaded")

    texts = [c.get("text", c.get("content", "")) for c in chunks]
    chunk_ids = [c.get("id", c.get("chunk_id", str(i))) for i, c in enumerate(chunks)]

    print(f"Loading model: {args.model} on {args.device}...")
    model = SentenceTransformer(args.model, device=args.device)

    print("Encoding sentences...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    dim = embeddings.shape[1]
    print(f"  {len(embeddings)} embeddings, dim={dim}")

    print("Building FAISS index...")
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    os.makedirs(args.output, exist_ok=True)

    index_path = os.path.join(args.output, "index.faiss")
    faiss.write_index(index, index_path)
    print(f"  Index: {index_path}")

    meta = {
        "chunk_ids": chunk_ids,
        "dim": dim,
        "count": len(chunks),
        "model": args.model,
    }
    meta_path = os.path.join(args.output, "meta.pkl")
    with open(meta_path, "wb") as f:
        pickle.dump(meta, f)
    print(f"  Meta:  {meta_path}")

    print("Done.")


if __name__ == "__main__":
    main()
