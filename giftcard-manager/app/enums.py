import enum


class Merchant(str, enum.Enum):
    AMAZON = "amazon"
    BEST_BUY = "best_buy"
    LOWES = "lowes"
    WALMART = "walmart"
    HOME_DEPOT = "home_depot"


class TransactionType(str, enum.Enum):
    ISSUE = "issue"
    RELOAD = "reload"
    REDEEM = "redeem"
    ADJUSTMENT = "adjustment"
