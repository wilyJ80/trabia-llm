from ingest.loader import Loader
from ingest.models import CPMIDocPage

def test_loader():
    filepath: str = 'data/relatorio-cpmi-versao-consolidada_231017_100010.pdf'
    loader: Loader = Loader()
    content: list[CPMIDocPage] = loader.load(filepath)
    assert content is not None
    assert isinstance(content, list)
    assert all(isinstance(page, CPMIDocPage) for page in content)
    assert len(content) > 0
    print(content)
