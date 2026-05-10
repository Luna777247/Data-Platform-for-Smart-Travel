"""
Pipeline Orchestrator
=====================

Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/pipelines/orchestration/pipeline_orchestrator.py

Main orchestrator cho Smart Tourism Data Platform.
Quản lý vòng đời của pipelines: bronze -> silver -> gold.

Responsibilities:
- Điều phối các pipeline stages
- Quản lý dependencies giữa các stages
- Xử lý lỗi và retry logic
- Reporting và monitoring

Usage:
    orchestrator = PipelineOrchestrator()
    await orchestrator.run_bronze_pipeline(city="hanoi")
    await orchestrator.run_silver_pipeline(city="hanoi")
    await orchestrator.run_gold_pipeline(city="hanoi")
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from src.collectors.google_places_collector import GooglePlacesCollector
from src.pipelines.enrichment.category_enrichment import CategoryEnricher
from src.pipelines.enrichment.business_enrichment import BusinessScorer
from src.db.repositories.poi_repository import POIRepository
from src.pipelines.monitoring.metrics_collector import MetricsCollector
from src.pipelines.monitoring.quality_monitor import QualityMonitor

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stages theo medallion architecture."""
    BRONZE = "bronze"  # Raw data ingestion
    SILVER = "silver"  # Cleaned & enriched
    GOLD = "gold"      # Aggregated & business-ready


class PipelineStatus(Enum):
    """Trạng thái pipeline execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class PipelineExecution:
    """Thông tin về một pipeline execution."""
    execution_id: str
    city: str
    stage: PipelineStage
    status: PipelineStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    records_processed: int = 0
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


class PipelineOrchestrator:
    """
    Main orchestrator cho data pipelines.
    
    Quản lý flow: Bronze -> Silver -> Gold với proper error handling
    và monitoring integration.
    
    Attributes:
        max_retries: Số lần retry tối đa cho failed tasks
        retry_delay: Delay giữa các lần retry (seconds)
        concurrent_limit: Số pipeline concurrent tối đa
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: int = 5,
        concurrent_limit: int = 5
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.concurrent_limit = concurrent_limit
        
        # Components
        self.collector = GooglePlacesCollector()
        self.category_enricher = CategoryEnricher()
        self.business_scorer = BusinessScorer()
        self.poi_repository = POIRepository()
        self.metrics = MetricsCollector()
        self.quality_monitor = QualityMonitor()
        
        # Execution tracking
        self._executions: Dict[str, PipelineExecution] = {}
        self._semaphore = asyncio.Semaphore(concurrent_limit)
        
        logger.info(f"PipelineOrchestrator initialized (max_retries={max_retries}, "
                   f"concurrent_limit={concurrent_limit})")
    
    async def run_full_pipeline(
        self,
        city: str,
        poi_types: Optional[List[str]] = None,
        skip_bronze: bool = False,
        skip_silver: bool = False,
        skip_gold: bool = False
    ) -> PipelineExecution:
        """
        Chạy full pipeline: bronze -> silver -> gold.
        
        Args:
            city: Thành phố cần collect data
            poi_types: Danh sách POI types (None = all types)
            skip_bronze: Skip bronze stage nếu data đã có
            skip_silver: Skip silver stage
            skip_gold: Skip gold stage
            
        Returns:
            PipelineExecution với thông tin execution
        """
        execution_id = f"full_{city}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting full pipeline for {city} (execution_id={execution_id})")
        
        try:
            # Stage 1: Bronze (Raw data collection)
            if not skip_bronze:
                bronze_exec = await self.run_bronze_pipeline(city, poi_types)
                if bronze_exec.status == PipelineStatus.FAILED:
                    raise Exception(f"Bronze pipeline failed: {bronze_exec.error_message}")
            
            # Stage 2: Silver (Cleaning & enrichment)
            if not skip_silver:
                silver_exec = await self.run_silver_pipeline(city)
                if silver_exec.status == PipelineStatus.FAILED:
                    raise Exception(f"Silver pipeline failed: {silver_exec.error_message}")
            
            # Stage 3: Gold (Aggregation & business logic)
            if not skip_gold:
                gold_exec = await self.run_gold_pipeline(city)
                if gold_exec.status == PipelineStatus.FAILED:
                    raise Exception(f"Gold pipeline failed: {gold_exec.error_message}")
            
            # Success
            execution = PipelineExecution(
                execution_id=execution_id,
                city=city,
                stage=PipelineStage.GOLD,
                status=PipelineStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            self._executions[execution_id] = execution
            self.metrics.record_pipeline_completion(city, "full")
            
            logger.info(f"Full pipeline completed for {city} ({execution_id})")
            return execution
            
        except Exception as e:
            logger.error(f"Full pipeline failed for {city}: {e}")
            
            execution = PipelineExecution(
                execution_id=execution_id,
                city=city,
                stage=PipelineStage.BRONZE,
                status=PipelineStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=str(e)
            )
            self._executions[execution_id] = execution
            self.metrics.record_pipeline_failure(city, "full", str(e))
            return execution
    
    async def run_bronze_pipeline(
        self,
        city: str,
        poi_types: Optional[List[str]] = None
    ) -> PipelineExecution:
        """
        Chạy bronze pipeline: Collect raw data từ Google Places API.
        
        Args:
            city: Thành phố cần collect
            poi_types: Loại POI cần collect
            
        Returns:
            PipelineExecution với kết quả
        """
        execution_id = f"bronze_{city}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting bronze pipeline for {city}")
        
        execution = PipelineExecution(
            execution_id=execution_id,
            city=city,
            stage=PipelineStage.BRONZE,
            status=PipelineStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        self._executions[execution_id] = execution
        
        try:
            async with self._semaphore:
                # Collect data từ Google Places
                collected_data = await self.collector.collect_city_data(
                    city=city,
                    poi_types=poi_types
                )
                
                # Store raw data to bronze layer
                records_count = await self.poi_repository.store_bronze_data(
                    city=city,
                    data=collected_data
                )
                
                # Update execution
                execution.status = PipelineStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.records_processed = records_count
                execution.metrics["collected_count"] = len(collected_data)
                
                self.metrics.record_pipeline_completion(city, "bronze", records_count)
                
                logger.info(f"Bronze pipeline completed for {city}: {records_count} records")
                return execution
                
        except Exception as e:
            logger.error(f"Bronze pipeline failed for {city}: {e}")
            execution.status = PipelineStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self.metrics.record_pipeline_failure(city, "bronze", str(e))
            return execution
    
    async def run_silver_pipeline(self, city: str) -> PipelineExecution:
        """
        Chạy silver pipeline: Clean & enrich bronze data.
        
        Args:
            city: Thành phố cần process
            
        Returns:
            PipelineExecution với kết quả
        """
        execution_id = f"silver_{city}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting silver pipeline for {city}")
        
        execution = PipelineExecution(
            execution_id=execution_id,
            city=city,
            stage=PipelineStage.SILVER,
            status=PipelineStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        self._executions[execution_id] = execution
        
        try:
            async with self._semaphore:
                # Read bronze data
                bronze_data = await self.poi_repository.get_bronze_data(city=city)
                
                if not bronze_data:
                    logger.warning(f"No bronze data found for {city}")
                    execution.status = PipelineStatus.COMPLETED
                    execution.completed_at = datetime.utcnow()
                    return execution
                
                # Clean & enrich data
                cleaned_data = []
                for poi in bronze_data:
                    try:
                        # Category enrichment
                        enriched = await self.category_enricher.enrich(poi)
                        # Business scoring
                        scored = await self.business_scorer.score(enriched)
                        cleaned_data.append(scored)
                    except Exception as enrich_error:
                        logger.warning(f"Failed to enrich POI {poi.get('place_id')}: {enrich_error}")
                        continue
                
                # Store to silver layer
                records_count = await self.poi_repository.store_silver_data(
                    city=city,
                    data=cleaned_data
                )
                
                # Quality check
                quality_score = await self.quality_monitor.check_silver_quality(
                    city=city,
                    data=cleaned_data
                )
                
                # Update execution
                execution.status = PipelineStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.records_processed = records_count
                execution.metrics["quality_score"] = quality_score
                execution.metrics["enriched_count"] = len(cleaned_data)
                
                self.metrics.record_pipeline_completion(city, "silver", records_count)
                
                logger.info(f"Silver pipeline completed for {city}: {records_count} records, "
                           f"quality={quality_score:.2f}")
                return execution
                
        except Exception as e:
            logger.error(f"Silver pipeline failed for {city}: {e}")
            execution.status = PipelineStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self.metrics.record_pipeline_failure(city, "silver", str(e))
            return execution
    
    async def run_gold_pipeline(self, city: str) -> PipelineExecution:
        """
        Chạy gold pipeline: Aggregate data cho business use cases.
        
        Args:
            city: Thành phố cần aggregate
            
        Returns:
            PipelineExecution với kết quả
        """
        execution_id = f"gold_{city}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting gold pipeline for {city}")
        
        execution = PipelineExecution(
            execution_id=execution_id,
            city=city,
            stage=PipelineStage.GOLD,
            status=PipelineStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        self._executions[execution_id] = execution
        
        try:
            async with self._semaphore:
                # Read silver data
                silver_data = await self.poi_repository.get_silver_data(city=city)
                
                if not silver_data:
                    logger.warning(f"No silver data found for {city}")
                    execution.status = PipelineStatus.COMPLETED
                    execution.completed_at = datetime.utcnow()
                    return execution
                
                # Aggregate by category
                category_stats = self._aggregate_by_category(silver_data)
                
                # Aggregate by district
                district_stats = self._aggregate_by_district(silver_data)
                
                # Calculate business insights
                insights = self._calculate_business_insights(silver_data)
                
                # Store to gold layer
                gold_data = {
                    "pois": silver_data,
                    "category_stats": category_stats,
                    "district_stats": district_stats,
                    "insights": insights,
                    "aggregated_at": datetime.utcnow().isoformat()
                }
                
                records_count = await self.poi_repository.store_gold_data(
                    city=city,
                    data=gold_data
                )
                
                # Update execution
                execution.status = PipelineStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.records_processed = records_count
                execution.metrics["category_count"] = len(category_stats)
                execution.metrics["district_count"] = len(district_stats)
                
                self.metrics.record_pipeline_completion(city, "gold", records_count)
                
                logger.info(f"Gold pipeline completed for {city}: {records_count} records")
                return execution
                
        except Exception as e:
            logger.error(f"Gold pipeline failed for {city}: {e}")
            execution.status = PipelineStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self.metrics.record_pipeline_failure(city, "gold", str(e))
            return execution
    
    def _aggregate_by_category(self, pois: List[Dict]) -> Dict[str, Any]:
        """Aggregate POIs by category."""
        stats = {}
        for poi in pois:
            category = poi.get("category", "unknown")
            if category not in stats:
                stats[category] = {"count": 0, "avg_rating": 0, "total_reviews": 0}
            stats[category]["count"] += 1
            stats[category]["avg_rating"] += poi.get("rating", 0)
            stats[category]["total_reviews"] += poi.get("user_ratings_total", 0)
        
        # Calculate averages
        for category in stats:
            if stats[category]["count"] > 0:
                stats[category]["avg_rating"] /= stats[category]["count"]
        
        return stats
    
    def _aggregate_by_district(self, pois: List[Dict]) -> Dict[str, Any]:
        """Aggregate POIs by district/area."""
        stats = {}
        for poi in pois:
            district = poi.get("district", "unknown")
            if district not in stats:
                stats[district] = {"count": 0, "categories": set()}
            stats[district]["count"] += 1
            stats[district]["categories"].add(poi.get("category", "unknown"))
        
        # Convert sets to lists for serialization
        for district in stats:
            stats[district]["categories"] = list(stats[district]["categories"])
        
        return stats
    
    def _calculate_business_insights(self, pois: List[Dict]) -> Dict[str, Any]:
        """Calculate business insights từ POI data."""
        if not pois:
            return {}
        
        total_rating = sum(p.get("rating", 0) for p in pois)
        total_reviews = sum(p.get("user_ratings_total", 0) for p in pois)
        
        return {
            "total_pois": len(pois),
            "avg_rating": total_rating / len(pois) if pois else 0,
            "total_reviews": total_reviews,
            "top_rated": sorted(
                pois,
                key=lambda x: x.get("rating", 0),
                reverse=True
            )[:10],
            "most_reviewed": sorted(
                pois,
                key=lambda x: x.get("user_ratings_total", 0),
                reverse=True
            )[:10]
        }
    
    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Lấy thông tin pipeline execution theo ID."""
        return self._executions.get(execution_id)
    
    def get_executions(
        self,
        city: Optional[str] = None,
        stage: Optional[PipelineStage] = None,
        status: Optional[PipelineStatus] = None,
        limit: int = 100
    ) -> List[PipelineExecution]:
        """Lấy danh sách pipeline executions với filter."""
        executions = list(self._executions.values())
        
        if city:
            executions = [e for e in executions if e.city == city]
        if stage:
            executions = [e for e in executions if e.stage == stage]
        if status:
            executions = [e for e in executions if e.status == status]
        
        # Sort by started_at descending
        executions.sort(key=lambda x: x.started_at or datetime.min, reverse=True)
        
        return executions[:limit]
    
    async def cleanup_old_executions(self, days: int = 7) -> int:
        """Xóa old execution records."""
        cutoff = datetime.utcnow() - __import__('datetime').timedelta(days=days)
        to_remove = [
            eid for eid, e in self._executions.items()
            if e.completed_at and e.completed_at < cutoff
        ]
        
        for eid in to_remove:
            del self._executions[eid]
        
        logger.info(f"Cleaned up {len(to_remove)} old executions")
        return len(to_remove)
