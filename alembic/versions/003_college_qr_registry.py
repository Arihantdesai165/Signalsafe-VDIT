"""003_college_qr_registry

Revision ID: 003_college_qr_registry
Revises: 002_screenshot_datasets
Create Date: 2026-10-30 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_college_qr_registry'
down_revision: Union[str, None] = '002_screenshot_datasets'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create table: college_payment_qrs
    op.create_table(
        'college_payment_qrs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('record_id', sa.String(length=64), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('payment_purpose', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=150), nullable=True),
        sa.Column('official_recipient_name', sa.String(length=255), nullable=False),
        sa.Column('expected_upi_id', sa.String(length=255), nullable=False),
        sa.Column('expected_amount', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('merchant_code', sa.String(length=50), nullable=True),
        sa.Column('qr_payload', sa.Text(), nullable=False),
        sa.Column('payload_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('image_storage_ref', sa.String(length=255), nullable=True),
        sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by_erp_id', sa.String(length=100), nullable=True),
        sa.Column('created_by_name', sa.String(length=255), nullable=True),
        sa.Column('approved_by_erp_id', sa.String(length=100), nullable=True),
        sa.Column('approved_by_name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('record_id')
    )

    # 2. Indexes
    op.create_index(op.f('ix_college_payment_qrs_record_id'), 'college_payment_qrs', ['record_id'], unique=True)
    op.create_index(op.f('ix_college_payment_qrs_payment_purpose'), 'college_payment_qrs', ['payment_purpose'], unique=False)
    op.create_index(op.f('ix_college_payment_qrs_department'), 'college_payment_qrs', ['department'], unique=False)
    op.create_index(op.f('ix_college_payment_qrs_official_recipient_name'), 'college_payment_qrs', ['official_recipient_name'], unique=False)
    op.create_index(op.f('ix_college_payment_qrs_expected_upi_id'), 'college_payment_qrs', ['expected_upi_id'], unique=False)
    op.create_index(op.f('ix_college_payment_qrs_payload_fingerprint'), 'college_payment_qrs', ['payload_fingerprint'], unique=False)
    op.create_index(op.f('ix_college_payment_qrs_approval_status'), 'college_payment_qrs', ['approval_status'], unique=False)
    op.create_index(op.f('ix_college_payment_qrs_is_active'), 'college_payment_qrs', ['is_active'], unique=False)

    op.create_index('idx_college_qr_lookup', 'college_payment_qrs', ['payload_fingerprint', 'is_active', 'approval_status'], unique=False)
    op.create_index('idx_college_qr_vpa_lookup', 'college_payment_qrs', ['expected_upi_id', 'is_active', 'approval_status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_college_qr_vpa_lookup', table_name='college_payment_qrs')
    op.drop_index('idx_college_qr_lookup', table_name='college_payment_qrs')
    op.drop_index(op.f('ix_college_payment_qrs_is_active'), table_name='college_payment_qrs')
    op.drop_index(op.f('ix_college_payment_qrs_approval_status'), table_name='college_payment_qrs')
    op.drop_index(op.f('ix_college_payment_qrs_payload_fingerprint'), table_name='college_payment_qrs')
    op.drop_index(op.f('ix_college_payment_qrs_expected_upi_id'), table_name='college_payment_qrs')
    op.drop_index(op.f('ix_college_payment_qrs_official_recipient_name'), table_name='college_payment_qrs')
    op.drop_index(op.f('ix_college_payment_qrs_department'), table_name='college_payment_qrs')
    op.drop_index(op.f('ix_college_payment_qrs_payment_purpose'), table_name='college_payment_qrs')
    op.drop_index(op.f('ix_college_payment_qrs_record_id'), table_name='college_payment_qrs')
    op.drop_table('college_payment_qrs')

