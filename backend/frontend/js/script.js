
async function cargarInmuebles() {
    try {
        const respuesta = await fetch("/inmueble");
        const datos = await respuesta.json();

        console.log(datos);
    } catch (error) {
        console.error("Error al cargar inmuebles:", error);
    }
}

cargarInmuebles();
