"""
Data Versioning & Lineage Tracking for Smart Travel Platform

Provides:
- Dataset versioning
- Data lineage tracking
- Pipeline run tracking
- Data quality metrics
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import json
import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    Text,
    JSON,
    Enum as SQLEnum,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

# ============================================================================
# ENUMS
# ============================================================================


class DatasetStatus(str, Enum):
    """Dataset processing status."""

    INGESTED = "ingested"
    PROCESSING = "processing"
    VALIDATED = "validated"
    ARCHIVED = "archived"
    FAILED = "failed"


class PipelineStage(str, Enum):
    """Pipeline execution stages."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    ANALYTICS = "analytics"


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

Base = declarative_base()


class DatasetVersion(Base):
    """
    Track dataset versions for data governance.

    Schema for tracking versions of processed datasets.
    """

    __tablename__ = "dataset_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)  # e.g., "1.0.0", "2021-05-07"
    city = Column(String(100), nullable=False, index=True)
    stage = Column(SQLEnum(PipelineStage), nullable=False, index=True)
    status = Column(SQLEnum(DatasetStatus), nullable=False, default=DatasetStatus.INGESTED)

    # Metrics
    record_count = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    schema_hash = Column(String(255), nullable=True)  # SHA256 of schema

    # Metadata
    source = Column(String(100), nullable=True)  # e.g., "osm", "google", "merged"
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # JSON metadata
    metadata = Column(JSON, nullable=True)  # {quality_score, errors, warnings, etc}

    def __repr__(self):
        return f"<DatasetVersion {self.dataset_name}:{self.version} ({self.stage})>"


class PipelineRun(Base):
    """
    Track pipeline execution runs.

    Schema for tracking each pipeline execution.
    """

    __tablename__ = "pipeline_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), unique=True, nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    stage = Column(SQLEnum(PipelineStage), nullable=False, index=True)

    # Execution details
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="running")  # running, success, failed

    # Task execution
    task_name = Column(String(255), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Input/Output
    input_dataset_version = Column(String(36), nullable=True)  # Reference to DatasetVersion
    output_dataset_version = Column(String(36), nullable=True)

    # Metrics
    records_processed = Column(Integer, nullable=True)
    records_errors = Column(Integer, nullable=True)
    records_warnings = Column(Integer, nullable=True)

    # Logs  
    logs = Column(Text, nullable=True)  # Execution logs
    error_details = Column(JSON, nullable=True)  # Error stack trace, etc

    def __repr__(self):
        return f"<PipelineRun {self.city}:{self.stage} {self.status}>"


class DataLineage(Base):
    """
    Track data lineage and transformations.

    Schema for tracking how data flows through pipeline.
    """

    __tablename__ = "data_lineage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_dataset_id = Column(String(36), nullable=False)  # DatasetVersion.id
    target_dataset_id = Column(String(36), nullable=False)  # DatasetVersion.id
    transformation_type = Column(String(100), nullable=False)  # e.g., "merge", "clean", "aggregate"
    pipeline_run_id = Column(String(36), nullable=True)  # Reference to PipelineRun

    # Transformation details
    transformation_config = Column(JSON, nullable=True)  # Config used for transformation
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<DataLineage {self.source_dataset_id} -> {self.target_dataset_id}>"


class DataQuality(Base):
    """
    Track data quality metrics.

    Schema for storing data quality checks and metrics.
    """

    __tablename__ = "data_quality"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_version_id = Column(String(36), nullable=False, index=True)
    check_name = Column(String(255), nullable=False)  # e.g., "duplicate_records", "null_values"
    status = Column(String(50), nullable=False)  # "pass", "warning", "fail"

    # Metrics
    total_records = Column(Integer, nullable=True)
    records_affected = Column(Integer, nullable=True)
    percentage_affected = Column(Integer, nullable=True)

    # Details
    details = Column(JSON, nullable=True)  # {sample_records, threshold, etc}
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<DataQuality {self.check_name}: {self.status}>"


# ============================================================================
# SERVICE LAYER
# ============================================================================


class DataVersioningService:
    """
    Service for managing data versioning and lineage.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_dataset_version(
        self,
        dataset_name: str,
        city: str,
        stage: PipelineStage,
        source: str,
        record_count: int,
        file_size_bytes: Optional[int] = None,
        schema_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DatasetVersion:
        """Create new dataset version record."""

        # Generate semantic version
        existing_versions = (
            self.session.query(DatasetVersion)
            .filter_by(dataset_name=dataset_name, city=city, stage=stage)
            .all()
        )

        version_num = len(existing_versions) + 1
        version = f"1.{version_num}.0"

        dataset_version = DatasetVersion(
            dataset_name=dataset_name,
            city=city,
            stage=stage,
            version=version,
            source=source,
            record_count=record_count,
            file_size_bytes=file_size_bytes,
            schema_hash=schema_hash,
            metadata=metadata or {},
        )

        self.session.add(dataset_version)
        self.session.commit()

        return dataset_version

    def create_pipeline_run(
        self,
        city: str,
        stage: PipelineStage,
        task_name: str,
        input_dataset_version: Optional[str] = None,
    ) -> PipelineRun:
        """Create new pipeline run record."""

        run = PipelineRun(
            city=city,
            stage=stage,
            task_name=task_name,
            input_dataset_version=input_dataset_version,
            status="running",
        )

        self.session.add(run)
        self.session.commit()

        return run

    def complete_pipeline_run(
        self,
        run_id: str,
        status: str,
        output_dataset_version: Optional[str] = None,
        records_processed: Optional[int] = None,
        records_errors: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ):
        """Mark pipeline run as completed."""

        run = self.session.query(PipelineRun).filter_by(id=run_id).first()

        if run:
            run.status = status
            run.completed_at = datetime.utcnow()
            run.output_dataset_version = output_dataset_version
            run.records_processed = records_processed
            run.records_errors = records_errors
            run.duration_seconds = duration_seconds
            run.error_details = error_details

            self.session.commit()

    def record_lineage(
        self,
        source_dataset_id: str,
        target_dataset_id: str,
        transformation_type: str,
        pipeline_run_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> DataLineage:
        """Record data lineage."""

        lineage = DataLineage(
            source_dataset_id=source_dataset_id,
            target_dataset_id=target_dataset_id,
            transformation_type=transformation_type,
            pipeline_run_id=pipeline_run_id,
            transformation_config=config,
        )

        self.session.add(lineage)
        self.session.commit()

        return lineage

    def record_quality_check(
        self,
        dataset_version_id: str,
        check_name: str,
        status: str,
        total_records: int,
        records_affected: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> DataQuality:
        """Record data quality check result."""

        percentage = (
            int((records_affected / total_records) * 100)
            if records_affected and total_records > 0
            else 0
        )

        quality = DataQuality(
            dataset_version_id=dataset_version_id,
            check_name=check_name,
            status=status,
            total_records=total_records,
            records_affected=records_affected,
            percentage_affected=percentage,
            details=details,
        )

        self.session.add(quality)
        self.session.commit()

        return quality

    def get_lineage_for_dataset(self, dataset_version_id: str) -> Dict[str, Any]:
        """Get complete lineage history for a dataset."""

        lineage_records = self.session.query(DataLineage).filter_by(
            target_dataset_id=dataset_version_id
        ).all()

        return {
            "dataset_version_id": dataset_version_id,
            "lineage_count": len(lineage_records),
            "lineages": [
                {
                    "source_id": line.source_dataset_id,
                    "transformation": line.transformation_type,
                    "created_at": line.created_at.isoformat(),
                }
                for line in lineage_records
            ],
        }

    def get_quality_report(self, dataset_version_id: str) -> Dict[str, Any]:
        """Get quality report for a dataset."""

        quality_records = self.session.query(DataQuality).filter_by(
            dataset_version_id=dataset_version_id
        ).all()

        passed = len([q for q in quality_records if q.status == "pass"])
        warnings = len([q for q in quality_records if q.status == "warning"])
        failures = len([q for q in quality_records if q.status == "fail"])

        return {
            "dataset_version_id": dataset_version_id,
            "total_checks": len(quality_records),
            "passed": passed,
            "warnings": warnings,
            "failures": failures,
            "score": int((passed / len(quality_records) * 100)) if quality_records else 0,
            "checks": [
                {
                    "name": q.check_name,
                    "status": q.status,
                    "affected": q.records_affected,
                    "percentage": q.percentage_affected,
                }
                for q in quality_records
            ],
        }
