from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SelectField, BooleanField, SubmitField, RadioField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, ValidationError
from app.models.user import User
from app.models.asignatura import Asignatura
from app.models.clase import Clase

class UserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(max=100)])
    rol = SelectField('Rol', choices=[
        ('admin', 'Administrador'),
        ('profesor', 'Profesor'),
        ('alumno', 'Alumno')
    ], validators=[DataRequired()])
    activo = BooleanField('Usuario Activo')
    submit = SubmitField('Guardar')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if self.original_username is None or self.original_username != username.data:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elija otro.')

    def validate_email(self, email):
        if self.original_email is None or self.original_email != email.data:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Este email ya está registrado. Por favor, use otro.')

class ProfesorForm(FlaskForm):
    usuario_tipo = RadioField('Tipo de Usuario', choices=[
        ('nuevo', 'Crear nuevo usuario'),
        ('existente', 'Usar usuario existente')
    ], default='nuevo', validators=[DataRequired()])
    
    usuario_id = SelectField('Usuario Existente', coerce=int, validators=[Optional()])
    
    nombre = StringField('Nombre', validators=[Optional(), Length(max=100)])
    apellido = StringField('Apellido', validators=[Optional(), Length(max=100)])
    asignatura_id = SelectField('Asignatura', coerce=int, validators=[DataRequired()])
    bio = TextAreaField('Biografía', validators=[Optional(), Length(max=500)])
    max_horas_diarias = IntegerField('Máximo de Horas Diarias', validators=[DataRequired(), NumberRange(min=1, max=10)])
    foto = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo se permiten imágenes.')])
    submit = SubmitField('Guardar')
    
    def validate(self, **kwargs):
        if not super(ProfesorForm, self).validate(**kwargs):
            return False
            
        if self.usuario_tipo.data == 'nuevo':
            if not self.nombre.data or not self.apellido.data:
                if not self.nombre.data:
                    self.nombre.errors = list(self.nombre.errors)
                    self.nombre.errors.append('Este campo es obligatorio cuando se crea un nuevo usuario.')
                if not self.apellido.data:
                    self.apellido.errors = list(self.apellido.errors)
                    self.apellido.errors.append('Este campo es obligatorio cuando se crea un nuevo usuario.')
                return False
        elif self.usuario_tipo.data == 'existente':
            if not self.usuario_id.data:
                self.usuario_id.errors = list(self.usuario_id.errors)
                self.usuario_id.errors.append('Debe seleccionar un usuario existente.')
                return False
        
        return True

class AsignaturaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    codigo = StringField('Código', validators=[DataRequired(), Length(max=20)])
    horas_semanales = IntegerField('Horas Semanales', validators=[DataRequired(), NumberRange(min=1, max=20)])
    bloques_continuos = BooleanField('¿Bloques Continuos?', default=True)
    color = StringField('Color', validators=[DataRequired()], default='#3498db')
    icono = StringField('Icono', validators=[Optional()], default='fas fa-book')
    activa = BooleanField('Asignatura Activa', default=True)
    submit = SubmitField('Guardar')

    def __init__(self, original_nombre=None, original_codigo=None, *args, **kwargs):
        super(AsignaturaForm, self).__init__(*args, **kwargs)
        self.original_nombre = original_nombre
        self.original_codigo = original_codigo

    def validate_nombre(self, nombre):
        if self.original_nombre is None or self.original_nombre != nombre.data:
            asignatura = Asignatura.query.filter_by(nombre=nombre.data).first()
            if asignatura is not None:
                raise ValidationError('Ya existe una asignatura con este nombre.')

    def validate_codigo(self, codigo):
        if self.original_codigo is None or self.original_codigo != codigo.data:
            asignatura = Asignatura.query.filter_by(codigo=codigo.data).first()
            if asignatura is not None:
                raise ValidationError('Ya existe una asignatura con este código.')

class ClaseForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    nivel = SelectField('Nivel', choices=[
        ('1', 'Primer Año'),
        ('2', 'Segundo Año'),
        ('3', 'Tercer Año'),
        ('4', 'Cuarto Año'),
        ('5', 'Quinto Año'),
        ('6', 'Sexto Año')
    ], validators=[DataRequired()])
    seccion = StringField('Sección', validators=[DataRequired(), Length(max=10)])
    capacidad = IntegerField('Capacidad', validators=[DataRequired(), NumberRange(min=1, max=50)])
    activa = BooleanField('Clase Activa', default=True)
    submit = SubmitField('Guardar')

    def __init__(self, original_nombre=None, *args, **kwargs):
        super(ClaseForm, self).__init__(*args, **kwargs)
        self.original_nombre = original_nombre

    def validate_nombre(self, nombre):
        if self.original_nombre is None or self.original_nombre != nombre.data:
            clase = Clase.query.filter_by(nombre=nombre.data).first()
            if clase is not None:
                raise ValidationError('Ya existe una clase con este nombre.') 