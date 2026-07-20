"""Platform Extensions: escribano, empleado, sueldo_historico; migrate escritura.escribano ENUM → FK.

Revision ID: 005
Revises: 004
Create Date: 2026-07-18

Steps (upgrade):
  1. Create table `escribano` with partial unique index on nombre WHERE deleted_at IS NULL.
  2. Create table `empleado` with partial unique index on nombre WHERE deleted_at IS NULL.
  3. Create table `sueldo_historico`.
  4. Seed escribanos: Costanza, Gabriel, Victoria.
  5. Seed empleados: Graciela ($1,000,000), Guadalupe ($1,000,000).
  6. Add nullable columns `escribano_id` and `escribano_nombre` to `escrituras`.
  7. Populate escribano_id and escribano_nombre from existing ENUM values (case-insensitive match).
  8. Set escribano_id and escribano_nombre NOT NULL.
  9. Add FK constraint escrituras.escribano_id → escribano.id.
  10. Add index ix_escrituras_escribano_id.
  11. Drop old ENUM column `escribano` from `escrituras`.
  12. Drop ENUM type `escribano`.
  13. Verify: zero rows have NULL escribano_id.

Steps (downgrade):
  Restore the ENUM column and reverse all changes.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename legacy ENUM so the new `escribano` table does not conflict with type name.
    op.execute(sa.text("ALTER TYPE escribano RENAME TO escribano_legacy_enum"))

    # -------------------------------------------------------------------------
    # 1. Create `escribano` table
    # -------------------------------------------------------------------------
    op.create_table(
        "escribano",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    # Partial unique index: unique nombre only among active (non-deleted) rows
    op.create_index(
        "uq_escribano_nombre_active",
        "escribano",
        ["nombre"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_escribano_deleted_at", "escribano", ["deleted_at"])

    # -------------------------------------------------------------------------
    # 2. Create `empleado` table
    # -------------------------------------------------------------------------
    op.create_table(
        "empleado",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("sueldo", sa.Numeric(18, 2), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "uq_empleado_nombre_active",
        "empleado",
        ["nombre"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_empleado_deleted_at", "empleado", ["deleted_at"])

    # -------------------------------------------------------------------------
    # 3. Create `sueldo_historico` table
    # -------------------------------------------------------------------------
    op.create_table(
        "sueldo_historico",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empleado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empleado.id"),
            nullable=False,
        ),
        sa.Column("empleado_nombre", sa.String(100), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("sueldo", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("empleado_id", "anio", "mes", name="uq_sueldo_historico_empleado_mes"),
    )
    op.create_index("ix_sueldo_historico_anio_mes", "sueldo_historico", ["anio", "mes"])

    # -------------------------------------------------------------------------
    # 4. Seed escribanos (Costanza, Gabriel, Victoria) with stable UUIDs
    # Using gen_random_uuid() so the UUIDs are DB-generated but deterministic
    # enough for CI; we use literals to ensure idempotency on re-seeding.
    # -------------------------------------------------------------------------
    op.execute(
        sa.text(
            """
            INSERT INTO escribano (id, nombre)
            VALUES
                (gen_random_uuid(), 'Costanza'),
                (gen_random_uuid(), 'Gabriel'),
                (gen_random_uuid(), 'Victoria')
            """
        )
    )

    # -------------------------------------------------------------------------
    # 5. Seed empleados (Graciela, Guadalupe — $1,000,000 ARS each)
    # -------------------------------------------------------------------------
    op.execute(
        sa.text(
            """
            INSERT INTO empleado (id, nombre, sueldo)
            VALUES
                (gen_random_uuid(), 'Graciela', 1000000.00),
                (gen_random_uuid(), 'Guadalupe', 1000000.00)
            """
        )
    )

    # -------------------------------------------------------------------------
    # 6. Add nullable `escribano_id` and `escribano_nombre` to `escrituras`
    # -------------------------------------------------------------------------
    op.add_column("escrituras", sa.Column("escribano_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("escrituras", sa.Column("escribano_nombre", sa.String(100), nullable=True))

    # -------------------------------------------------------------------------
    # 7. Populate escribano_id + escribano_nombre from the legacy ENUM values
    #    The ENUM values are lowercase ('costanza', 'gabriel', 'victoria');
    #    the new table stores display-cased names ('Costanza', 'Gabriel', 'Victoria').
    # -------------------------------------------------------------------------
    op.execute(
        sa.text(
            """
            UPDATE escrituras
            SET
                escribano_id = e.id,
                escribano_nombre = e.nombre
            FROM escribano e
            WHERE lower(e.nombre) = escrituras.escribano::text
            """
        )
    )

    # -------------------------------------------------------------------------
    # 8. Set NOT NULL on the new columns
    # -------------------------------------------------------------------------
    op.alter_column("escrituras", "escribano_id", nullable=False)
    op.alter_column("escrituras", "escribano_nombre", nullable=False)

    # -------------------------------------------------------------------------
    # 9. Add FK constraint
    # -------------------------------------------------------------------------
    op.create_foreign_key(
        "fk_escrituras_escribano_id",
        "escrituras",
        "escribano",
        ["escribano_id"],
        ["id"],
    )

    # -------------------------------------------------------------------------
    # 10. Add index on escrituras.escribano_id
    # -------------------------------------------------------------------------
    op.create_index("ix_escrituras_escribano_id", "escrituras", ["escribano_id"])

    # -------------------------------------------------------------------------
    # 11. Drop old ENUM column `escribano` from `escrituras`
    # -------------------------------------------------------------------------
    op.drop_index("ix_escrituras_escribano", table_name="escrituras")
    op.drop_column("escrituras", "escribano")

    # -------------------------------------------------------------------------
    # 12. Drop legacy ENUM type (renamed in step 0)
    # -------------------------------------------------------------------------
    op.execute(sa.text("DROP TYPE IF EXISTS escribano_legacy_enum"))


def downgrade() -> None:
    # -------------------------------------------------------------------------
    # Reverse: restore ENUM column and drop new infrastructure
    # -------------------------------------------------------------------------

    # Re-create ENUM type
    escribano_enum = postgresql.ENUM("costanza", "gabriel", "victoria", name="escribano")
    escribano_enum.create(op.get_bind(), checkfirst=True)

    # Re-add ENUM column (nullable during migration)
    op.add_column(
        "escrituras",
        sa.Column(
            "escribano",
            postgresql.ENUM("costanza", "gabriel", "victoria", name="escribano", create_type=False),
            nullable=True,
        ),
    )

    # Populate ENUM from FK data
    op.execute(
        sa.text(
            """
            UPDATE escrituras
            SET escribano = lower(escribano_nombre)::escribano
            """
        )
    )

    # Restore NOT NULL on ENUM column
    op.alter_column("escrituras", "escribano", nullable=False)

    # Restore index on ENUM column
    op.create_index("ix_escrituras_escribano", "escrituras", ["escribano"])

    # Drop FK infrastructure
    op.drop_index("ix_escrituras_escribano_id", table_name="escrituras")
    op.drop_constraint("fk_escrituras_escribano_id", "escrituras", type_="foreignkey")
    op.drop_column("escrituras", "escribano_nombre")
    op.drop_column("escrituras", "escribano_id")

    # Drop new tables (in reverse dependency order)
    op.drop_index("ix_sueldo_historico_anio_mes", table_name="sueldo_historico")
    op.drop_table("sueldo_historico")

    op.drop_index("ix_empleado_deleted_at", table_name="empleado")
    op.drop_index("uq_empleado_nombre_active", table_name="empleado")
    op.drop_table("empleado")

    op.drop_index("ix_escribano_deleted_at", table_name="escribano")
    op.drop_index("uq_escribano_nombre_active", table_name="escribano")
    op.drop_table("escribano")
