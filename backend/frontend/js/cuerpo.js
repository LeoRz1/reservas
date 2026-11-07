const galeria = document.getElementById("galeriaInmuebles");
const mensajeVacio = document.getElementById("mensajeVacio");
const buscador = document.getElementById("buscarInmueble");
let inmuebles = [];

const formatoPrecio = (n) => "$" + Number(n).toLocaleString("es-CO");

// ---------- Modales ----------
const abrirModal = (id) => document.getElementById(id).classList.add("activo");
const cerrarModal = (id) => document.getElementById(id).classList.remove("activo");

document.getElementById("btnAcerca").addEventListener("click", () => abrirModal("modalAcerca"));
document.getElementById("cerrarAcerca").addEventListener("click", () => cerrarModal("modalAcerca"));
document.getElementById("cerrarDetalles").addEventListener("click", () => cerrarModal("modalDetalles"));

document.querySelectorAll(".modal").forEach((modal) => {
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("activo");
  });
});

document.getElementById("btnInicio").addEventListener("click", () => {
  buscador.value = "";
  mostrar(inmuebles);
});

// ---------- Galería ----------
async function cargarInmuebles() {
  try {
    const res = await fetch("/api/inmuebles");
    if (!res.ok) throw new Error();
    inmuebles = await res.json();   
    mostrar(inmuebles);
  } catch {
    galeria.innerHTML = "";
    mensajeVacio.textContent = "No se pudieron cargar los inmuebles.";
    mensajeVacio.hidden = false;
  }
}

function mostrar(lista) {
  galeria.innerHTML = "";
  mensajeVacio.textContent = "No se encontraron inmuebles.";
  mensajeVacio.hidden = lista.length > 0;

  lista.forEach((i) => {
    const tarjeta = document.createElement("article");
    tarjeta.className = "tarjeta";

    const img = document.createElement("img");
    img.src = i.imagen || "";
    img.alt = i.titulo;
    img.loading = "lazy";

    const titulo = document.createElement("h3");
    titulo.textContent = i.titulo;

    const ubicacion = document.createElement("p");
    ubicacion.textContent = `${i.barrio ? i.barrio + ", " : ""}${i.ciudad}`;

    const precio = document.createElement("p");
    precio.className = "precio";
    precio.textContent = formatoPrecio(i.precio);

    const estado = document.createElement("span");
    estado.className = i.estado ? "etiqueta disponible" : "etiqueta no-disponible";
    estado.textContent = i.estado ? "Disponible" : "No disponible";

    tarjeta.append(img, titulo, ubicacion, precio, estado);
    tarjeta.addEventListener("click", () => abrirDetalles(i));
    galeria.appendChild(tarjeta);
  });
}

// ---------- Detalles ----------
function abrirDetalles(i) {
  document.getElementById("modalImagen").src = i.imagen || "";
  document.getElementById("modalTitulo").textContent = i.titulo;
  document.getElementById("modalTipo").textContent = i.tipo;
  document.getElementById("modalDescripcion").textContent = i.descripcion;
  document.getElementById("modalDireccion").textContent =
    `${i.direccion}${i.barrio ? ", " + i.barrio : ""} - ${i.ciudad}`;
  document.getElementById("modalCaracteristicas").textContent =
    `${i.area} m² · ${i.habitaciones} hab. · ${i.banos} baños · ${i.garajes} garajes`;
  document.getElementById("modalPrecio").textContent = formatoPrecio(i.precio);
  document.getElementById("modalEstado").textContent = i.estado ? "Disponible" : "No disponible";

  document.getElementById("reservaInmuebleId").value = i.id;
  document.getElementById("btnReservar").disabled = !i.estado;
  abrirModal("modalDetalles");
}

// ---------- Búsqueda ----------
buscador.addEventListener("input", () => {
  const texto = buscador.value.trim().toLowerCase();
  mostrar(inmuebles.filter((i) =>
    [i.titulo, i.ciudad, i.barrio, i.direccion, i.tipo]
      .some((campo) => (campo || "").toLowerCase().includes(texto))
  ));
});

// ---------- Reserva ----------
const hoy = new Date().toISOString().split("T")[0];
document.getElementById("fecha_inicio").min = hoy;
document.getElementById("fecha_fin").min = hoy;

document.getElementById("formReserva").addEventListener("submit", async (e) => {
  e.preventDefault();
  const res = await fetch("/api/reservas", { method: "POST", body: new FormData(e.target) });

  let data = {};
  try { data = await res.json(); } catch {}

  if (res.ok) {
    e.target.reset();
    cerrarModal("modalDetalles");
    document.getElementById("pagoReservaId").value = data.reserva_id;
    document.getElementById("pagoTotal").textContent = formatoPrecio(data.valor_total);
    abrirModal("modalPago");
  } else if (res.status === 401) {
    window.location.href = "/login";
  } else {
    alert(data.error || "Error al reservar");
  }
});

// ---------- Pago ----------
document.getElementById("cerrarPago").addEventListener("click", () => cerrarModal("modalPago"));

document.getElementById("formPago").addEventListener("submit", async (e) => {
  e.preventDefault();
  const res = await fetch("/api/pagos", { method: "POST", body: new FormData(e.target) });

  let data = {};
  try { data = await res.json(); } catch {}

  if (res.ok) {
    alert("Pago registrado. Reserva confirmada.");
    e.target.reset();
    cerrarModal("modalPago");
    window.location.href = "/cuerpo";
  } else if (res.status === 401) {
    window.location.href = "/login";
  } else {
    alert(data.error || "Error al pagar");
  }
});

document.getElementById("btnCancelarReserva").addEventListener("click", async () => {
  const id = document.getElementById("pagoReservaId").value;
  const res = await fetch(`/api/reservas/${id}/cancelar`, { method: "POST" });
  if (res.ok) {
    cerrarModal("modalPago");
    window.location.href = "/cuerpo";
  } else {
    alert("No se pudo cancelar");
  }
});

cargarInmuebles();