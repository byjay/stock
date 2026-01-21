import random

def get_sector_map(symbols):
    """
    Groups symbols into logical sectors/themes.
    In a real system, this would load from a CSV or KIS API.
    """
    sectors = ["AI_CHIPS", "BLOCKCHAIN", "QUANT_TECH", "EV_FUTURE", "PHARMA_BIO", "DEFENSE"]
    sector_map = {}
    for sym in symbols:
        sector_map[sym] = random.choice(sectors)
    return sector_map
