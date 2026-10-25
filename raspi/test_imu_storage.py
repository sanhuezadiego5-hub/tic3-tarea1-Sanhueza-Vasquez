import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from imu_protocol import Reassembler, TCPFrames, decode_packet
from imu_server import BlockStore
from imu_storage import load_block, fingerprint


class StorageTests(unittest.TestCase):
    def block(self, encoding='binary'):
        name = 'TIC3_WIRE_FIXTURE' if encoding == 'binary' else 'TIC3_JSON_FIXTURE'
        source = Path(os.environ[name]).read_bytes()
        decoder, frames = TCPFrames(), []
        for offset in range(0, len(source), 4096):
            frames.extend(decoder.feed(source[offset:offset + 4096]))
        assembler = Reassembler(keep_raw=True)
        for packet in frames:
            h, _ = decode_packet(packet)
            if h['type'] == 2 and h['window_seq'] == 0 and h['stream'] == 0:
                result = assembler.push(packet)
                if result:
                    return result
        self.fail('missing fixture block')

    def test_roundtrip_size_integrity_and_conflicting_replay(self):
        original = self.block()
        with tempfile.TemporaryDirectory() as folder:
            store = BlockStore(folder)
            path, created = store.save(original, 'tcp', 'binary')
            self.assertTrue(created)
            recovered = load_block(path)
            for field in ('values', 'sample_seq', 'read_us', 'sample_count', 'range', 'sample_hz'):
                self.assertEqual(recovered[field], original[field])
            self.assertEqual(fingerprint(recovered), fingerprint(original))
            self.assertLess(path.stat().st_size, len(json.dumps(recovered, separators=(',', ':')).encode()))
            changed = dict(original, values=list(original['values']))
            changed.pop('_raw_records')
            changed['values'][0] += 1
            with self.assertRaisesRegex(ValueError, 'conflicting replay'):
                BlockStore(folder).save(changed, 'tcp', 'binary')
            content = path.read_bytes()
            damaged = bytearray(content)
            damaged[-33] ^= 1
            path.write_bytes(damaged)
            with self.assertRaisesRegex(ValueError, 'checksum'):
                load_block(path)
            path.write_bytes(content[:10])
            with self.assertRaisesRegex(ValueError, 'truncated'):
                load_block(path)

    def test_json_storage_and_replay_from_other_encoding(self):
        with tempfile.TemporaryDirectory() as folder:
            path, _ = BlockStore(folder).save(self.block('json'), 'udp', 'json')
            self.assertEqual(path.suffix, '.json')
            recovered = load_block(path)
            self.assertEqual(recovered['values'], self.block()['values'])
            replay, created = BlockStore(folder).save(self.block(), 'tcp', 'binary')
            self.assertEqual(replay, path)
            self.assertFalse(created)
            self.assertFalse(list(Path(folder).rglob('*.bin')))

    def test_historical_json_without_new_digest_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            path, _ = BlockStore(folder).save(self.block('json'), 'tcp', 'json')
            old = load_block(path)
            old['sha256'] = 'historical-json-digest'
            path.write_text(json.dumps(old))
            _, created = BlockStore(folder).save(self.block(), 'tcp', 'binary')
            self.assertFalse(created)

    def test_disk_failure_does_not_commit_block(self):
        with tempfile.TemporaryDirectory() as folder:
            store = BlockStore(folder)
            with patch('imu_server.os.fsync', side_effect=OSError('disk failure')):
                with self.assertRaisesRegex(OSError, 'disk failure'):
                    store.save(self.block(), 'tcp', 'binary')
            self.assertEqual(store.blocks, 0)
            self.assertFalse(list(Path(folder).rglob('window-*')))
            path, created = store.save(self.block(), 'tcp', 'binary')
            self.assertTrue(created)
            self.assertEqual(load_block(path)['sample_count'], 400)


if __name__ == '__main__':
    unittest.main()
