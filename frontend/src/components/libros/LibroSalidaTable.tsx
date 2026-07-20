import { LibroTable, type LibroTableProps } from "@/components/libros/LibroTable";

type LibroSalidaTableProps = Omit<LibroTableProps, "emptyMessage">;

export function LibroSalidaTable(props: LibroSalidaTableProps) {
  return (
    <LibroTable
      {...props}
      emptyMessage="No hay pagos al Colegio registrados en este período."
    />
  );
}
