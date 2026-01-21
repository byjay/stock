from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    [ISATS Ferrari Strategy Base] 전략 템플릿
    - 모든 진화 전략은 이 클래스를 상속받아야 합니다.
    """
    def __init__(self, dna_genes):
        self.params = dna_genes

    @abstractmethod
    async def execute(self, market_data):
        """실제 매매 로직 구현부"""
        pass

    def update_params(self, new_genes):
        """진화된 유전자로 파라미터 갱신"""
        self.params = new_genes
