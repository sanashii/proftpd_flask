"""Add user statistics fields

Revision ID: 8e93d438ac61
Revises: 
Create Date: 2024-11-04 20:48:12.614342

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e93d438ac61'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('login_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_modified', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('bytes_uploaded', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('bytes_downloaded', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('files_uploaded', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('files_downloaded', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('files_downloaded')
        batch_op.drop_column('files_uploaded')
        batch_op.drop_column('bytes_downloaded')
        batch_op.drop_column('bytes_uploaded')
        batch_op.drop_column('last_modified')
        batch_op.drop_column('last_login')
        batch_op.drop_column('login_count')

    # ### end Alembic commands ###