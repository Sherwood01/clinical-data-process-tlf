"""initial_schema: Create all core tables for the TLF SaaS platform.

Revision ID: 0001
Revises:
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable uuid-ossp extension for UUID generation
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── Tenants ──
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("settings", JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # ── Users ──
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255)),
        sa.Column("role", sa.String(50), server_default="viewer"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    # ── Studies ──
    op.create_table(
        "studies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("protocol_id", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("settings", JSONB, server_default="{}"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_studies_tenant_id", "studies", ["tenant_id"])

    # ── Datasets ──
    op.create_table(
        "datasets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", UUID(as_uuid=True), sa.ForeignKey("studies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("original_filename", sa.String(500)),
        sa.Column("file_format", sa.String(20)),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("minio_bucket", sa.String(255), nullable=False),
        sa.Column("minio_object_key", sa.String(500), nullable=False),
        sa.Column("record_count", sa.Integer),
        sa.Column("column_count", sa.Integer),
        sa.Column("variables", JSONB, server_default="[]"),
        sa.Column("variable_names", ARRAY(sa.String), server_default="{}"),
        sa.Column("is_encrypted", sa.Boolean, server_default="true"),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_datasets_study_id", "datasets", ["study_id"])
    op.create_index("ix_datasets_tenant_id", "datasets", ["tenant_id"])

    # ── SAP Documents ──
    op.create_table(
        "sap_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", UUID(as_uuid=True), sa.ForeignKey("studies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("original_filename", sa.String(500)),
        sa.Column("file_format", sa.String(20)),
        sa.Column("minio_object_key", sa.String(500)),
        sa.Column("parsed_text", sa.Text),
        sa.Column("is_parsed", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── TOC Entries ──
    op.create_table(
        "toc_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", UUID(as_uuid=True), sa.ForeignKey("studies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("sap_id", UUID(as_uuid=True), sa.ForeignKey("sap_documents.id")),
        sa.Column("tlf_id", sa.String(50), nullable=False),
        sa.Column("tlf_type", sa.String(20), nullable=False),
        sa.Column("tlf_name", sa.String(500)),
        sa.Column("population", sa.String(200)),
        sa.Column("sort_order", sa.Integer),
        sa.Column("section", sa.String(50)),
        sa.Column("analysis_type", sa.String(50)),
        sa.Column("is_generated", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_toc_entries_study_id", "toc_entries", ["study_id"])

    # ── TLF Jobs ──
    op.create_table(
        "tlf_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("study_id", UUID(as_uuid=True), sa.ForeignKey("studies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("toc_entry_id", UUID(as_uuid=True), sa.ForeignKey("toc_entries.id")),
        sa.Column("tlf_id", sa.String(50), nullable=False),
        sa.Column("tlf_type", sa.String(20), nullable=False),
        sa.Column("tlf_name", sa.String(500)),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("celery_task_id", sa.String(255)),
        sa.Column("progress", sa.Float, server_default="0.0"),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_tlf_jobs_study_id", "tlf_jobs", ["study_id"])

    # ── TLF Outputs ──
    op.create_table(
        "tlf_outputs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("tlf_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("study_id", UUID(as_uuid=True), sa.ForeignKey("studies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("minio_object_key", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Audit Log ──
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", sa.String(100)),
        sa.Column("details", JSONB, server_default="{}"),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"])


def downgrade():
    op.drop_table("audit_log")
    op.drop_table("tlf_outputs")
    op.drop_table("tlf_jobs")
    op.drop_table("toc_entries")
    op.drop_table("sap_documents")
    op.drop_table("datasets")
    op.drop_table("studies")
    op.drop_table("users")
    op.drop_table("tenants")
