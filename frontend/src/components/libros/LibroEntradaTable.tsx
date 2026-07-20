import { LibroTable, type LibroTableProps } from "@/components/libros/LibroTable";

type LibroEntradaTableProps = Omit<LibroTableProps, "emptyMessage">;

export function LibroEntradaTable(props: LibroEntradaTableProps) {
  return (
    <LibroTable
      {...props}
      emptyMessage="No hay entradas registradas para este período."
    />
  );
}
