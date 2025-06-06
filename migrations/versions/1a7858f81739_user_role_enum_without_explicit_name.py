"""User role enum without explicit name

Revision ID: 1a7858f81739
Revises: 670e4179b4bd
Create Date: 2025-06-03 17:48:10.688128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a7858f81739'
down_revision = '670e4179b4bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.VARCHAR(length=12),
               type_=sa.Enum('SYSTEM_ADMIN', 'USER', name='roleenum', native_enum=False, length=50),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.Enum('SYSTEM_ADMIN', 'USER', name='roleenum', native_enum=False, length=50),
               type_=sa.VARCHAR(length=12),
               existing_nullable=False)

    # ### end Alembic commands ###
