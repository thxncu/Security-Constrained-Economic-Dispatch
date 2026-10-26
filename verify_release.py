"""Verify the SHA-256 manifest without importing third-party packages."""
from pathlib import Path
import hashlib

def verify(root=None):
    root=Path(root or Path(__file__).resolve().parent).resolve()
    manifest=root/'SHA256SUMS.txt'
    if not manifest.is_file():raise FileNotFoundError('SHA256SUMS.txt is missing')
    count=0;seen=set()
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        expected,name=line.split('  ',1)
        target=(root/name).resolve()
        if not target.is_relative_to(root) or name in seen:raise ValueError(f'Unsafe/duplicate entry: {name}')
        seen.add(name)
        if not target.is_file():raise FileNotFoundError(name)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:raise ValueError(f'Checksum mismatch: {name}')
        count+=1
    if count==0:raise ValueError('Empty manifest')
    return count

if __name__=='__main__':
    print(f'PASS: {verify()} manifest files match SHA-256.')
