import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_empleados(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/configuracion/empleados")
    assert response.status_code == 200
    names = {row["nombre"] for row in response.json()}
    assert {"Graciela", "Guadalupe"}.issubset(names)


@pytest.mark.asyncio
async def test_create_empleado(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/configuracion/empleados",
        json={"nombre": "Nuevo Empleado", "sueldo": "1500000.00"},
    )
    assert response.status_code == 201
    assert response.json()["nombre"] == "Nuevo Empleado"


@pytest.mark.asyncio
async def test_patch_sueldo(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/configuracion/empleados",
        json={"nombre": "Patch Sueldo", "sueldo": "1000000.00"},
    )
    empleado_id = created.json()["id"]

    response = await auth_client.patch(
        f"/api/v1/configuracion/empleados/{empleado_id}",
        json={"sueldo": "1200000.00"},
    )
    assert response.status_code == 200
    assert response.json()["sueldo"] == "1200000.00"


@pytest.mark.asyncio
async def test_patch_invalid_sueldo_returns_422(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/configuracion/empleados",
        json={"nombre": "Invalid Sueldo", "sueldo": "1000.00"},
    )
    empleado_id = created.json()["id"]

    response = await auth_client.patch(
        f"/api/v1/configuracion/empleados/{empleado_id}",
        json={"sueldo": "0"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_empleado_returns_204(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/configuracion/empleados",
        json={"nombre": "Delete Emp", "sueldo": "1000.00"},
    )
    empleado_id = created.json()["id"]

    response = await auth_client.delete(f"/api/v1/configuracion/empleados/{empleado_id}")
    assert response.status_code == 204
