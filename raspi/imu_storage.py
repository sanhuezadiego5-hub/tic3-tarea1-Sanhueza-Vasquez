"""Versioned binary capture files; sample records keep the wire's !IIhhh layout."""
import hashlib
import json
from pathlib import Path
import struct

from imu_protocol import FIELDS, RECORD

MAGIC = b'TIC3BIN\x01'
PREFIX = struct.Struct('!8sI')
ARRAYS = {'sample_seq', 'read_us', 'values', '_raw_records'}
IDENTITY_FIELDS = tuple(k for k in FIELDS if k not in {
    'magic', 'version', 'type', 'fragment_index', 'fragment_count',
    'sample_offset', 'fragment_samples', 'payload_bytes', 'crc32'})


def records(block):
    raw = block.get('_raw_records')
    if raw is None:
        raw = b''.join(RECORD.pack(seq, timestamp - block['window_start_us'],
                                  *block['values'][3*i:3*i+3])
                       for i, (seq, timestamp) in enumerate(zip(block['sample_seq'], block['read_us'])))
    if len(raw) != block['sample_count'] * RECORD.size:
        raise ValueError('invalid stored sample count')
    return raw


def fingerprint(block):
    """Encoding-independent identity, also usable with historical JSON captures."""
    header = {k: block[k] for k in IDENTITY_FIELDS}
    return hashlib.sha256(json.dumps(header, sort_keys=True, separators=(',', ':')).encode()
                          + records(block)).hexdigest()


def encode_block(block):
    metadata = {k: v for k, v in block.items() if k not in ARRAYS}
    header = json.dumps(metadata, separators=(',', ':'), allow_nan=False).encode()
    content = PREFIX.pack(MAGIC, len(header)) + header + records(block)
    return content + hashlib.sha256(content).digest()


def load_block(path):
    """Read a .bin or historical .json block into the same analysis structure."""
    path = Path(path)
    if path.suffix == '.json':
        return json.loads(path.read_text())
    content = path.read_bytes()
    if len(content) < PREFIX.size + 32:
        raise ValueError('truncated binary capture')
    magic, length = PREFIX.unpack_from(content)
    if magic != MAGIC or length > len(content) - PREFIX.size - 32:
        raise ValueError('invalid binary capture header')
    if hashlib.sha256(content[:-32]).digest() != content[-32:]:
        raise ValueError('binary capture checksum mismatch')
    block = json.loads(content[PREFIX.size:PREFIX.size + length])
    raw = content[PREFIX.size + length:-32]
    if block['sample_count'] * RECORD.size != len(raw):
        raise ValueError('invalid binary capture length')
    rows = list(RECORD.iter_unpack(raw))
    block.update(sample_seq=[r[0] for r in rows],
                 read_us=[block['window_start_us'] + r[1] for r in rows],
                 values=[v for r in rows for v in r[2:]])
    if fingerprint(block) != block['sha256']:
        raise ValueError('binary capture identity mismatch')
    return block
