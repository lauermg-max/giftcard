class GiftCardError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class GiftCardNotFound(GiftCardError):
    def __init__(self, detail: str = "Gift card not found"):
        super().__init__(detail, status_code=404)


class GiftCardInactive(GiftCardError):
    def __init__(self, detail: str = "Gift card is inactive"):
        super().__init__(detail, status_code=400)


class GiftCardExpired(GiftCardError):
    def __init__(self, detail: str = "Gift card has expired"):
        super().__init__(detail, status_code=400)


class GiftCardInsufficientFunds(GiftCardError):
    def __init__(self, detail: str = "Gift card has insufficient balance"):
        super().__init__(detail, status_code=400)


class GiftCardDuplicateCode(GiftCardError):
    def __init__(self, detail: str = "Gift card code already exists"):
        super().__init__(detail, status_code=409)


class GiftCardCodeGenerationError(GiftCardError):
    def __init__(self, detail: str = "Unable to generate a unique gift card code"):
        super().__init__(detail, status_code=500)
