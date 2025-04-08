from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(message="El nombre de usuario es obligatorio")])
    password = PasswordField('Contraseña', validators=[DataRequired(message="La contraseña es obligatoria")])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(message="El nombre de usuario es obligatorio"),
        Length(min=3, max=64, message="El usuario debe tener entre 3 y 64 caracteres")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio"),
        Email(message="Por favor, ingrese un email válido"),
        Length(max=120, message="El email es demasiado largo")
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
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria"),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres")
    ])
    password2 = PasswordField('Repetir Contraseña', validators=[
        DataRequired(message="Debe confirmar la contraseña"),
        EqualTo('password', message="Las contraseñas no coinciden")
    ])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elija otro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este email ya está registrado. Por favor, use otro o inicie sesión.')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio"),
        Email(message="Por favor, ingrese un email válido")
    ])
    submit = SubmitField('Enviar instrucciones de restablecimiento')

class PasswordResetForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria"),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres")
    ])
    password2 = PasswordField('Repetir Contraseña', validators=[
        DataRequired(message="Debe confirmar la contraseña"),
        EqualTo('password', message="Las contraseñas no coinciden")
    ])
    submit = SubmitField('Restablecer Contraseña') 