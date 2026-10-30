
from flask import Flask, jsonify, render_template, session
from conexion import get_conection
from mysql.connector import IntegrityError
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
ROL_ARRENDATARIO = 2
app = Flask(
    __name__,
    static_folder="frontend"
    )
app.secret_key = "Coding_on_a_different_wavelength"

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/inmueble")
def listar_inmuebles():
    conexion = get_conection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM inmueble")
    inmueble = cursor.fetchall()

    cursor.close()
    conexion.close()

    return jsonify(inmueble)

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
            return redirect(url_for("cuerpo"))   # cambia por la página a la que quieras enviarlo

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


if __name__ == "__main__":
    app.run(debug=True)
