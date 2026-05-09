"""
Pipeline Orchestrator - Main Controller
Điều phối toàn bộ OSM Data Pipeline từ Bronze đến Gold
"""
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from pipelines.ingestion.osm_ingestion import OSMIngestionEngine
from pipelines.bronze.osm_processor import BronzeOSMProcessor
from pipelines.silver.silver_processor import SilverProcessor
from pipelines.validators.data_validator import DataValidator
from pipelines.shared.schemas import POICategory, PipelineConfig, SourceType
from pipelines.shared.utils import setup_logging, save_json_file

logger = setup_logging(__name__)


class PipelineOrchestrator:
    """Main orchestrator cho OSM Data Pipeline"""
    
    def __init__(self, config_path: str = "pipelines/config"):
        self.config_path = Path(config_path)
        self.ingestion_engine = None
        self.bronze_processor = None
        self.silver_processor = None
        self.validator = None
        self.pipeline_config = None
        self.load_configuration()
    
    def load_configuration(self):
        """Load pipeline configuration"""
        try:
            config_file = self.config_path / "pipeline_config.json"
            if config_file.exists():
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.pipeline_config = PipelineConfig(**config_data)
            else:
                # Default configuration
                self.pipeline_config = PipelineConfig(
                    source=SourceType.OSM,
                    cities=["hanoi", "danang", "dalat", "hue", "cantho", "haiphong", "nhatrang", "vungtau"],
                    categories=[
                        POICategory.TOURIST_ATTRACTION,
                        POICategory.RESTAURANT,
                        POICategory.HOTEL,
                        POICategory.CAFE,
                        POICategory.SHOPPING_MALL,
                        POICategory.PARK,
                        POICategory.CINEMA,
                        POICategory.MUSEUM
                    ],
                    batch_size=1000,
                    max_retries=3,
                    timeout_seconds=60,
                    enable_validation=True,
                    enable_deduplication=True,
                    enable_enrichment=True
                )
                # Save default config
                save_json_file(self.pipeline_config.dict(), config_file)
            
            logger.info(f"✅ Loaded pipeline configuration: {len(self.pipeline_config.cities)} cities")
            
        except Exception as e:
            logger.error(f"❌ Error loading pipeline configuration: {e}")
            raise
    
    def initialize_components(self):
        """Initialize all pipeline components"""
        try:
            logger.info("🔧 Initializing pipeline components...")
            
            self.ingestion_engine = OSMIngestionEngine()
            self.bronze_processor = BronzeOSMProcessor()
            self.silver_processor = SilverProcessor()
            self.validator = DataValidator()
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            raise
    
    async def run_ingestion_phase(self) -> Dict[str, Any]:
        """Phase 1: Raw data ingestion"""
        logger.info("🚀 Starting Phase 1: Raw Data Ingestion")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            results = await self.ingestion_engine.ingest_all(
                cities=self.pipeline_config.cities,
                categories=self.pipeline_config.categories
            )
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            phase_result = {
                "phase": "ingestion",
                "status": "completed" if results["failed"] == 0 else "partial",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "processing_time_seconds": processing_time,
                "results": results,
                "success_rate": results["successful"] / results["total_jobs"] * 100
            }
            
            logger.info(f"✅ Phase 1 completed in {processing_time:.2f}s")
            logger.info(f"📊 Success rate: {phase_result['success_rate']:.1f}%")
            
            return phase_result
            
        except Exception as e:
            logger.error(f"❌ Phase 1 failed: {e}")
            return {
                "phase": "ingestion",
                "status": "failed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def run_bronze_processing_phase(self) -> Dict[str, Any]:
        """Phase 2: Bronze layer processing"""
        logger.info("🔄 Starting Phase 2: Bronze Layer Processing")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            results = self.bronze_processor.process_all(
                cities=self.pipeline_config.cities,
                categories=self.pipeline_config.categories
            )
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            phase_result = {
                "phase": "bronze_processing",
                "status": "completed" if results["failed_jobs"] == 0 else "partial",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "processing_time_seconds": processing_time,
                "results": results,
                "success_rate": results["processed_jobs"] / results["total_jobs"] * 100
            }
            
            logger.info(f"✅ Phase 2 completed in {processing_time:.2f}s")
            logger.info(f"📊 Success rate: {phase_result['success_rate']:.1f}%")
            logger.info(f"📊 Total places processed: {results['total_places']}")
            
            return phase_result
            
        except Exception as e:
            logger.error(f"❌ Phase 2 failed: {e}")
            return {
                "phase": "bronze_processing",
                "status": "failed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def run_silver_processing_phase(self) -> Dict[str, Any]:
        """Phase 3: Silver layer processing"""
        logger.info("⚡ Starting Phase 3: Silver Layer Processing")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            results = self.silver_processor.process_all(
                cities=self.pipeline_config.cities,
                categories=self.pipeline_config.categories
            )
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            phase_result = {
                "phase": "silver_processing",
                "status": "completed" if results["failed_jobs"] == 0 else "partial",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "processing_time_seconds": processing_time,
                "results": results,
                "success_rate": results["processed_jobs"] / results["total_jobs"] * 100
            }
            
            logger.info(f"✅ Phase 3 completed in {processing_time:.2f}s")
            logger.info(f"📊 Success rate: {phase_result['success_rate']:.1f}%")
            logger.info(f"📊 Total Gold places created: {results['total_gold_places']}")
            logger.info(f"📊 Total duplicates removed: {results['total_duplicates_removed']}")
            
            return phase_result
            
        except Exception as e:
            logger.error(f"❌ Phase 3 failed: {e}")
            return {
                "phase": "silver_processing",
                "status": "failed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def run_validation_phase(self) -> Dict[str, Any]:
        """Phase 4: Data validation"""
        logger.info("🔍 Starting Phase 4: Data Validation")
        
        if not self.pipeline_config.enable_validation:
            logger.info("⏭️ Validation disabled, skipping phase")
            return {
                "phase": "validation",
                "status": "skipped",
                "reason": "Validation disabled in configuration"
            }
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Load sample data from each layer for validation
            validation_results = {}
            
            # Validate Bronze layer
            bronze_data = self._load_sample_data("bronze")
            if bronze_data:
                bronze_report = self.validator.validate_dataset(bronze_data, "bronze")
                validation_results["bronze"] = bronze_report
            
            # Validate Silver layer
            silver_data = self._load_sample_data("silver")
            if silver_data:
                silver_report = self.validator.validate_dataset(silver_data, "silver")
                validation_results["silver"] = silver_report
            
            # Validate Gold layer
            gold_data = self._load_sample_data("gold")
            if gold_data:
                gold_report = self.validator.validate_dataset(gold_data, "gold")
                validation_results["gold"] = gold_report
            
            # Generate validation summary
            validation_summary = self.validator.generate_validation_summary(validation_results)
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            phase_result = {
                "phase": "validation",
                "status": "completed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "processing_time_seconds": processing_time,
                "validation_results": validation_results,
                "validation_summary": validation_summary
            }
            
            logger.info(f"✅ Phase 4 completed in {processing_time:.2f}s")
            logger.info(f"📊 Overall quality score: {validation_summary['overall_quality']:.2f}")
            
            return phase_result
            
        except Exception as e:
            logger.error(f"❌ Phase 4 failed: {e}")
            return {
                "phase": "validation",
                "status": "failed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def _load_sample_data(self, layer: str) -> List[Any]:
        """Load sample data cho validation"""
        try:
            if layer == "bronze":
                # Load sample Bronze records
                bronze_path = Path("storage/bronze/osm")
                sample_files = []
                
                for city_dir in bronze_path.iterdir():
                    if city_dir.is_dir():
                        for cat_dir in city_dir.iterdir():
                            if cat_dir.is_dir():
                                files = list(cat_dir.glob("raw_*.json"))
                                if files:
                                    sample_files.extend(files[:1])  # Take 1 file per city/category
                
                # Load data from sample files
                all_data = []
                for file_path in sample_files[:5]:  # Limit to 5 files
                    data = self.validator.load_json_file(file_path)
                    if data and "records" in data:
                        from pipelines.shared.schemas import BronzeRecord
                        for record_data in data["records"]:
                            try:
                                record = BronzeRecord(**record_data)
                                all_data.append(record)
                            except:
                                continue
                
                return all_data[:100]  # Limit to 100 records
                
            elif layer == "silver":
                # Load sample Silver places
                silver_path = Path("storage/silver/osm")
                sample_files = []
                
                for city_dir in silver_path.iterdir():
                    if city_dir.is_dir():
                        for cat_dir in city_dir.iterdir():
                            if cat_dir.is_dir():
                                files = list(cat_dir.glob("processed_*.json"))
                                if files:
                                    sample_files.extend(files[:1])
                
                all_data = []
                for file_path in sample_files[:5]:
                    data = self.validator.load_json_file(file_path)
                    if data and "places" in data:
                        from pipelines.shared.schemas import SilverPlace
                        for place_data in data["places"]:
                            try:
                                place = SilverPlace(**place_data)
                                all_data.append(place)
                            except:
                                continue
                
                return all_data[:100]
                
            elif layer == "gold":
                # Load sample Gold places
                gold_path = Path("storage/gold/osm")
                sample_files = list(gold_path.glob("*_master.parquet"))
                
                if not sample_files:
                    sample_files = list(gold_path.glob("*_master.json"))
                
                if sample_files:
                    data = self.validator.load_json_file(sample_files[0])
                    if data and "places" in data:
                        from pipelines.shared.schemas import GoldPlace
                        all_data = []
                        for place_data in data["places"]:
                            try:
                                place = GoldPlace(**place_data)
                                all_data.append(place)
                            except:
                                continue
                        return all_data[:100]
                
            return []
            
        except Exception as e:
            logger.warning(f"Error loading sample data for {layer}: {e}")
            return []
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """Run complete pipeline từ ingestion đến validation"""
        logger.info("🎯 Starting Full OSM Data Pipeline")
        
        pipeline_start = datetime.now(timezone.utc)
        
        # Initialize components
        self.initialize_components()
        
        # Run phases sequentially
        phase_results = {}
        
        # Phase 1: Ingestion
        phase_results["ingestion"] = await self.run_ingestion_phase()
        
        # Phase 2: Bronze Processing
        phase_results["bronze_processing"] = self.run_bronze_processing_phase()
        
        # Phase 3: Silver Processing
        phase_results["silver_processing"] = self.run_silver_processing_phase()
        
        # Phase 4: Validation
        phase_results["validation"] = self.run_validation_phase()
        
        # Generate pipeline summary
        total_time = (datetime.now(timezone.utc) - pipeline_start).total_seconds()
        
        pipeline_summary = {
            "pipeline_id": f"osm_pipeline_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "start_time": pipeline_start.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "total_processing_time_seconds": total_time,
            "configuration": self.pipeline_config.dict(),
            "phase_results": phase_results,
            "overall_status": self._calculate_overall_status(phase_results),
            "performance_metrics": self._calculate_performance_metrics(phase_results)
        }
        
        # Save pipeline report
        self._save_pipeline_report(pipeline_summary)
        
        logger.info("=" * 80)
        logger.info("🎉 PIPELINE EXECUTION COMPLETED")
        logger.info("=" * 80)
        logger.info(f"📊 Overall Status: {pipeline_summary['overall_status']}")
        logger.info(f"⏱️ Total Time: {total_time:.2f}s")
        logger.info(f"📈 Performance: {pipeline_summary['performance_metrics']}")
        
        return pipeline_summary
    
    def _calculate_overall_status(self, phase_results: Dict[str, Any]) -> str:
        """Calculate overall pipeline status"""
        statuses = [result.get("status", "unknown") for result in phase_results.values()]
        
        if "failed" in statuses:
            return "failed"
        elif "partial" in statuses:
            return "partial"
        elif "skipped" in statuses and all(s in ["completed", "skipped"] for s in statuses):
            return "completed_with_skips"
        elif all(s == "completed" for s in statuses):
            return "completed"
        else:
            return "unknown"
    
    def _calculate_performance_metrics(self, phase_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        metrics = {
            "total_phases": len(phase_results),
            "completed_phases": len([r for r in phase_results.values() if r.get("status") == "completed"]),
            "failed_phases": len([r for r in phase_results.values() if r.get("status") == "failed"]),
            "total_processing_time": sum(r.get("processing_time_seconds", 0) for r in phase_results.values()),
            "average_phase_time": 0,
            "success_rates": {}
        }
        
        if metrics["total_phases"] > 0:
            metrics["average_phase_time"] = metrics["total_processing_time"] / metrics["total_phases"]
        
        # Extract success rates
        for phase_name, result in phase_results.items():
            if "success_rate" in result:
                metrics["success_rates"][phase_name] = result["success_rate"]
        
        return metrics
    
    def _save_pipeline_report(self, pipeline_summary: Dict[str, Any]):
        """Save pipeline execution report"""
        try:
            reports_dir = Path("storage/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"pipeline_report_{timestamp}.json"
            
            success = save_json_file(pipeline_summary, report_file)
            if success:
                logger.info(f"📄 Pipeline report saved: {report_file}")
            else:
                logger.error("❌ Failed to save pipeline report")
                
        except Exception as e:
            logger.error(f"❌ Error saving pipeline report: {e}")


async def main():
    """Main function để run full pipeline"""
    orchestrator = PipelineOrchestrator()
    results = await orchestrator.run_full_pipeline()
    return results


if __name__ == "__main__":
    asyncio.run(main())
