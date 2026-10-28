"""Immutable source ZIP artifact adapter for MVP; source registry owns authorization."""
import hashlib
import re

ARTIFACT_ID = re.compile(r'^([A-Za-z0-9][A-Za-z0-9._-]{0,63})@([A-Za-z0-9][A-Za-z0-9._-]{0,63})$')


def resolve(registry, owner_id, artifact_id):
    match = ARTIFACT_ID.fullmatch(artifact_id)
    if not match:
        raise ValueError('Invalid artifact id: expected source_id@source_version')
    source = registry.get_source(owner_id=owner_id, source_id=match[1], source_version=match[2])
    data = source['source_bytes']
    digest = hashlib.sha256(data).hexdigest()
    if digest != source['source_hash']:
        raise ValueError('Artifact digest mismatch')
    return {'artifact_id': artifact_id, 'artifact_hash': 'sha256:' + digest,
            'entrypoint': source['entrypoint'], 'size_bytes': len(data)}, data
