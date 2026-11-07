const lista = document.getElementById("lista");
const vacio = document.getElementById("vacio");
const detalle = document.getElementById("detalle");
const banner = document.getElementById("banner-demo");

let reservas = [];
let filtro = "pendiente";
let seleccionId = null;

const dinero = (n) => "$" + Number(n).toLocaleString("es-CO");

// Las fechas "AAAA-MM-DD" se arman a mano para que no se corran un día por la zona horaria
function fecha(texto) {
  if (!texto) return "—";
  const [a, m, d] = texto.slice(0, 10).split("-");
  return new Date(a, m - 1, d).toLocaleDateString("es-CO", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function dias(inicio, fin) {
  const [a1, m1, d1] = inicio.split("-");
  const [a2, m2, d2] = fin.split("-");
  return Math.round((new Date(a2, m2 - 1, d2) - new Date(a1, m1 - 1, d1)) / 86400000);
}

function el(tag, clase, texto) {
  const nodo = document.createElement(tag);
  if (clase) nodo.className = clase;
  if (texto !== undefined) nodo.textContent = texto;
  return nodo;
}

// ---------- Carga ----------
async function cargar() {
  try {
    const res = await fetch("/api/admin/reservas");
    if (res.status === 403 || res.status === 401) throw new Error("permiso");
    if (!res.ok) throw new Error("servidor");
    reservas = await res.json();
    banner.hidden = true;
  } catch {
    reservas = [];
    banner.hidden = false;
  }
  pintar();
}

// ---------- Lista ----------
function pintar() {
  const cuenta = { pendiente: 0, confirmada: 0, cancelada: 0, todos: reservas.length };
  reservas.forEach((r) => { cuenta[r.estado]++; });
  Object.entries(cuenta).forEach(([k, v]) => {
    document.getElementById("cnt-" + k).textContent = v;
  });

  const visibles = reservas.filter((r) => filtro === "todos" || r.estado === filtro);
  lista.innerHTML = "";
  vacio.hidden = visibles.length > 0;
  vacio.textContent = "No hay reservas en este estado.";

  visibles.forEach((r) => {
    const li = el("li");
    const boton = el("button", "res-item" + (r.id === seleccionId ? " activa" : ""));
    boton.type = "button";

    boton.append(
      el("span", "res-titulo", r.titulo),
      el("span", "res-meta", `${r.nombre} ${r.apellido} · ${fecha(r.fecha_inicio)} → ${fecha(r.fecha_fin)}`),
      el("span", "tag " + r.estado, r.estado)
    );
    boton.addEventListener("click", () => { seleccionId = r.id; pintar(); mostrarDetalle(r); });
    li.appendChild(boton);
    lista.appendChild(li);
  });
}

// ---------- Detalle ----------
function dato(etiqueta, valor) {
  const fila = el("div", "fila-dato");
  fila.append(el("span", "dato-et", etiqueta), el("span", "dato-val", valor));
  return fila;
}

function mostrarDetalle(r) {
  detalle.innerHTML = "";

  const inmueble = el("div", "bloque-detalle");
  inmueble.append(
    el("h2", "", r.titulo),
    dato("Ubicación", `${r.direccion}, ${r.ciudad}`),
    dato("Fechas", `${fecha(r.fecha_inicio)} → ${fecha(r.fecha_fin)} (${dias(r.fecha_inicio, r.fecha_fin)} días)`),
    dato("Estado", r.estado),
    dato("Total", dinero(r.valor_total)),
    dato("Reservada el", fecha(r.fecha_creacion))
  );

  const persona = el("div", "bloque-detalle");
  persona.append(
    el("h3", "", "Quién reservó"),
    dato("Nombre", `${r.nombre} ${r.apellido}`),
    dato("Correo", r.correo),
    dato("Teléfono", r.telefono)
  );

  const pago = el("div", "bloque-detalle");
  pago.appendChild(el("h3", "", "Pago"));
  if (r.monto) {
    pago.append(
      dato("Método", r.metodo_pago),
      dato("Monto", dinero(r.monto)),
      dato("Fecha", fecha(r.fecha_pago))
    );
  } else {
    pago.appendChild(el("p", "", "Sin pago registrado."));
  }

  detalle.append(inmueble, persona, pago);
}

// ---------- Filtros ----------
document.querySelectorAll(".filtro").forEach((boton) => {
  boton.addEventListener("click", () => {
    document.querySelectorAll(".filtro").forEach((b) => b.classList.remove("activo"));
    boton.classList.add("activo");
    filtro = boton.dataset.filtro;
    pintar();
  });
});

cargar();