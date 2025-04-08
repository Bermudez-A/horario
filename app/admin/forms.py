from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, ValidationError
from app.models.user import User
from app.models.asignatura import Asignatura

class UserForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(message="El nombre de usuario es obligatorio"),
        Length(min=3, max=64, message="El usuario debe tener entre 3 y 64 caracteres")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio"),
        Email(message="Por favor, ingrese un email válido")
    ])
    nombre = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(max=100, message="El nombre es demasiado largo")
    ])
    apellido = StringField('Apellido', validators=[
        DataRequired(message="El apellido es obligatorio"),
        Length(max=100, message="El apellido es demasiado largo")
    ])
    rol = SelectField('Rol', choices=[
        ('admin', 'Administrador'),
        ('profesor', 'Profesor'),
        ('alumno', 'Alumno')
    ], validators=[DataRequired(message="Seleccione un rol")])
    activo = BooleanField('Activo')
    submit = SubmitField('Guardar')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elija otro.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Este email ya está registrado. Por favor, use otro.')

class ProfesorForm(FlaskForm):
    especialidad = StringField('Especialidad', validators=[
        DataRequired(message="La especialidad es obligatoria"),
        Length(max=100, message="La especialidad es demasiado larga")
    ])
    bio = TextAreaField('Biografía', validators=[
        Optional(),
        Length(max=500, message="La biografía es demasiado larga")
    ])
    max_horas_diarias = IntegerField('Máximo de horas diarias', validators=[
        DataRequired(message="El máximo de horas diarias es obligatorio"),
        NumberRange(min=1, max=7, message="Las horas diarias deben estar entre 1 y 7")
    ], default=4)
    foto = FileField('Foto de perfil', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Solo se permiten imágenes')
    ])
    submit = SubmitField('Guardar')

class AsignaturaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(max=100, message="El nombre es demasiado largo")
    ])
    codigo = StringField('Código', validators=[
        DataRequired(message="El código es obligatorio"),
        Length(max=20, message="El código es demasiado largo")
    ])
    horas_semanales = IntegerField('Horas semanales', validators=[
        DataRequired(message="Las horas semanales son obligatorias"),
        NumberRange(min=1, max=20, message="Las horas semanales deben estar entre 1 y 20")
    ], default=1)
    bloques_continuos = BooleanField('Preferencia por bloques de 2 horas')
    color = StringField('Color (hexadecimal)', default='#3498db', validators=[
        DataRequired(message="El color es obligatorio"),
        Length(min=7, max=7, message="El color debe tener formato #RRGGBB")
    ])
    icono = StringField('Icono (FontAwesome)', validators=[
        Optional(),
        Length(max=50, message="El nombre del icono es demasiado largo")
    ])
    activa = BooleanField('Activa', default=True)
    submit = SubmitField('Guardar')

    def __init__(self, original_nombre=None, original_codigo=None, *args, **kwargs):
        super(AsignaturaForm, self).__init__(*args, **kwargs)
        self.original_nombre = original_nombre
        self.original_codigo = original_codigo

    def validate_nombre(self, nombre):
        if nombre.data != self.original_nombre:
            asignatura = Asignatura.query.filter_by(nombre=nombre.data).first()
            if asignatura is not None:
                raise ValidationError('Ya existe una asignatura con este nombre')

    def validate_codigo(self, codigo):
        if codigo.data != self.original_codigo:
            asignatura = Asignatura.query.filter_by(codigo=codigo.data).first()
            if asignatura is not None:
                raise ValidationError('Ya existe una asignatura con este código')

class ClaseForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(max=50, message="El nombre es demasiado largo")
    ])
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=200, message="La descripción es demasiado larga")
    ])
    nivel = StringField('Nivel', validators=[
        DataRequired(message="El nivel es obligatorio"),
        Length(max=50, message="El nivel es demasiado largo")
    ])
    curso = StringField('Curso', validators=[
        DataRequired(message="El curso es obligatorio"),
        Length(max=50, message="El curso es demasiado largo")
    ])
    color = StringField('Color (hexadecimal)', default='#2ecc71', validators=[
        DataRequired(message="El color es obligatorio"),
        Length(min=7, max=7, message="El color debe tener formato #RRGGBB")
    ])
    activa = BooleanField('Activa', default=True)
    submit = SubmitField('Guardar') 