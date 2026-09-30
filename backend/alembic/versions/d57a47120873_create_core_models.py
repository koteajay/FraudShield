"""create_core_models

Revision ID: d57a47120873
Revises: 
Create Date: 2026-09-30 13:43:13.040708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd57a47120873'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('user', 'analyst', 'admin', name='userrole', native_enum=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=False)

    # 2. devices
    op.create_table(
        'devices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('fingerprint', sa.String(length=128), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False),
        sa.Column('operating_system', sa.String(length=50), nullable=True),
        sa.Column('browser', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('is_trusted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_vpn', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_tor', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_emulator', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_devices_fingerprint'), 'devices', ['fingerprint'], unique=False)
    op.create_index(op.f('ix_devices_ip_address'), 'devices', ['ip_address'], unique=False)
    op.create_index(op.f('ix_devices_user_id'), 'devices', ['user_id'], unique=False)

    # 3. transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_reference', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('payment_card_bin', sa.String(length=8), nullable=True),
        sa.Column('payment_card_last4', sa.String(length=4), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('merchant_id', sa.String(length=64), nullable=True),
        sa.Column('merchant_name', sa.String(length=128), nullable=True),
        sa.Column('merchant_category', sa.String(length=64), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('country', sa.String(length=3), nullable=True),
        sa.Column('city', sa.String(length=64), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('billing_country', sa.String(length=3), nullable=True),
        sa.Column('shipping_country', sa.String(length=3), nullable=True),
        sa.Column('is_billing_shipping_mismatch', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('distance_from_last_txn_km', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel', native_enum=False), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'DECLINED', 'FLAGGED', 'UNDER_REVIEW', name='transactionstatus', native_enum=False), nullable=False),
        sa.Column('review_status', sa.Enum('NOT_REQUIRED', 'PENDING_REVIEW', 'IN_REVIEW', 'RESOLVED_LEGITIMATE', 'RESOLVED_FRAUD', 'ESCALATED', name='reviewstatus', native_enum=False), nullable=False),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_transactions_ip_address'), 'transactions', ['ip_address'], unique=False)
    op.create_index(op.f('ix_transactions_merchant_id'), 'transactions', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_transactions_review_status'), 'transactions', ['review_status'], unique=False)
    op.create_index(op.f('ix_transactions_risk_level'), 'transactions', ['risk_level'], unique=False)
    op.create_index(op.f('ix_transactions_risk_score'), 'transactions', ['risk_score'], unique=False)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)
    op.create_index(op.f('ix_transactions_timestamp'), 'transactions', ['timestamp'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_reference'), 'transactions', ['transaction_reference'], unique=True)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_transactions_device_id'), 'transactions', ['device_id'], unique=False)

    # 4. fraud_flags
    op.create_table(
        'fraud_flags',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('flag_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='flagseverity', native_enum=False), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('score_impact', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('resolved_by', sa.String(length=64), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_fraud_flags_created_at'), 'fraud_flags', ['created_at'], unique=False)
    op.create_index(op.f('ix_fraud_flags_flag_type'), 'fraud_flags', ['flag_type'], unique=False)
    op.create_index(op.f('ix_fraud_flags_severity'), 'fraud_flags', ['severity'], unique=False)
    op.create_index(op.f('ix_fraud_flags_transaction_id'), 'fraud_flags', ['transaction_id'], unique=False)

    # 5. fraud_rule_results
    op.create_table(
        'fraud_rule_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('rule_id', sa.String(length=64), nullable=False),
        sa.Column('rule_name', sa.String(length=128), nullable=False),
        sa.Column('rule_category', sa.String(length=64), nullable=False),
        sa.Column('is_triggered', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('weight', sa.Float(), nullable=False, server_default=sa.text('1.0')),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='ruleseverity', native_enum=False), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_fraud_rule_results_is_triggered'), 'fraud_rule_results', ['is_triggered'], unique=False)
    op.create_index(op.f('ix_fraud_rule_results_rule_id'), 'fraud_rule_results', ['rule_id'], unique=False)
    op.create_index(op.f('ix_fraud_rule_results_transaction_id'), 'fraud_rule_results', ['transaction_id'], unique=False)

    # 6. reviews
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('assigned_to_user_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.Enum('ASSIGNED', 'IN_PROGRESS', 'APPROVED', 'REJECTED', 'ESCALATED', 'CLOSED', name='reviewstate', native_enum=False), nullable=False),
        sa.Column('decision', sa.Enum('APPROVE', 'REJECT', 'REQUEST_VERIFICATION', 'ADD_TO_BLOCKLIST', 'CONFIRMED_FRAUD', name='reviewdecision', native_enum=False), nullable=True),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='reviewpriority', native_enum=False), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('resolution_reason', sa.Text(), nullable=True),
        sa.Column('escalated_to', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reviews_assigned_to_user_id'), 'reviews', ['assigned_to_user_id'], unique=False)
    op.create_index(op.f('ix_reviews_created_at'), 'reviews', ['created_at'], unique=False)
    op.create_index(op.f('ix_reviews_priority'), 'reviews', ['priority'], unique=False)
    op.create_index(op.f('ix_reviews_status'), 'reviews', ['status'], unique=False)
    op.create_index(op.f('ix_reviews_transaction_id'), 'reviews', ['transaction_id'], unique=False)

    # 7. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=True),
        sa.Column('notification_type', sa.Enum('SUSPICIOUS_TRANSACTION', 'NEW_DEVICE_LOGIN', 'ACCOUNT_LOCKED', 'FRAUD_ALERT', 'REVIEW_REQUIRED', 'SYSTEM_ALERT', name='notificationtype', native_enum=False), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('channel', sa.Enum('IN_APP', 'EMAIL', 'SMS', 'PUSH', 'WEBHOOK', name='notificationchannel', native_enum=False), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'HIGH', 'CRITICAL', name='notificationseverity', native_enum=False), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notifications_transaction_id'), 'notifications', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # 8. login_attempts
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('attempted_email', sa.String(length=255), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('country', sa.String(length=3), nullable=True),
        sa.Column('city', sa.String(length=64), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_successful', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('failure_reason', sa.String(length=128), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_login_attempts_attempted_email'), 'login_attempts', ['attempted_email'], unique=False)
    op.create_index(op.f('ix_login_attempts_device_id'), 'login_attempts', ['device_id'], unique=False)
    op.create_index(op.f('ix_login_attempts_ip_address'), 'login_attempts', ['ip_address'], unique=False)
    op.create_index(op.f('ix_login_attempts_is_successful'), 'login_attempts', ['is_successful'], unique=False)
    op.create_index(op.f('ix_login_attempts_is_suspicious'), 'login_attempts', ['is_suspicious'], unique=False)
    op.create_index(op.f('ix_login_attempts_timestamp'), 'login_attempts', ['timestamp'], unique=False)
    op.create_index(op.f('ix_login_attempts_user_id'), 'login_attempts', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('login_attempts')
    op.drop_table('notifications')
    op.drop_table('reviews')
    op.drop_table('fraud_rule_results')
    op.drop_table('fraud_flags')
    op.drop_table('transactions')
    op.drop_table('devices')
    op.drop_table('users')
