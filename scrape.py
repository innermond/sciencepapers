from urllib.parse import urlparse

def domain(url: str, ld=2) -> str:
    d = urlparse(url).netloc
    d = d.split('.')
    if len(d) > ld:
        d = d[-ld:]
    d = '.'.join(d)
    return d.strip()

