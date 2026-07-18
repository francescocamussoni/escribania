#!/usr/bin/env python3
"""Demo interactivo del motor de cálculo (sin base de datos)."""

from decimal import Decimal

from services.calculo_factura import calcular_factura_completa, canonical_config


def fmt(value: Decimal) -> str:
    return f"${value:,.2f}"


def main() -> None:
    config = canonical_config()

    # Fixture canónico de la constitución
    usd = Decimal("105000.00")
    dolar_mep = Decimal("1450.34")
    dolar_nacion = Decimal("1425.00")

    print("=" * 60)
    print("  Motor de cálculo — Contaduría Escribanía")
    print("  Fixture canónico (constitution.md §5)")
    print("=" * 60)
    print(f"  USD valor escritura : {fmt(usd)}")
    print(f"  Dólar MEP           : {fmt(dolar_mep)}")
    print(f"  Dólar Nación        : {fmt(dolar_nacion)}")
    print("-" * 60)

    r = calcular_factura_completa(usd, dolar_mep, dolar_nacion, config)

    print(f"  Monto base (MEP)    : {fmt(r['monto_base_mep'])}")
    print(f"  Precio base (Nación): {fmt(r['precio_base_nacion'])}")
    print("-" * 60)
    print("  HONORARIOS")
    print(f"    Honorario principal : {fmt(r['honorario_principal'])}")
    print(f"    Certificación       : {fmt(r['certificacion'])}")
    print(f"    Suma hon + cert     : {fmt(r['suma_hon_cert'])}")
    print(f"    Subtotal honorarios : {fmt(r['subtotal_honorarios'])}")
    print("-" * 60)
    print("  LEYES NOTARIALES")
    print(f"    Total               : {fmt(r['total_leyes_notariales'])}")
    print("-" * 60)
    print("  IMPUESTOS")
    print(f"    Sellos              : {fmt(r['sellos'])}")
    print(f"    Total               : {fmt(r['total_impuestos'])}")
    print("-" * 60)
    print("  GASTOS ADMIN")
    print(f"    Total               : {fmt(r['total_gastos_admin'])}")
    print("=" * 60)
    print(f"  TOTAL FACTURA       : {fmt(r['total_factura'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
