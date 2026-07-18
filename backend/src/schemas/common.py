from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

MoneyStr = Annotated[Decimal, PlainSerializer(lambda v: format(v, "f"), return_type=str)]
