"""SQLAlchemy ORM models for the TLF SaaS platform."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from backend.db.session import Base


def _uuid():
    return uuid.uuid4()


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    settings = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 租户订阅与配额管理字段
    plan_type = Column(String(50), default="free")  # 订阅套餐 ('free', 'plus', 'enterprise')
    lemon_subscription_id = Column(String(255), nullable=True)  # Lemon Squeezy 订阅唯一标识
    subscription_status = Column(String(100), nullable=True)  # 订阅状态 ('active', 'past_due', etc.)
    current_period_end = Column(DateTime(timezone=True), nullable=True)  # 当前账期结束时间
    monthly_usage_count = Column(Integer, default=0)  # 本月已生成报告次数

    studies = relationship("Study", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    role = Column(String(50), default="viewer")
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 个人订阅与配额管理字段
    plan_type = Column(String(50), default="free")  # 个人订阅套餐 ('free', 'pro')
    lemon_subscription_id = Column(String(255), nullable=True)  # 个人订阅唯一标识
    subscription_status = Column(String(100), nullable=True)  # 订阅状态 ('active', 'past_due', etc.)
    current_period_end = Column(DateTime(timezone=True), nullable=True)  # 当前账期结束时间
    monthly_usage_count = Column(Integer, default=0)  # 本月已生成报告次数 (用于个人额度)


class Study(Base):
    __tablename__ = "studies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    protocol_id = Column(String(100))
    description = Column(Text)
    status = Column(String(50), default="active")
    settings = Column(JSONB, default=dict)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="studies")
    datasets = relationship("Dataset", back_populates="study", cascade="all, delete-orphan")
    sap_documents = relationship("SAPDocument", back_populates="study", cascade="all, delete-orphan")
    toc_entries = relationship("TOCEntry", back_populates="study", cascade="all, delete-orphan")
    tlf_jobs = relationship("TLFJob", back_populates="study", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # e.g. "adsl", "adae"
    original_filename = Column(String(500))
    file_format = Column(String(20))  # sas7bdat | csv | xpt
    file_size_bytes = Column(BigInteger)
    minio_bucket = Column(String(255), nullable=False)
    minio_object_key = Column(String(500), nullable=False)
    record_count = Column(Integer)
    column_count = Column(Integer)
    variables = Column(JSONB, default=list)
    variable_names = Column(ARRAY(String), default=list)
    is_encrypted = Column(Boolean, default=True)
    checksum_sha256 = Column(String(64))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    study = relationship("Study", back_populates="datasets")


class SAPDocument(Base):
    __tablename__ = "sap_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    original_filename = Column(String(500))
    file_format = Column(String(20))  # docx | pdf
    minio_object_key = Column(String(500))
    parsed_text = Column(Text)
    is_parsed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    study = relationship("Study", back_populates="sap_documents")
    toc_entries = relationship("TOCEntry", back_populates="sap_document")


class TOCEntry(Base):
    __tablename__ = "toc_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sap_id = Column(UUID(as_uuid=True), ForeignKey("sap_documents.id"))
    tlf_id = Column(String(50), nullable=False)  # "Table 14.1.1.1"
    tlf_type = Column(String(20), nullable=False)  # table | figure | listing
    tlf_name = Column(String(500))
    population = Column(String(200))
    sort_order = Column(Integer)
    section = Column(String(50))
    analysis_type = Column(String(50))
    is_generated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    study = relationship("Study", back_populates="toc_entries")
    sap_document = relationship("SAPDocument", back_populates="toc_entries")


class TLFJob(Base):
    __tablename__ = "tlf_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    toc_entry_id = Column(UUID(as_uuid=True), ForeignKey("toc_entries.id"))
    tlf_id = Column(String(50), nullable=False)
    tlf_type = Column(String(20), nullable=False)
    tlf_name = Column(String(500))
    status = Column(String(20), default="pending")  # pending | running | completed | failed
    celery_task_id = Column(String(255))
    progress = Column(Float, default=0.0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    study = relationship("Study", back_populates="tlf_jobs")
    outputs = relationship("TLFOutput", back_populates="job", cascade="all, delete-orphan")


class TLFOutput(Base):
    __tablename__ = "tlf_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    job_id = Column(UUID(as_uuid=True), ForeignKey("tlf_jobs.id", ondelete="CASCADE"), nullable=False)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf | csv | png | json
    minio_object_key = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger)
    checksum_sha256 = Column(String(64))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    job = relationship("TLFJob", back_populates="outputs")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
