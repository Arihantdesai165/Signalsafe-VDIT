"""002_screenshot_datasets

Revision ID: 002_screenshot_datasets
Revises: 001_initial_schema
Create Date: 2026-10-30 19:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_screenshot_datasets'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: screenshot_datasets
    op.create_table(
        'screenshot_datasets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_id', sa.String(length=64), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('dataset_type', sa.String(length=100), nullable=False, server_default='Demonstration Synthetic Dataset'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('total_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('invalid_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('uploaded_by_erp_id', sa.String(length=100), nullable=True),
        sa.Column('uploaded_by_name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_id')
    )
    op.create_index(op.f('ix_screenshot_datasets_dataset_id'), 'screenshot_datasets', ['dataset_id'], unique=True)
    op.create_index(op.f('ix_screenshot_datasets_is_active'), 'screenshot_datasets', ['is_active'], unique=False)

    # 2. Table: screenshot_transaction_records
    op.create_table(
        'screenshot_transaction_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.String(length=100), nullable=True),
        sa.Column('transaction_id', sa.String(length=100), nullable=True),
        sa.Column('utr_rrn', sa.String(length=100), nullable=True),
        sa.Column('transaction_date', sa.String(length=50), nullable=True),
        sa.Column('transaction_time', sa.String(length=50), nullable=True),
        sa.Column('amount_inr', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('payer_display_name', sa.String(length=255), nullable=True),
        sa.Column('payer_account_masked', sa.String(length=100), nullable=True),
        sa.Column('payee_name', sa.String(length=255), nullable=True),
        sa.Column('payee_vpa', sa.String(length=255), nullable=True),
        sa.Column('bank_or_app_label', sa.String(length=100), nullable=True),
        sa.Column('transaction_status', sa.String(length=50), nullable=True),
        sa.Column('dataset_type', sa.String(length=100), nullable=True),
        sa.Column('verification_status', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['dataset_id'], ['screenshot_datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_screenshot_transaction_records_dataset_id'), 'screenshot_transaction_records', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_screenshot_transaction_records_record_id'), 'screenshot_transaction_records', ['record_id'], unique=False)
    op.create_index(op.f('ix_screenshot_transaction_records_transaction_id'), 'screenshot_transaction_records', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_screenshot_transaction_records_utr_rrn'), 'screenshot_transaction_records', ['utr_rrn'], unique=False)
    op.create_index(op.f('ix_screenshot_transaction_records_payee_name'), 'screenshot_transaction_records', ['payee_name'], unique=False)
    op.create_index(op.f('ix_screenshot_transaction_records_payee_vpa'), 'screenshot_transaction_records', ['payee_vpa'], unique=False)
    op.create_index(op.f('ix_screenshot_transaction_records_amount_inr'), 'screenshot_transaction_records', ['amount_inr'], unique=False)


def downgrade() -> None:
    op.drop_table('screenshot_transaction_records')
    op.drop_table('screenshot_datasets')

