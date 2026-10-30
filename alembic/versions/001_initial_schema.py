"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-30 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create sequence for concurrency-safe incident ID generation
    op.execute("CREATE SEQUENCE IF NOT EXISTS incident_id_seq START WITH 1 INCREMENT BY 1;")

    # 2. Table: user_profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('erp_user_id', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='STUDENT'),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('erp_user_id')
    )
    op.create_index('ix_user_profiles_erp_user_id', 'user_profiles', ['erp_user_id'])
    op.create_index('ix_user_profiles_email', 'user_profiles', ['email'])

    # 3. Table: incident_reports
    op.create_table(
        'incident_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incident_id', sa.String(length=50), nullable=False),
        sa.Column('reporter_erp_id', sa.String(length=100), nullable=True),
        sa.Column('reported_by', sa.String(length=255), nullable=False),
        sa.Column('reporter_email', sa.String(length=255), nullable=True),
        sa.Column('reporter_role', sa.String(length=50), nullable=False, server_default='STUDENT'),
        sa.Column('reporter_dept', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('category_label', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_evidence', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='Medium'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('assigned_admin_erp_id', sa.String(length=100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_id')
    )
    op.create_index('ix_incident_reports_incident_id', 'incident_reports', ['incident_id'])
    op.create_index('ix_incident_reports_status', 'incident_reports', ['status'])
    op.create_index('ix_incident_reports_created_at', 'incident_reports', ['created_at'])
    op.create_index('ix_incident_reports_reporter_erp_id', 'incident_reports', ['reporter_erp_id'])
    op.create_index('ix_incident_reports_assigned_admin_erp_id', 'incident_reports', ['assigned_admin_erp_id'])

    # 4. Table: incident_evidence
    op.create_table(
        'incident_evidence',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('file_storage_ref', sa.String(length=500), nullable=True),
        sa.Column('sanitized_metadata', sa.Text(), nullable=True),
        sa.Column('uploaded_by_erp_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['incident_id'], ['incident_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incident_evidence_incident_id', 'incident_evidence', ['incident_id'])

    # 5. Table: incident_investigations
    op.create_table(
        'incident_investigations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('admin_erp_id', sa.String(length=100), nullable=True),
        sa.Column('admin_name', sa.String(length=255), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('investigation_note', sa.Text(), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['incident_id'], ['incident_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incident_investigations_incident_id', 'incident_investigations', ['incident_id'])

    # 6. Table: screenshot_scan_results
    op.create_table(
        'screenshot_scan_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_id', sa.String(length=64), nullable=False),
        sa.Column('user_erp_id', sa.String(length=100), nullable=True),
        sa.Column('detection_result', sa.String(length=100), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('detection_metadata', sa.Text(), nullable=True),
        sa.Column('engine_version', sa.String(length=50), nullable=False, server_default='SignalSafe-OCR-v2.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scan_id')
    )
    op.create_index('ix_screenshot_scan_results_scan_id', 'screenshot_scan_results', ['scan_id'])
    op.create_index('ix_screenshot_scan_results_user_erp_id', 'screenshot_scan_results', ['user_erp_id'])
    op.create_index('ix_screenshot_scan_results_created_at', 'screenshot_scan_results', ['created_at'])

    # 7. Table: url_scan_results
    op.create_table(
        'url_scan_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_id', sa.String(length=64), nullable=False),
        sa.Column('user_erp_id', sa.String(length=100), nullable=True),
        sa.Column('normalized_url', sa.Text(), nullable=False),
        sa.Column('detection_result', sa.String(length=100), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('detection_metadata', sa.Text(), nullable=True),
        sa.Column('report_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scan_id')
    )
    op.create_index('ix_url_scan_results_scan_id', 'url_scan_results', ['scan_id'])
    op.create_index('ix_url_scan_results_user_erp_id', 'url_scan_results', ['user_erp_id'])
    op.create_index('ix_url_scan_results_created_at', 'url_scan_results', ['created_at'])

    # 8. Table: qr_scan_results
    op.create_table(
        'qr_scan_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_id', sa.String(length=64), nullable=False),
        sa.Column('user_erp_id', sa.String(length=100), nullable=True),
        sa.Column('extracted_destination', sa.Text(), nullable=False),
        sa.Column('detection_result', sa.String(length=100), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('detection_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scan_id')
    )
    op.create_index('ix_qr_scan_results_scan_id', 'qr_scan_results', ['scan_id'])
    op.create_index('ix_qr_scan_results_user_erp_id', 'qr_scan_results', ['user_erp_id'])
    op.create_index('ix_qr_scan_results_created_at', 'qr_scan_results', ['created_at'])

    # 9. Table: security_audit_logs
    op.create_table(
        'security_audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('actor_erp_id', sa.String(length=100), nullable=True),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('actor_role', sa.String(length=50), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('target_resource_type', sa.String(length=100), nullable=False),
        sa.Column('target_resource_id', sa.String(length=100), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=False, server_default='SUCCESS'),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    op.create_index('ix_security_audit_logs_event_id', 'security_audit_logs', ['event_id'])
    op.create_index('ix_security_audit_logs_actor_erp_id', 'security_audit_logs', ['actor_erp_id'])
    op.create_index('ix_security_audit_logs_event_type', 'security_audit_logs', ['event_type'])
    op.create_index('ix_security_audit_logs_created_at', 'security_audit_logs', ['created_at'])

    # 10. Table: user_preferences
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_erp_id', sa.String(length=100), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('theme', sa.String(length=20), nullable=False, server_default='light'),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_erp_id'], ['user_profiles.erp_user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_erp_id')
    )
    op.create_index('ix_user_preferences_user_erp_id', 'user_preferences', ['user_erp_id'])

    # 11. Table: community_reported_urls
    op.create_table(
        'community_reported_urls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('url_key', sa.Text(), nullable=False),
        sa.Column('report_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_reported_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url_key')
    )
    op.create_index('ix_community_reported_urls_url_key', 'community_reported_urls', ['url_key'])

    # 12. Table: app_statistics
    op.create_table(
        'app_statistics',
        sa.Column('stat_key', sa.String(length=100), nullable=False),
        sa.Column('stat_value', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('stat_key')
    )


def downgrade() -> None:
    op.drop_table('app_statistics')
    op.drop_table('community_reported_urls')
    op.drop_table('user_preferences')
    op.drop_table('security_audit_logs')
    op.drop_table('qr_scan_results')
    op.drop_table('url_scan_results')
    op.drop_table('screenshot_scan_results')
    op.drop_table('incident_investigations')
    op.drop_table('incident_evidence')
    op.drop_table('incident_reports')
    op.drop_table('user_profiles')
    op.execute("DROP SEQUENCE IF EXISTS incident_id_seq;")
