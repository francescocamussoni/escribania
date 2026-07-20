class EscribanoNotFoundError(Exception):
    pass


class EscribanoDuplicateError(Exception):
    pass


class EscribanoHasEscriturasError(Exception):
    def __init__(self, escrituras_count: int) -> None:
        self.escrituras_count = escrituras_count
        super().__init__(
            f"Escribano has {escrituras_count} associated escrituras; "
            "set force=true to deactivate"
        )
