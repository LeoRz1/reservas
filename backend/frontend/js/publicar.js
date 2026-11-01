const form = document.getElementById("formInmueble");
const mensajeError = document.getElementById("mensajeError");
const boton = form.querySelector(".btn-guardar");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  mensajeError.hidden = true;
  boton.disabled = true;

  try {
    const res = await fetch("/api/inmuebles", { method: "POST", body: new FormData(form) });

    if (res.ok) {
      window.location.href = "/cuerpo";
      return;
    }

    if (res.status === 401) {
      window.location.href = "/login";
      return;
    }

    let texto = "Error al publicar";
    try { texto = (await res.json()).error || texto; } catch {}
    mensajeError.textContent = texto;
  } catch {
    mensajeError.textContent = "No se pudo conectar con el servidor.";
  }

  mensajeError.hidden = false;
  boton.disabled = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
});