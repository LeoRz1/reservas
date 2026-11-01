
from flask import Flask, jsonify, render_template, session
from datetime import date
import os, uuid
from conexion import get_conection
from mysql.connector import IntegrityError
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
ROL_ARRENDATARIO = 2
METODOS_PAGO = {"tarjeta", "transferencia", "efectivo"}

app = Flask(
    __name__,
    static_folder="frontend"
    )
app.secret_key = "Coding_on_a_different_wavelength"

UPLOAD_DIR = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
EXT_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}
CIUDAD_ID = 1   
TIPO_ID = 1     

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/api/inmuebles", methods=["GET"])
def api_inmuebles():
    conn = get_conection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT i.id, i.titulo, i.descripcion, i.precio, i.area, i.habitaciones,
               i.banos, i.garajes, i.estado,
               t.nombre AS tipo,
               l.direccion, l.barrio, c.nombre AS ciudad,
               f.ruta AS imagen
        FROM inmueble i
        JOIN locacion l ON l.id = i.locacion_id
        JOIN ciudad c ON c.id = l.ciudad_id
        JOIN tipo_inmueble t ON t.id = i.tipo_inmueble_id
        LEFT JOIN propiedad_foto f ON f.inmueble_id = i.id AND f.principal = 1
        ORDER BY i.fecha_publicacion DESC
    """)
    filas = cur.fetchall()
    cur.close()
    conn.close()

    for fila in filas:
        fila["precio"] = float(fila["precio"])
        fila["area"] = float(fila["area"])

    return jsonify(filas)








@app.route("/api/inmuebles", methods=["POST"])
def crear_inmueble():
    if "usuario_id" not in session:
        return jsonify({"error": "Debes iniciar sesión"}), 401

    f = request.form
    try:
        titulo       = f["titulo"].strip()
        descripcion  = f["descripcion"].strip()
        precio       = float(f["precio"])
        area         = float(f["area"])
        habitaciones = int(f["habitaciones"])
        banos        = int(f["banos"])
        garajes      = int(f["garajes"])
        tipo_id      = int(f["tipo_inmueble_id"])
        ciudad_id    = int(f["ciudad_id"])
        barrio       = f.get("barrio", "").strip() or None
        direccion    = f["direccion"].strip()
        complemento  = f.get("complemento", "").strip() or None
        estado       = 1 if f.get("disponibilidad") == "true" else 0
    except (KeyError, ValueError):
        return jsonify({"error": "Datos incompletos o inválidos"}), 400

    if precio <= 0 or area <= 0:
        return jsonify({"error": "Precio y área deben ser mayores a 0"}), 400

    foto = request.files.get("imagen")
    if not foto or "." not in foto.filename:
        return jsonify({"error": "Falta la imagen"}), 400

    ext = foto.filename.rsplit(".", 1)[-1].lower()
    if ext not in EXT_PERMITIDAS:
        return jsonify({"error": "Formato de imagen no permitido"}), 400

    nombre_archivo = f"{uuid.uuid4().hex}.{ext}"
    ruta_disco = os.path.join(UPLOAD_DIR, nombre_archivo)

    conn = get_conection()
    try:
        cur = conn.cursor()

        cur.execute(
            """INSERT INTO locacion (ciudad_id, barrio, direccion, complemento)
               VALUES (%s, %s, %s, %s)""",
            (ciudad_id, barrio, direccion, complemento),
        )
        locacion_id = cur.lastrowid

        cur.execute(
            """INSERT INTO inmueble
               (titulo, descripcion, precio, area, habitaciones, banos, garajes,
                estado, locacion_id, tipo_inmueble_id, usuario_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (titulo, descripcion, precio, area, habitaciones, banos, garajes,
             estado, locacion_id, tipo_id, session["usuario_id"]),
        )
        inmueble_id = cur.lastrowid

        foto.save(ruta_disco)
        cur.execute(
            """INSERT INTO propiedad_foto
               (inmueble_id, nombre_original, ruta, tipo_mime, tamano_bytes, orden, principal)
               VALUES (%s, %s, %s, %s, %s, 0, 1)""",
            (inmueble_id, foto.filename, f"/frontend/uploads/{nombre_archivo}",
             foto.mimetype, os.path.getsize(ruta_disco)),
        )

        conn.commit()
        return jsonify({"ok": True, "id": inmueble_id}), 201

    except Exception as e:
        conn.rollback()
        if os.path.exists(ruta_disco):
            os.remove(ruta_disco)
        print("ERROR crear_inmueble:", e)
        return jsonify({"error": "No se pudo guardar"}), 500
    finally:
        conn.close()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        contrasena = request.form["contrasena"]

        conn = get_conection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuario WHERE correo = %s", (correo,))
        usuario = cur.fetchone()
        cur.close()
        conn.close()

        if usuario and check_password_hash(usuario["contrasena_HASH"], contrasena):
            session["usuario_id"] = usuario["id"]
            session["rol_id"] = usuario["rol_id"]
            return redirect(url_for("cuerpo"))   

        flash("Correo o contraseña incorrectos.", "error")

    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        cedula     = request.form["cedula"].strip()
        nombre     = request.form["nombre"].strip()
        apellido   = request.form["apellido"].strip()
        telefono   = "57" + request.form["telefono"].strip()
        correo     = request.form["correo"].strip().lower()
        contrasena = request.form["contrasena"]

        if contrasena != request.form["confirmar"]:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("registro.html")

        conn = get_conection()
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO usuario
                   (cedula_ciudadania, nombre, apellido, correo,
                    contrasena_HASH, telefono, rol_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (cedula, nombre, apellido, correo,
                 generate_password_hash(contrasena), telefono, ROL_ARRENDATARIO),
            )
            conn.commit()
        except IntegrityError:
            flash("Cédula o correo ya registrados.", "error")
            return render_template("registro.html")
        finally:
            conn.close()

        return redirect(url_for("login")) 
    
    return render_template("registro.html")

@app.route("/cuerpo")
def cuerpo():
    return render_template("cuerpo.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/publicar")
def publicar():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conn = get_conection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nombre FROM tipo_inmueble ORDER BY nombre")
    tipos = cur.fetchall()
    cur.execute("SELECT id, nombre, departamento FROM ciudad ORDER BY nombre")
    ciudades = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("publicar.html", tipos=tipos, ciudades=ciudades)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/reservas", methods=["POST"])
def crear_reserva():
    if "usuario_id" not in session:
        return jsonify({"error": "Debes iniciar sesión"}), 401

    try:
        id_inmueble = int(request.form["id_inmueble"])
        inicio = date.fromisoformat(request.form["fecha_inicio"])
        fin = date.fromisoformat(request.form["fecha_fin"])
    except (KeyError, ValueError):
        return jsonify({"error": "Datos incompletos o inválidos"}), 400

    if inicio < date.today():
        return jsonify({"error": "La fecha de inicio no puede ser pasada"}), 400
    if fin <= inicio:
        return jsonify({"error": "La fecha de fin debe ser posterior a la de inicio"}), 400

    conn = get_conection()
    try:
        cur = conn.cursor(dictionary=True)

        # Bloquea la fila del inmueble para evitar dos reservas simultáneas
        cur.execute(
            "SELECT precio, estado, usuario_id FROM inmueble WHERE id = %s FOR UPDATE",
            (id_inmueble,),
        )
        inmueble = cur.fetchone()
        if not inmueble:
            conn.rollback()
            return jsonify({"error": "El inmueble no existe"}), 404
        if not inmueble["estado"]:
            conn.rollback()
            return jsonify({"error": "El inmueble no está disponible"}), 400
        if inmueble["usuario_id"] == session["usuario_id"]:
            conn.rollback()
            return jsonify({"error": "No puedes reservar tu propio inmueble"}), 400

        # ¿Se cruza con otra reserva activa?
        cur.execute(
            """SELECT id FROM informacion_reserva
               WHERE id_inmueble = %s AND estado <> 'cancelada'
                 AND fecha_inicio < %s AND fecha_fin > %s""",
            (id_inmueble, fin, inicio),
        )
        if cur.fetchone():
            conn.rollback()
            return jsonify({"error": "Esas fechas ya están reservadas"}), 409

        # El total lo calcula el servidor (precio mensual / 30 * días)
        dias = (fin - inicio).days
        valor_total = round(float(inmueble["precio"]) / 30 * dias, 2)

        cur.execute(
            """INSERT INTO informacion_reserva
               (id_usuario, id_inmueble, fecha_inicio, fecha_fin, estado, valor_total)
               VALUES (%s, %s, %s, %s, 'pendiente', %s)""",
            (session["usuario_id"], id_inmueble, inicio, fin, valor_total),
        )
        reserva_id = cur.lastrowid
        conn.commit()
        return jsonify({"ok": True, "reserva_id": reserva_id, "valor_total": valor_total}), 201

    except Exception as e:
        conn.rollback()
        print("ERROR crear_reserva:", e)
        return jsonify({"error": "No se pudo crear la reserva"}), 500
    finally:
        conn.close()




@app.route("/api/pagos", methods=["POST"])
def crear_pago():
    if "usuario_id" not in session:
        return jsonify({"error": "Debes iniciar sesión"}), 401

    try:
        id_reserva = int(request.form["id_reserva"])
    except (KeyError, ValueError):
        return jsonify({"error": "Reserva inválida"}), 400

    metodo = request.form.get("metodo_pago", "")
    if metodo not in METODOS_PAGO:
        return jsonify({"error": "Elige un método de pago"}), 400

    conn = get_conection()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """SELECT id_usuario, estado, valor_total
               FROM informacion_reserva WHERE id = %s FOR UPDATE""",
            (id_reserva,),
        )
        reserva = cur.fetchone()

        if not reserva or reserva["id_usuario"] != session["usuario_id"]:
            conn.rollback()
            return jsonify({"error": "La reserva no existe"}), 404
        if reserva["estado"] != "pendiente":
            conn.rollback()
            return jsonify({"error": "Esta reserva ya no está pendiente"}), 400

        cur.execute("SELECT id FROM pago WHERE id_informacion_reserva = %s", (id_reserva,))
        if cur.fetchone():
            conn.rollback()
            return jsonify({"error": "Esta reserva ya tiene un pago"}), 409

        # El monto sale de la base de datos, nunca del navegador
        cur.execute(
            """INSERT INTO pago (monto, metodo_pago, id_informacion_reserva)
               VALUES (%s, %s, %s)""",
            (reserva["valor_total"], metodo, id_reserva),
        )
        cur.execute(
            "UPDATE informacion_reserva SET estado = 'confirmada' WHERE id = %s",
            (id_reserva,),
        )
        conn.commit()
        return jsonify({"ok": True}), 201

    except Exception as e:
        conn.rollback()
        print("ERROR crear_pago:", e)
        return jsonify({"error": "No se pudo registrar el pago"}), 500
    finally:
        conn.close()


@app.route("/api/reservas/<int:id_reserva>/cancelar", methods=["POST"])
def cancelar_reserva(id_reserva):
    if "usuario_id" not in session:
        return jsonify({"error": "Debes iniciar sesión"}), 401

    conn = get_conection()
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE informacion_reserva SET estado = 'cancelada'
               WHERE id = %s AND id_usuario = %s AND estado = 'pendiente'""",
            (id_reserva, session["usuario_id"]),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "No se pudo cancelar"}), 404
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()




        


if __name__ == "__main__":
    app.run(debug=True)
