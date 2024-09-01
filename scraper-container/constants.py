rank_map = {
    'IRON': 0,
    'BRONZE': 5,
    'SILVER': 10,
    'GOLD': 15,
    'PLATINUM': 20,
    'EMERALD': 25,
    'DIAMOND': 30,
    'MASTER': 35,
    'GRANDMASTER': 40
}

div_map = {
    'IV': 1,
    'III': 2,
    'II': 3,
    'I': 4
}


def map_rank(rank, div):
    return rank_map[rank] + div_map[div]
