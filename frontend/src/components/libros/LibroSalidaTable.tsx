import { LibroTable, type LibroTableProps } from "@/components/libros/LibroTable";

type LibroSalidaTableProps = Omit<LibroTableProps, "emptyMessage">;

export function LibroSalidaTable(props: LibroSalidaTableProps) {
  return (
    <LibroTable
      {...props}
      emptyMessage="No hay salidas registradas para este período."
    />
  );
}
