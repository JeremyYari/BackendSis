from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://jeremy:RWxpWIwEz7Dl76dXBSkSWymmbqGCIxH0@dpg-cqbibfggph6c73c0t1vg-a.oregon-postgres.render.com/sisvitasavdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)

# Definición de modelos
class Usuario(db.Model):
    __tablename__ = 'usuario'
    usuario_id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    apellidos = db.Column(db.String(255), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    tipo_usuario = db.Column(db.Integer, nullable=False)  # Add this line
    login = db.relationship('Login', backref='usuario', uselist=False)
    resultados = db.relationship('ResultadoTest', backref='usuario', lazy=True)
    coordenadas = db.Column(db.String(255))

class Login(db.Model):
    __tablename__ = 'login'
    login_id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(255), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.usuario_id'), nullable=False, unique=True)

class Pregunta(db.Model):
    __tablename__ = 'pregunta'
    pregunta_id = db.Column(db.Integer, primary_key=True)
    pregunta = db.Column(db.Text, nullable=False)

class Respuesta(db.Model):
    __tablename__ = 'respuesta'
    respuesta_id = db.Column(db.Integer, primary_key=True)
    respuesta = db.Column(db.Text, nullable=False)
    puntaje = db.Column(db.Integer)

class RespuestaUsuario(db.Model):
    __tablename__ = 'respuesta_usuario'
    respuesta_usuario_id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.usuario_id'), nullable=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('pregunta.pregunta_id'), nullable=False)
    respuesta_id = db.Column(db.Integer, db.ForeignKey('respuesta.respuesta_id'), nullable=False)
    fecha_respuesta = db.Column(db.Date, nullable=False)
    test_id = db.Column(db.Integer)

class ResultadoTest(db.Model):
    __tablename__ = 'resultado_test'
    resultado_id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.usuario_id'), nullable=False)
    test_id = db.Column(db.Integer, nullable=False)
    puntaje = db.Column(db.Integer)
    resultado = db.Column(db.String(255))
    comentarios = db.Column(db.Text)  # New field

# Esquemas para serialización con Marshmallow
class UsuarioSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Usuario
        include_fk = True

class PreguntaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Pregunta

class RespuestaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Respuesta

class RespuestaUsuarioSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = RespuestaUsuario

class ResultadoTestSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ResultadoTest
        include_fk = True

    comentarios = ma.auto_field()


# Instancias de los esquemas
usuario_schema = UsuarioSchema()
usuarios_schema = UsuarioSchema(many=True)
pregunta_schema = PreguntaSchema()
preguntas_schema = PreguntaSchema(many=True)
respuesta_schema = RespuestaSchema()
respuestas_schema = RespuestaSchema(many=True)
respuesta_usuario_schema = RespuestaUsuarioSchema()
respuestas_usuario_schema = RespuestaUsuarioSchema(many=True)
resultado_test_schema = ResultadoTestSchema()
resultados_test_schema = ResultadoTestSchema(many=True)

# Rutas de la API
@app.route('/usuario', methods=['POST'])
def crear_usuario():
    correo = request.json['correo']
    nombre = request.json['nombre']
    apellidos = request.json['apellidos']
    fecha_nacimiento = datetime.strptime(request.json['fecha_nacimiento'], '%Y-%m-%d').date()
    contrasena_plana = request.json['contrasena']
    tipo_usuario = request.json['tipo_usuario']
    coordenadas = request.json.get('coordenadas', '')  # Obtener coordenadas del JSON

    if Login.query.filter_by(correo=correo).first():
        return jsonify(message='El correo ya está registrado'), 400

    hashed_password = bcrypt.generate_password_hash(contrasena_plana).decode('utf-8')

    nuevo_usuario = Usuario(
        correo=correo,
        nombre=nombre,
        apellidos=apellidos,
        fecha_nacimiento=fecha_nacimiento,
        tipo_usuario=tipo_usuario,
        coordenadas=coordenadas  # Asignar coordenadas al modelo Usuario
    )
    db.session.add(nuevo_usuario)
    db.session.commit()

    nuevo_login = Login(correo=correo, contrasena=hashed_password, usuario_id=nuevo_usuario.usuario_id)
    db.session.add(nuevo_login)
    db.session.commit()

    return jsonify(message='Usuario creado exitosamente'), 201


@app.route('/login', methods=['POST'])
def login():
    correo = request.json['correo']
    contrasena = request.json['contrasena']

    login = Login.query.filter_by(correo=correo).first()

    if not login or not bcrypt.check_password_hash(login.contrasena, contrasena):
        return jsonify(success=False, message='Correo o contraseña incorrectos'), 401

    usuario = Usuario.query.filter_by(usuario_id=login.usuario_id).first()

    if usuario.tipo_usuario != 1:  # Verifica que el tipo de usuario sea 1
        return jsonify(success=False, message='No tiene permiso para iniciar sesión'), 403

    usuario_data = usuario_schema.dump(usuario)

    return jsonify(success=True, message='Inicio de sesión exitoso', usuario_id=usuario.usuario_id), 200

@app.route('/login2', methods=['POST'])
def login2():
    correo = request.json['correo']
    contrasena = request.json['contrasena']

    login = Login.query.filter_by(correo=correo).first()

    if not login or not bcrypt.check_password_hash(login.contrasena, contrasena):
        return jsonify(success=False, message='Correo o contraseña incorrectos'), 401

    usuario = Usuario.query.filter_by(usuario_id=login.usuario_id).first()

    if usuario.tipo_usuario != 2:  # Verifica que el tipo de usuario sea 1
        return jsonify(success=False, message='No tiene permiso para iniciar sesión'), 403

    usuario_data = usuario_schema.dump(usuario)

    return jsonify(success=True, message='Inicio de sesión exitoso', usuario_id=usuario.usuario_id), 200


@app.route('/preguntas', methods=['GET'])
def obtener_preguntas():
    preguntas = Pregunta.query.all()
    return preguntas_schema.jsonify(preguntas)

@app.route('/respuestas', methods=['GET'])
def obtener_respuestas():
    respuestas = Respuesta.query.all()
    return respuestas_schema.jsonify(respuestas)

@app.route('/guardar-respuestas', methods=['POST'])
def guardar_respuestas():
    if not request.is_json:
        return jsonify(message="El contenido de la solicitud no es JSON"), 400

    datos = request.get_json()

    if not isinstance(datos, list):
        return jsonify(message="La estructura JSON debe ser una lista"), 400

    for respuesta_data in datos:
        usuario_id = respuesta_data.get('usuario_id')
        pregunta_id = respuesta_data.get('pregunta_id')
        respuesta_id = respuesta_data.get('respuesta_id')
        fecha_respuesta_str = respuesta_data.get('fecha_respuesta')

        if not (usuario_id and pregunta_id and respuesta_id and fecha_respuesta_str):
            return jsonify(message="Datos de respuesta incompletos"), 400

        try:
            fecha_respuesta = datetime.strptime(fecha_respuesta_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify(message="Formato de fecha incorrecto"), 400

        # Obtener el último test_id del usuario
        ultima_respuesta_usuario = RespuestaUsuario.query.filter_by(usuario_id=usuario_id).order_by(RespuestaUsuario.test_id.desc()).first()
        if ultima_respuesta_usuario:
            ultimo_test_id = ultima_respuesta_usuario.test_id
        else:
            ultimo_test_id = 0

        # Calcular el nuevo test_id
        nuevo_test_id = ultimo_test_id + 1 if pregunta_id == 1 else ultimo_test_id

        nueva_respuesta_usuario = RespuestaUsuario(
            usuario_id=usuario_id,
            pregunta_id=pregunta_id,
            respuesta_id=respuesta_id,
            fecha_respuesta=fecha_respuesta,
            test_id=nuevo_test_id
        )
        db.session.add(nueva_respuesta_usuario)

    db.session.commit()

    # Calcular y guardar el resultado del test
    puntaje, resultado = calcular_resultado_test(usuario_id, nuevo_test_id)
    guardar_resultado_test(usuario_id, nuevo_test_id, puntaje, resultado)

    # Devolver respuesta con indicador de éxito
    return jsonify(message='Respuestas guardadas exitosamente', puntaje=puntaje, resultado=resultado, completado=True), 201

def calcular_resultado_test(usuario_id, test_id):
    puntaje_total = 0
    respuestas_usuario = RespuestaUsuario.query.filter_by(usuario_id=usuario_id, test_id=test_id).all()

    for respuesta_usuario in respuestas_usuario:
        respuesta = Respuesta.query.get(respuesta_usuario.respuesta_id)
        if respuesta:
            puntaje_total += respuesta.puntaje

    resultado = "Normal" if puntaje_total <= 17 else "Leve" if puntaje_total <= 24 else "Moderado" if puntaje_total <= 30 else "Severo"

    return puntaje_total, resultado


def guardar_resultado_test(usuario_id, test_id, puntaje, resultado):
    nuevo_resultado = ResultadoTest(
        usuario_id=usuario_id,
        test_id=test_id,
        puntaje=puntaje,
        resultado=resultado
    )

    db.session.add(nuevo_resultado)
    db.session.commit()

@app.route('/ver-respuestas/<int:usuario_id>', methods=['GET'])
def ver_respuestas(usuario_id):
    respuestas_usuario = RespuestaUsuario.query.filter_by(usuario_id=usuario_id).all()
    return respuestas_usuario_schema.jsonify(respuestas_usuario)

@app.route('/ver-resultado/<int:usuario_id>', methods=['GET'])
def ver_resultado(usuario_id):
    resultados = ResultadoTest.query.filter_by(usuario_id=usuario_id).all()
    if resultados:
        return resultados_test_schema.jsonify(resultados)
    else:
        return jsonify(message="No se encontraron resultados para el usuario especificado"), 404

# Ruta para obtener datos de heatmap y tabla para todos los usuarios
@app.route('/heatmap', methods=['GET'])
def obtener_heatmap():
    usuarios = Usuario.query.all()
    heatmap_data = []

    for usuario in usuarios:
        resultados = ResultadoTest.query.filter_by(usuario_id=usuario.usuario_id).all()
        for resultado in resultados:
            heatmap_data.append({
                'usuario_id': usuario.usuario_id,
                'nombre': usuario.nombre,
                'apellidos': usuario.apellidos,
                'puntaje': resultado.puntaje,
                'resultado': resultado.resultado,
                'resultado_id': resultado.resultado_id,  # Agregar resultado_id
                'comentarios': resultado.comentarios,  # Agregar comentarios
                'coordenadas': usuario.coordenadas,
                'color': obtener_color(resultado.puntaje)
            })

    return jsonify(heatmap=heatmap_data)

# Función para obtener color según el puntaje
def obtener_color(puntaje):
    if puntaje <= 17:
        return 'green'
    elif puntaje <= 24:
        return 'yellow'
    elif puntaje <= 30:
        return 'orange'
    else:
        return 'red'

@app.route('/actualizar-comentarios/<int:resultado_id>', methods=['PUT'])
def actualizar_comentarios(resultado_id):
    comentario = request.json.get('comentarios')
    resultado = ResultadoTest.query.get(resultado_id)
    if not resultado:
        return jsonify({'error': 'Resultado no encontrado'}), 404
    
    resultado.comentarios = comentario
    db.session.commit()
    return jsonify({'mensaje': 'Comentario actualizado exitosamente'})

@app.route('/usuarios-tipo1', methods=['GET'])
def obtener_usuarios_tipo1():
    usuarios = Usuario.query.filter_by(tipo_usuario=1).all()
    return usuarios_schema.jsonify(usuarios)

@app.route('/usuario/<int:usuario_id>', methods=['PUT'])
def actualizar_usuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify(success=False, error='Usuario no encontrado'), 404

    login = Login.query.filter_by(usuario_id=usuario_id).first()
    if not login:
        return jsonify(success=False, error='Login no encontrado'), 404

    nuevo_correo = request.json.get('correo', usuario.correo)

    # Verificar si el nuevo correo ya existe en otro usuario
    if nuevo_correo != usuario.correo and Usuario.query.filter_by(correo=nuevo_correo).first():
        return jsonify(success=False, error='El correo ya está registrado'), 400

    usuario.correo = nuevo_correo
    usuario.nombre = request.json.get('nombre', usuario.nombre)
    usuario.apellidos = request.json.get('apellidos', usuario.apellidos)
    usuario.fecha_nacimiento = datetime.strptime(request.json.get('fecha_nacimiento', usuario.fecha_nacimiento.strftime('%Y-%m-%d')), '%Y-%m-%d').date()

    login.correo = usuario.correo  # Update email in login table

    db.session.commit()
    return jsonify(success=True, mensaje='Usuario actualizado exitosamente')

@app.route('/usuario/<int:usuario_id>', methods=['DELETE'])
def eliminar_usuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify(success=False, error='Usuario no encontrado'), 404

    login = Login.query.filter_by(usuario_id=usuario_id).first()
    if login:
        db.session.delete(login)

    db.session.delete(usuario)
    db.session.commit()
    return jsonify(success=True, mensaje='Usuario eliminado exitosamente')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

