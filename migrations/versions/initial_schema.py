"""initial schema

Revision ID: initial_schema
Revises: 
Create Date: 2024-04-09 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Crear tabla de usuarios
    op.create_table('usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(64), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=True),
        sa.Column('nombre', sa.String(100), nullable=True),
        sa.Column('apellido', sa.String(100), nullable=True),
        sa.Column('rol', sa.String(20), nullable=False, server_default='usuario'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('fecha_registro', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ultima_conexion', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    # Crear tabla de profesores
    op.create_table('profesores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('especialidad', sa.String(100), nullable=True),
        sa.Column('foto', sa.String(255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('max_horas_diarias', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear tabla de asignaturas
    op.create_table('asignaturas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('codigo', sa.String(20), nullable=True),
        sa.Column('horas_semanales', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('bloques_continuos', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('color', sa.String(7), nullable=False, server_default='#3498db'),
        sa.Column('icono', sa.String(50), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
        sa.UniqueConstraint('nombre')
    )

    # Crear tabla de clases
    op.create_table('clases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(50), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('nivel', sa.String(50), nullable=True),
        sa.Column('curso', sa.String(50), nullable=True),
        sa.Column('color', sa.String(7), nullable=False, server_default='#2ecc71'),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre')
    )

    # Crear tabla de asignaturas_profesores
    op.create_table('asignaturas_profesores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asignatura_id', sa.Integer(), nullable=False),
        sa.Column('profesor_id', sa.Integer(), nullable=False),
        sa.Column('asignado_en', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['asignatura_id'], ['asignaturas.id'], ),
        sa.ForeignKeyConstraint(['profesor_id'], ['profesores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear tabla de asignaturas_profesores_clases
    op.create_table('asignaturas_profesores_clases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asignatura_profesor_id', sa.Integer(), nullable=False),
        sa.Column('clase_id', sa.Integer(), nullable=False),
        sa.Column('fecha_asignacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['asignatura_profesor_id'], ['asignaturas_profesores.id'], ),
        sa.ForeignKeyConstraint(['clase_id'], ['clases.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asignatura_profesor_id', 'clase_id', name='uix_asignatura_profesor_clase')
    )

    # Crear tabla de horarios
    op.create_table('horarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clase_id', sa.Integer(), nullable=False),
        sa.Column('dia', sa.String(15), nullable=False),
        sa.Column('hora', sa.String(15), nullable=False),
        sa.Column('asignatura_id', sa.Integer(), nullable=False),
        sa.Column('profesor_id', sa.Integer(), nullable=False),
        sa.Column('unido_con_clase_id', sa.Integer(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ultima_modificacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['asignatura_id'], ['asignaturas.id'], ),
        sa.ForeignKeyConstraint(['clase_id'], ['clases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profesor_id'], ['profesores.id'], ),
        sa.ForeignKeyConstraint(['unido_con_clase_id'], ['clases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear tabla de disponibilidades
    op.create_table('disponibilidades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profesor_id', sa.Integer(), nullable=False),
        sa.Column('dia', sa.String(10), nullable=False),
        sa.Column('hora', sa.String(20), nullable=False),
        sa.Column('disponible', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('motivo', sa.String(255), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('fecha_modificacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['profesor_id'], ['profesores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profesor_id', 'dia', 'hora', name='uq_disponibilidad_profesor_dia_hora')
    )

    # Crear tabla de disponibilidad_comun
    op.create_table('disponibilidad_comun',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dia', sa.String(15), nullable=False),
        sa.Column('hora', sa.String(10), nullable=False),
        sa.Column('titulo', sa.String(100), nullable=False),
        sa.Column('color', sa.String(20), nullable=False, server_default='#3498db'),
        sa.Column('icono', sa.String(30), nullable=False, server_default='fa-coffee'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dia', 'hora', name='uq_disponibilidad_comun_dia_hora')
    )

    # Crear tabla de excepciones
    op.create_table('excepciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('horario_id', sa.Integer(), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('motivo', sa.String(255), nullable=True),
        sa.Column('profesor_suplente_id', sa.Integer(), nullable=True),
        sa.Column('creado_por', sa.Integer(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['horario_id'], ['horarios.id'], ),
        sa.ForeignKeyConstraint(['profesor_suplente_id'], ['profesores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Eliminar tablas en orden inverso para respetar las dependencias
    op.drop_table('excepciones')
    op.drop_table('disponibilidad_comun')
    op.drop_table('disponibilidades')
    op.drop_table('horarios')
    op.drop_table('asignaturas_profesores_clases')
    op.drop_table('asignaturas_profesores')
    op.drop_table('clases')
    op.drop_table('asignaturas')
    op.drop_table('profesores')
    op.drop_table('usuarios') 