
class Define:
    PLACE_HOLDER = b"\xFF\xFF\xFF\xFF"
    ADDRESS_LENGTH = 23
    HASH_LENGTH = 34
    RECID_MIN = 0
    RECID_MAX = 3
    RECID_UNCOMPR = 27
    LEN_COMPACT_SIG = 65
    NETWORKS = {
        1: 'NULS',
        2: 'tNULS'
    }
    MESSAGE_TEMPLATE = b"\x18NULS Signed Message:\n%b"
    COIN_UNIT = 100000000
    CHEAP_UNIT_FEE = 100000
    UNIT_FEE = 1000000
    KB = 1024
    CONTRACT_MINIMUM_PRICE = 25
    

