# SMART TOURISM DATA PLATFORM - RECOMMENDED DIRECTORY STRUCTURE

**Version:** 2.0  
**Created:** May 2026  
**Updated:** May 10, 2026  
**Status:** ✅ Dynamic Plugin Architecture (Truly Extensible)

---

> **🎉 MAJOR UPDATE (May 10, 2026):** System transformed from **Hardcoded** → **Truly Dynamic Plugin Architecture**
> 
> **Key Achievement:** Add unlimited data sources via API without code changes!
> 
> - Before: Fixed 2 sources (OSM, Google) - Code required to add more
> - After: Unlimited sources via Plugin System - Just API call!
> 
> **See:** `docs/PLUGIN_SYSTEM.md` for complete plugin documentation

---

## 🎯 OVERVIEW

Đây là cấu trúc thư mục được đề xuất cho Smart Tourism Data Platform, được thiết kế theo chuẩn enterprise với **Dynamic Plugin Architecture**:

- **🔌 Dynamic Extensibility** - Thêm nguồn dữ liệu mới qua API, không cần code
- **📦 Plugin-Based** - Base interfaces cho collectors và transformers
- **⚡ Hot-Swappable** - Register/unregister plugins runtime
- **🌍 Multi-Source** - Unlimited data sources (OSM, Google, TripAdvisor, Yelp, ...)
- **🏗️ Scalability** - Hỗ trợ multi-source, multi-city scaling
- **🔧 Maintainability** - Clear separation via plugin system
- **📊 Observability** - Comprehensive monitoring và logging
- **🚀 Production Ready** - Deployment và operations ready

---

## 🆚 Architecture Evolution

### Before (Hardcoded) ❌
```
src/collectors/
├── osm_collector.py          # Static
├── google_places_collector.py # Static
└── __init__.py               # __all__ = [2 sources only]
```

### After (Dynamic) ✅
```
src/plugins/                  # Dynamic plugin system
├── base.py                   # Base interfaces
├── registry.py               # Plugin registry (MongoDB-backed)
├── loader.py                 # Dynamic loader
└── collectors/               # Plugin implementations
    ├── __init__.py
    ├── tripadvisor_collector.py  # Example plugin
    ├── yelp_collector.py        # Future plugin
    └── custom/                  # User-defined plugins
```

---

## 📁 RECOMMENDED DIRECTORY STRUCTURE

```
smart-tourism-platform/
├── 📋 README.md                           # Project overview
├── 📋 CHANGELOG.md                         # Version history
├── 📋 CONTRIBUTING.md                      # Development guidelines
├── 📋 LICENSE.md                           # License information
├── 📋 .gitignore                          # Git ignore rules
├── 📋 .env.example                        # Environment template
│
├── 📁 docs/                               # 📚 Documentation
│   ├── README.md                          # Documentation overview
│   ├── MANIFEST.txt                       # Document manifest
│   ├── SMART_TOURISM_DATA_PLATFORM.docx   # Architecture document
│   ├── SMART_TOURISM_DATA_PLATFORM_Architecture.md
│   ├── SMART_TOURISM_DEVELOPER_GUIDE.md
│   ├── SMART_TOURISM_SCHEMAS.json
│   ├── SMART_TOURISM_CHEATSHEET.md
│   ├── RECOMMENDED_STRUCTURE.md           # This file
│   ├── PLUGIN_SYSTEM.md                   # ⭐ Plugin architecture guide
│   ├── PLUGIN_IMPLEMENTATION_SUMMARY.md   # ⭐ Implementation details
│   ├── api/                               # API documentation
│   │   ├── openapi.yaml                   # OpenAPI spec
│   │   ├── postman_collection.json        # Postman collection
│   │   └── plugins/                       # ⭐ Plugin API docs
│   │       ├── plugin_registration.md
│   │       └── source_configuration.md
│   └── deployment/                        # Deployment guides
│       ├── docker.md                      # Docker deployment
│       ├── kubernetes.md                  # K8s deployment
│       └── production.md                  # Production setup
│
├── 📁 src/                                # 🔧 Source Code
│   ├── __init__.py
│   ├── main.py                            # Application entry point
│   │
│   ├── 📁 plugins/                        # 🔌 PLUGIN SYSTEM (⭐ NEW)
│   │   ├── __init__.py                    # Package exports
│   │   ├── base.py                        # Base interfaces
│   │   │                                  #   - BasePlugin
│   │   │                                  #   - BaseCollector
│   │   │                                  #   - BaseTransformer
│   │   │                                  #   - BaseEnricher
│   │   ├── registry.py                    # PluginRegistry
│   │   │                                  #   - In-memory storage
│   │   │                                  #   - MongoDB persistence
│   │   ├── loader.py                      # Dynamic loader
│   │   │                                  #   - Load from modules
│   │   │                                  #   - Load from files
│   │   │                                  #   - Load from database
│   │   └── collectors/                    # Collector plugins
│   │       ├── __init__.py
│   │       ├── tripadvisor_collector.py   # Example: TripAdvisor
│   │       ├── yelp_collector.py          # Future: Yelp
│   │       └── custom/                    # User plugins
│   │           ├── README.md              # Custom plugin guide
│   │           └── .gitkeep                 # Preserve directory
│   │
│   ├── 📁 api/                            # 🌐 API Layer
│   │   ├── __init__.py
│   │   ├── routes/                        # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── pipeline_management.py      # Pipeline control APIs
│   │   │   ├── pipeline_minio.py          # ⭐ MinIO pipeline APIs
│   │   │   ├── data_query.py              # Data query APIs
│   │   │   ├── monitoring.py              # Monitoring APIs
│   │   │   ├── health.py                  # Health check APIs
│   │   │   ├── admin.py                   # Admin APIs
│   │   │   ├── auth.py                    # Authentication APIs
│   │   │   └── plugins.py                 # ⭐ PLUGIN MANAGEMENT APIs
│   │   │                                    #   - POST /plugins (register)
│   │   │                                    #   - GET /plugins (list)
│   │   │                                    #   - POST /plugins/sources (config)
│   │   ├── schemas/                       # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py                # Pipeline schemas
│   │   │   ├── data.py                    # Data schemas
│   │   │   ├── monitoring.py              # Monitoring schemas
│   │   │   └── common.py                  # Common schemas
│   │   ├── dependencies/                 # FastAPI dependencies
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                    # Authentication
│   │   │   ├── database.py                # Database connections
│   │   │   └── monitoring.py              # Monitoring setup
│   │   └── middleware/                    # Custom middleware
│   │       ├── __init__.py
│   │       ├── logging.py                 # Logging middleware
│   │       ├── cors.py                    # CORS middleware
│   │       └── rate_limit.py              # Rate limiting
│   │
│   ├── 📁 services/                      # 🏢 Business Logic
│   │   ├── __init__.py
│   │   ├── pipeline_management_service.py # Pipeline control service
│   │   ├── data_query_service.py          # Data query service
│   │   ├── monitoring_service.py         # Monitoring service
│   │   ├── data_quality_service.py        # Data quality service
│   │   ├── notification_service.py        # Notification service
│   │   └── auth_service.py                # Authentication service
│   │
│   ├── 📁 core/                          # 🔧 Core Components
│   │   ├── __init__.py
│   │   ├── config.py                      # Configuration management
│   │   ├── database.py                    # Database setup
│   │   ├── security.py                    # Security utilities
│   │   ├── logging.py                     # Logging setup
│   │   ├── monitoring.py                  # Monitoring setup
│   │   └── exceptions.py                  # Custom exceptions
│   │
│   ├── 📁 db/                            # 🗄️ Database Layer
│   │   ├── __init__.py
│   │   ├── models/                        # MongoDB models
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py                # Pipeline models
│   │   │   ├── poi.py                     # POI models
│   │   │   ├── monitoring.py              # Monitoring models
│   │   │   └── quality.py                 # Quality models
│   │   ├── repositories/                  # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── pipeline_repository.py      # Pipeline repository
│   │   │   ├── poi_repository.py          # POI repository
│   │   │   ├── monitoring_repository.py    # Monitoring repository
│   │   │   └── quality_repository.py       # Quality repository
│   │   └── migrations/                    # Database migrations
│   │       ├── __init__.py
│   │       ├── 001_initial_setup.py       # Initial setup
│   │       └── 002_add_indexes.py         # Index creation
│   │
│   ├── 📁 utils/                         # 🛠️ Utilities
│   │   ├── __init__.py
│   │   ├── auth_utils.py                  # Authentication utilities
│   │   ├── date_utils.py                  # Date utilities
│   │   ├── geo_utils.py                   # Geospatial utilities
│   │   ├── validation_utils.py            # Validation utilities
│   │   ├── monitoring_utils.py            # Monitoring utilities
│   │   └── notification_utils.py          # Notification utilities
│   │
│   └── 📁 tests/                         # 🧪 Tests
│       ├── __init__.py
│       ├── conftest.py                    # Pytest configuration
│       ├── unit/                          # Unit tests
│       │   ├── test_services/             # Service tests
│       │   ├── test_core/                 # Core tests
│       │   └── test_utils/                # Utility tests
│       ├── integration/                   # Integration tests
│       │   ├── test_api/                  # API tests
│       │   ├── test_db/                   # Database tests
│       │   └── test_pipeline/             # Pipeline tests
│       ├── e2e/                           # End-to-end tests
│       │   ├── test_full_pipeline.py      # Full pipeline tests
│       │   └── test_api_integration.py    # API integration tests
│       └── fixtures/                      # Test data
│           ├── sample_data.json           # Sample data
│           └── mock_responses.json        # Mock API responses
│
├── 📁 pipelines/                         # 🔄 Data Processing Pipelines
│   ├── __init__.py
│   ├── README.md                          # Pipeline overview
│   ├── config/                            # Pipeline configurations
│   │   ├── pipeline_config.json          # Main pipeline config
│   │   ├── cities.json                    # Cities configuration
│   │   ├── poi_types.json                 # POI types configuration
│   │   └── sources.json                   # ⭐ Dynamic source configs (via API)
│   │                                        # Sources registered via plugin API
│   │
│   ├── 📁 ingestion/                     # 📥 Data Ingestion (DYNAMIC)
│   │   ├── __init__.py
│   │   ├── base_ingestion.py              # ⭐ Base ingestion (plugin-aware)
│   │   ├── plugin_ingestion.py            # ⭐ Dynamic plugin ingestion
│   │   ├── osm_ingestion.py               # OSM ingestion (uses plugin)
│   │   └── google_ingestion.py            # Google ingestion (uses plugin)
│   │                                        # New sources: NO CODE NEEDED
│   │                                        # Just register plugin via API!
│   │
│   ├── 📁 bronze/                        # 🥉 Bronze Layer (SOURCE-AGNOSTIC)
│   │   ├── __init__.py
│   │   ├── base_processor.py              # ⭐ Source-agnostic processor
│   │   ├── plugin_processor.py            # ⭐ Dynamic processor
│   │   ├── osm_processor.py               # OSM via plugin
│   │   └── google_processor.py            # Google via plugin
│   │                                        # New source → auto-available
│   │
│   ├── 📁 silver/                        # 🥈 Silver Layer (UNIVERSAL)
│   │   ├── __init__.py
│   │   ├── silver_processor.py            # Universal silver processor
│   │   ├── deduplication.py              # Source-agnostic dedup
│   │   ├── normalization.py              # Universal normalization
│   │   └── validation.py                  # Schema validation
│   │                                        # Works with ANY plugin source
│   │
│   ├── 📁 gold/                          # 🥇 Gold Layer (UNIFIED)
│   │   ├── __init__.py
│   │   ├── gold_processor.py              # Universal gold processor
│   │   ├── enrichment.py                  # Plugin-based enrichment
│   │   ├── aggregation.py                 # Multi-source aggregation
│   │   └── indexing.py                    # Search index creation
│   │                                        # Merges ALL plugin sources
│   │
│   ├── 📁 shared/                        # 🔗 Shared Components
│   │   ├── __init__.py
│   │   ├── schemas.py                     # Pydantic schemas
│   │   ├── utils.py                       # Shared utilities
│   │   ├── config.py                      # Shared configuration
│   │   └── constants.py                   # Constants
│   │
│   ├── 📁 collectors/                    # 📥 BUILT-IN COLLECTORS
│   │   ├── __init__.py                    # Exports OSM + Google
│   │   ├── osm_collector.py               # OSM (now plugin-compatible)
│   │   ├── google_places_collector.py     # Google Places (plugin-compatible)
│   │   └── base_collector.py              # Legacy base (deprecated)
│   │                                        # → Use src/plugins/base.py instead
│   │
│   ├── 📁 validators/                     # ✅ Data Validation
│   │   ├── __init__.py
│   │   ├── data_validator.py              # Data validator
│   │   ├── schema_validator.py            # Schema validator
│   │   ├── quality_validator.py           # Quality validator
│   │   └── geo_validator.py               # Geospatial validator
│   │
│   ├── 📁 enrichment/                     # 🎯 Data Enrichment (PLUGIN-BASED)
│   │   ├── __init__.py
│   │   ├── base_enrichment.py             # ⭐ Base enricher interface
│   │   ├── geospatial_enrichment.py       # Geospatial enrichment
│   │   ├── rating_enrichment.py           # Rating enrichment
│   │   ├── category_enrichment.py         # Category enrichment
│   │   ├── business_enrichment.py         # Business scoring
│   │   └── custom/                        # ⭐ Custom enrichers
│   │       └── .gitkeep
│   │
│   ├── 📁 orchestration/                  # 🎼 Pipeline Orchestration
│   │   ├── __init__.py
│   │   ├── pipeline_orchestrator.py       # Plugin-aware orchestrator
│   │   ├── scheduler.py                   # Pipeline scheduler
│   │   ├── executor.py                    # Plugin-based executor
│   │   └── monitoring.py                  # Pipeline monitoring
│   │
│   └── 📁 monitoring/                     # 📊 Pipeline Monitoring
│       ├── __init__.py
│       ├── metrics_collector.py           # Metrics collection
│       ├── quality_monitor.py             # Quality monitoring
│       ├── performance_monitor.py         # Performance monitoring
│       └── alerting.py                    # Alert management
│
├── 📁 storage/                           # 💾 Data Storage
│   ├── 📁 bronze/                         # 🥉 Bronze Layer (SOURCE-AGNOSTIC)
│   │   ├── 📁 {source}/                   # ⭐ Dynamic source folder
│   │   │   ├── 📁 {city}/                 # City-specific
│   │   │   │   └── 📁 {category}/         # Category-specific
│   │   │   │       └── raw_{timestamp}.json
│   │   │   └── 📁 metadata/              # Source metadata
│   │   ├── 📁 osm/                       # OSM (example)
│   │   ├── 📁 google/                    # Google (example)
│   │   └── 📁 {new_source}/              # ⭐ NEW sources auto-created
│   │                                        # Via plugin API registration
│   │
│   ├── 📁 silver/                         # 🥈 Silver Layer (UNIVERSAL)
│   │   ├── 📁 {source}/                   # ⭐ Source subfolder
│   │   │   └── 📁 {city}/
│   │   │       └── processed_{timestamp}.parquet
│   │   ├── 📁 osm/                       # OSM processed
│   │   ├── 📁 google/                    # Google processed
│   │   └── 📁 unified/                    # ⭐ Multi-source unified data
│   │       └── 📁 {city}/
│   │           └── all_sources_{date}.parquet
│   │
│   ├── 📁 gold/                           # 🥇 Gold Layer (AGGREGATED)
│   │   ├── 📁 master_poi/                 # Unified POI (all sources)
│   │   │   └── 📁 {city}/
│   │   │       └── master_poi_{date}.parquet
│   │   ├── 📁 poi_reviews/               # Aggregated reviews
│   │   │   └── 📁 {city}/
│   │   │       └── reviews_{date}.parquet
│   │   └── 📁 quality_reports/           # Quality reports
│   │       └── 📁 {date}/
│   │           └── quality_report_{timestamp}.json
│   │
│   └── 📁 reports/                        # 📊 Reports & Logs
│       ├── 📁 pipeline_reports/          # Pipeline execution reports
│       ├── 📁 quality_reports/           # Data quality reports
│       ├── 📁 monitoring_reports/        # Monitoring reports
│       └── 📁 logs/                       # Application logs
│
├── 📁 deployment/                        # 🚀 Deployment Configuration
│   ├── 📁 docker/                         # Docker configuration
│   │   ├── Dockerfile                     # Main application Dockerfile
│   │   ├── Dockerfile.pipeline            # Pipeline worker Dockerfile
│   │   ├── docker-compose.yml             # Local development
│   │   ├── docker-compose.prod.yml        # Production deployment
│   │   └── docker-compose.dev.yml         # Development deployment
│   │
│   ├── 📁 kubernetes/                     # Kubernetes configuration
│   │   ├── namespace.yaml                 # Namespace definition
│   │   ├── configmap.yaml                 # Configuration maps
│   │   ├── secret.yaml                    # Secrets
│   │   ├── deployment.yaml                # Application deployment
│   │   ├── service.yaml                   # Service definition
│   │   ├── ingress.yaml                   # Ingress configuration
│   │   ├── hpa.yaml                       # Horizontal Pod Autoscaler
│   │   ├── pipeline-deployment.yaml       # Pipeline worker deployment
│   │   └── monitoring/                    # Monitoring stack
│   │       ├── prometheus.yaml            # Prometheus deployment
│   │       ├── grafana.yaml               # Grafana deployment
│   │       └── alertmanager.yaml          # Alertmanager deployment
│   │
│   ├── 📁 terraform/                      # Infrastructure as Code
│   │   ├── main.tf                        # Main Terraform configuration
│   │   ├── variables.tf                   # Variables definition
│   │   ├── outputs.tf                     # Outputs definition
│   │   ├── modules/                       # Terraform modules
│   │   │   ├── vpc/                       # VPC configuration
│   │   │   ├── eks/                       # EKS cluster
│   │   │   ├── rds/                       # RDS database
│   │   │   └── s3/                        # S3 buckets
│   │   └── environments/                  # Environment-specific configs
│   │       ├── dev/                       # Development environment
│   │       ├── staging/                   # Staging environment
│   │       └── prod/                      # Production environment
│   │
│   └── 📁 ansible/                        # Configuration management
│       ├── playbook.yml                  # Main playbook
│       ├── inventory/                     # Host inventory
│       ├── roles/                         # Ansible roles
│       │   ├── common/                    # Common configuration
│       │   ├── database/                  # Database setup
│       │   ├── monitoring/                # Monitoring setup
│       │   └── security/                  # Security hardening
│       └── group_vars/                    # Group variables
│
├── 📁 scripts/                           # 📜 Utility Scripts
│   ├── setup.sh                          # Environment setup
│   ├── deploy.sh                          # Deployment script
│   ├── backup.sh                          # Backup script
│   ├── cleanup.sh                         # Cleanup script
│   ├── monitoring/                        # Monitoring scripts
│   │   ├── health_check.sh                # Health check script
│   │   ├── metrics_collector.sh           # Metrics collection
│   │   └── alerting.sh                   # Alerting script
│   ├── data/                              # Data management scripts
│   │   ├── migrate_data.py                # Data migration
│   │   ├── backup_data.py                 # Data backup
│   │   ├── restore_data.py                # Data restore
│   │   └── cleanup_data.py                # Data cleanup
│   └── testing/                           # Testing scripts
│       ├── run_tests.sh                   # Test runner
│       ├── performance_test.py            # Performance testing
│       └── load_test.py                   # Load testing
│
├── 📁 monitoring/                        # 📊 Monitoring Configuration
│   ├── 📁 prometheus/                     # Prometheus configuration
│   │   ├── prometheus.yml                 # Main configuration
│   │   ├── rules/                         # Alerting rules
│   │   │   ├── pipeline_alerts.yml        # Pipeline alerts
│   │   │   ├── quality_alerts.yml         # Quality alerts
│   │   │   └── performance_alerts.yml     # Performance alerts
│   │   └── targets/                       # Service discovery
│   │       ├── api_targets.yml            # API targets
│   │       └── pipeline_targets.yml       # Pipeline targets
│   │
│   ├── 📁 grafana/                        # Grafana configuration
│   │   ├── dashboards/                    # Grafana dashboards
│   │   │   ├── pipeline_overview.json     # Pipeline overview
│   │   │   ├── data_quality.json          # Data quality
│   │   │   ├── system_performance.json    # System performance
│   │   │   └── business_metrics.json      # Business metrics
│   │   ├── datasources/                   # Data sources
│   │   │   └── prometheus.yml             # Prometheus datasource
│   │   └── provisioning/                  # Auto-provisioning
│   │       ├── dashboards.yml             # Dashboard provisioning
│   │       └── datasources.yml           # Datasource provisioning
│   │
│   ├── 📁 alertmanager/                  # Alertmanager configuration
│   │   ├── alertmanager.yml               # Main configuration
│   │   ├── templates/                     # Alert templates
│   │   │   ├── pipeline.tmpl              # Pipeline alerts
│   │   │   ├── quality.tmpl               # Quality alerts
│   │   │   └── system.tmpl               # System alerts
│   │   └── receivers/                    # Alert receivers
│   │       ├── slack.yml                  # Slack integration
│   │       ├── email.yml                  # Email integration
│   │       └── webhook.yml                # Webhook integration
│   │
│   └── 📁 logs/                           # Log aggregation
│       ├── filebeat.yml                   # Filebeat configuration
│       ├── logstash.yml                   # Logstash configuration
│       └── kibana/                        # Kibana dashboards
│           ├── pipeline_logs.json         # Pipeline logs dashboard
│           └── system_logs.json            # System logs dashboard
│
├── 📁 config/                            # ⚙️ Configuration Files
│   ├── 📁 environments/                  # Environment-specific configs
│   │   ├── development.env                # Development environment
│   │   ├── staging.env                    # Staging environment
│   │   ├── production.env                 # Production environment
│   │   └── testing.env                    # Testing environment
│   ├── 📁 logging/                        # Logging configuration
│   │   ├── development.yml                # Development logging
│   │   ├── production.yml                 # Production logging
│   │   └── testing.yml                    # Testing logging
│   └── 📁 monitoring/                     # Monitoring configuration
│       ├── prometheus.yml                 # Prometheus config
│       ├── grafana.yml                    # Grafana config
│       └── alertmanager.yml              # Alertmanager config
│
├── 📁 tools/                             # 🛠️ Development Tools
│   ├── 📁 airflow/                        # Airflow DAGs
│   │   ├── dags/                          # DAG definitions
│   │   │   ├── osm_pipeline_dag.py        # OSM pipeline DAG
│   │   │   ├── google_pipeline_dag.py     # Google pipeline DAG
│   │   │   ├── quality_check_dag.py       # Quality check DAG
│   │   │   └── monitoring_dag.py          # Monitoring DAG
│   │   ├── plugins/                       # Custom plugins
│   │   │   ├── smart_tourism_hook.py      # Custom hooks
│   │   │   └── smart_tourism_operator.py  # Custom operators
│   │   └── config/                        # Airflow configuration
│   │       ├── airflow.cfg                # Airflow config
│   │       └── connections.json           # Connection configurations
│   │
│   ├── 📁 jupyter/                        # Jupyter notebooks
│   │   ├── data_exploration.ipynb        # Data exploration
│   │   ├── quality_analysis.ipynb         # Quality analysis
│   │   ├── performance_analysis.ipynb     # Performance analysis
│   │   └── ml_experiments.ipynb           # ML experiments
│   │
│   └── 📁 data_quality/                   # Data quality tools
│       ├── quality_checks.py              # Quality check functions
│       ├── anomaly_detection.py           # Anomaly detection
│       ├── data_profiling.py               # Data profiling
│       └── reporting.py                   # Quality reporting
│
├── 📁 .github/                           # 🐙 GitHub Configuration
│   ├── 📁 workflows/                      # GitHub Actions workflows
│   │   ├── ci.yml                         # Continuous Integration
│   │   ├── cd.yml                         # Continuous Deployment
│   │   ├── security.yml                   # Security scanning
│   │   ├── testing.yml                    # Automated testing
│   │   └── monitoring.yml                 # Monitoring setup
│   ├── 📁 templates/                      # Issue templates
│   │   ├── bug_report.md                  # Bug report template
│   │   ├── feature_request.md             # Feature request template
│   │   └── security_issue.md             # Security issue template
│   └── 📁 scripts/                        # GitHub scripts
│       ├── setup.sh                       # Setup script
│       └── deploy.sh                      # Deploy script
│
├── 📁 .vscode/                           # 📝 VS Code Configuration
│   ├── settings.json                     # Editor settings
│   ├── launch.json                        # Debug configuration
│   ├── tasks.json                         # Task configuration
│   └── extensions.json                    # Recommended extensions
│
├── 📁 .idea/                             # 🛠️ IntelliJ IDEA Configuration
│   ├── misc.xml                          # Project configuration
│   ├── modules.xml                       # Module configuration
│   └── workspace.xml                      # Workspace configuration
│
├── 📁 requirements/                      # 📦 Dependencies
│   ├── base.txt                          # Base dependencies
│   ├── development.txt                    # Development dependencies
│   ├── production.txt                    # Production dependencies
│   ├── testing.txt                        # Testing dependencies
│   └── monitoring.txt                     # Monitoring dependencies
│
└── 📁 .git/                             # 📚 Git Configuration
    ├── config/                           # Git configuration
    ├── hooks/                            # Git hooks
    │   ├── pre-commit                     # Pre-commit hook
    │   ├── pre-push                       # Pre-push hook
    │   └── commit-msg                     # Commit message hook
    └── info/                             # Git information
```

---

## 🎯 KEY PRINCIPLES

### **1. Separation of Concerns**
- **API Layer** (`src/api/`) - Xử lý HTTP requests/responses
- **Business Logic** (`src/services/`) - Logic nghiệp vụ
- **Data Layer** (`src/db/`) - Database operations
- **Pipeline Layer** (`pipelines/`) - Data processing pipelines

### **2. Configuration Management**
- **Environment-specific** configs in `config/environments/`
- **Centralized** configuration in `src/core/config.py`
- **Secrets** management through environment variables

### **3. Observability First**
- **Comprehensive monitoring** in `monitoring/`
- **Structured logging** throughout the application
- **Metrics collection** at every layer
- **Alerting** for critical issues

### **4. Scalability Ready**
- **Microservices-friendly** structure
- **Container-ready** with Docker/Kubernetes
- **Horizontal scaling** support
- **Multi-environment** deployment

### **5. Testing Strategy**
- **Unit tests** for business logic
- **Integration tests** for API endpoints
- **End-to-end tests** for full workflows
- **Performance tests** for scalability

---

## 🚀 DEPLOYMENT STRATEGY

### **Development Environment**
```bash
# Local development
docker-compose -f deployment/docker/docker-compose.dev.yml up
```

### **Staging Environment**
```bash
# Staging deployment
kubectl apply -f deployment/kubernetes/
```

### **Production Environment**
```bash
# Production deployment
terraform apply -var-file=environments/prod.tfvars
```

---

## 📊 MONITORING STACK

### **Components**
- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **Alertmanager** - Alert management
- **ELK Stack** - Log aggregation
- **Jaeger** - Distributed tracing

### **Dashboards**
- **Pipeline Overview** - Pipeline execution status
- **Data Quality** - Quality metrics and trends
- **System Performance** - Resource utilization
- **Business Metrics** - KPI dashboards

---

## 🛠️ DEVELOPMENT WORKFLOW

### **1. Setup**
```bash
# Clone repository
git clone <repository-url>
cd smart-tourism-platform

# Setup environment
./scripts/setup.sh

# Install dependencies
pip install -r requirements/development.txt
```

### **2. Development**
```bash
# Start development environment
docker-compose -f deployment/docker/docker-compose.dev.yml up

# Run tests
pytest src/tests/

# Run linting
flake8 src/
black src/
```

### **3. Deployment**
```bash
# Build Docker image
docker build -f deployment/docker/Dockerfile -t smart-tourism-platform .

# Deploy to staging
./scripts/deploy.sh staging

# Deploy to production
./scripts/deploy.sh production
```

---

## � DYNAMIC PLUGIN SYSTEM (⭐ NEW in v2.0)

### **Architecture Overview**

Hệ thống giờ đây sử dụng **Plugin-Based Architecture**, cho phép mở rộng không giới hạn:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PLUGIN REGISTRY                                 │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Registered Sources (DYNAMIC via API)                          │ │
│  │  ├─ osm (built-in)                                            │ │
│  │  ├─ google_places (built-in)                                  │ │
│  │  ├─ tripadvisor (registered via API) ⭐ NEW                   │ │
│  │  ├─ yelp (registered via API) ⭐ NEW                         │ │
│  │  └─ custom_source (user-defined) ⭐ NEW                       │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Dynamic Loading
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIVERSAL PIPELINE                                │
│  Source-Agnostic Processing (works with ANY registered source)      │
│  ├─ Ingestion → Bronze → Silver → Gold                             │
│  ├─ Deduplication (multi-source aware)                             │
│  ├─ Enrichment (plugin-based transformers)                          │
│  └─ Aggregation (unified master POI)                              │
└─────────────────────────────────────────────────────────────────────┘
```

### **Plugin System Structure**

```
src/plugins/                           # 🔌 Plugin System Root
│
├── base.py                            # ⭐ Base Interfaces
│   ├── BasePlugin                     #   Abstract base
│   ├── BaseCollector                  #   Data source interface
│   ├── BaseTransformer                #   Data transform interface
│   └── BaseEnricher                   #   Data enrich interface
│
├── registry.py                        # ⭐ Plugin Registry
│   ├── PluginRegistry                 #   Central registry
│   ├── register_collector()           #   Register new source
│   ├── get_collector()                #   Load plugin instance
│   └── initialize_plugins()           #   Startup initialization
│
├── loader.py                          # ⭐ Dynamic Loader
│   ├── load_from_module()             #   Load from Python module
│   ├── load_from_file()               #   Load from file
│   └── load_from_database()           #   Load from MongoDB
│
└── collectors/                          # Plugin Implementations
    ├── __init__.py
    ├── tripadvisor_collector.py       #   Example: TripAdvisor
    ├── yelp_collector.py              #   Future: Yelp
    └── custom/                        #   ⭐ User plugins
        ├── README.md                  #     How to create custom plugin
        └── .gitkeep
```

### **API Endpoints (8 New Endpoints)**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/plugins` | List all registered plugins |
| `POST` | `/api/v1/plugins` | ⭐ **Register new plugin** |
| `GET` | `/api/v1/plugins/{id}` | Get plugin details |
| `DELETE` | `/api/v1/plugins/{id}` | Unregister plugin |
| `POST` | `/api/v1/plugins/{id}/test` | Test plugin connection |
| `GET` | `/api/v1/plugins/sources` | List configured sources |
| `POST` | `/api/v1/plugins/sources` | ⭐ **Create source instance** |
| `POST` | `/api/v1/plugins/sources/{id}/collect` | ⭐ **Trigger collection** |

### **Adding New Source (No Code Required!)**

**OLD WAY (Hardcoded):**
```bash
# 1. Write collector class
# 2. Add to src/collectors/__init__.py
# 3. Deploy and restart
# 4. Total time: 2-4 hours
```

**NEW WAY (Dynamic via API):**
```bash
# 1. Register plugin via API (30 seconds)
curl -X POST "http://localhost:8000/api/v1/plugins" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "plugin_id": "tripadvisor",
    "plugin_type": "source",
    "name": "TripAdvisor Collector",
    "class_path": "src.plugins.collectors.tripadvisor_collector.TripAdvisorCollector",
    "config_schema": {
      "api_key": {"type": "string", "required": true},
      "rate_limit": {"type": "integer", "default": 100}
    }
  }'

# 2. Create source instance
curl -X POST "http://localhost:8000/api/v1/plugins/sources" \
  -d '{
    "source_id": "tripadvisor_hanoi",
    "plugin_id": "tripadvisor",
    "name": "TripAdvisor Hanoi",
    "config": {"api_key": "YOUR_KEY"}
  }'

# 3. Start collecting!
curl -X POST "http://localhost:8000/api/v1/plugins/sources/tripadvisor_hanoi/collect?city=hanoi&category=restaurant"

# Total time: 2 minutes! ⚡
```

### **Creating Custom Plugin**

**Step 1: Implement BaseCollector**
```python
# src/plugins/collectors/my_custom_collector.py
from src.plugins.base import BaseCollector
from typing import Dict, List, Any

class MyCustomCollector(BaseCollector):
    @property
    def plugin_name(self) -> str:
        return "my_custom_source"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    async def validate_config(self, config: Dict) -> bool:
        required = ["api_endpoint", "api_key"]
        return all(k in config for k in required)
    
    async def collect(self, city: str, category: str, **kwargs) -> List[Dict]:
        # Your collection logic
        data = await self._fetch_from_api(city, category)
        return data
```

**Step 2: Register via API**
```bash
curl -X POST "http://localhost:8000/api/v1/plugins" \
  -d '{"plugin_id": "my_custom_source", ...}'
```

**Done!** 🎉 No deployment needed!

### **Storage Structure (Source-Agnostic)**

Storage folders are **auto-created** when new sources are registered:

```
storage/
├── bronze/
│   ├── osm/                    # Built-in
│   ├── google/                 # Built-in
│   └── {new_source}/           # ⭐ Auto-created on plugin registration!
│       └── hanoi/
│           └── restaurant/
│               └── raw_20260510.json
```

### **Benefits of Dynamic Architecture**

| Aspect | Before (Hardcoded) | After (Dynamic) |
|--------|-------------------|-----------------|
| **Add new source** | 2-4 hours (code+deploy) | 2 minutes (API call) |
| **Source limit** | Fixed (2 sources) | Unlimited |
| **Developer needed** | Yes | No (for configuration) |
| **Hot-swap** | No (restart required) | Yes (runtime registration) |
| **Testing** | Manual deploy | API test endpoint |
| **Extensibility** | Low | High |

---

## �� DOCUMENTATION STRATEGY

### **Documentation Types**
- **API Documentation** - OpenAPI specs in `docs/api/`
- **Architecture Documentation** - Design documents in `docs/`
- **Plugin Development Guide** - `docs/PLUGIN_SYSTEM.md` ⭐
- **Deployment Guides** - Step-by-step guides in `docs/deployment/`
- **Code Documentation** - Inline comments and docstrings

### **Documentation Maintenance**
- **Auto-generated** API docs from OpenAPI specs
- **Version-controlled** documentation with Git
- **Review process** for documentation changes
- **Regular updates** to match code changes
- **Plugin docs** auto-updated from plugin registry

---

## 🔒 SECURITY CONSIDERATIONS

### **Security Layers**
- **Authentication** - JWT-based authentication
- **Authorization** - Role-based access control
- **Data Encryption** - Encryption at rest and in transit
- **API Security** - Rate limiting and input validation
- **Infrastructure Security** - Network isolation and firewall rules

### **Security Best Practices**
- **Secrets management** through environment variables
- **Regular security scans** in CI/CD pipeline
- **Dependency updates** for security patches
- **Audit logging** for security events

---

## 📈 PERFORMANCE OPTIMIZATION

### **Database Optimization**
- **Indexing strategy** for common queries
- **Connection pooling** for database connections
- **Query optimization** for slow queries
- **Caching strategy** for frequently accessed data

### **Application Optimization**
- **Async processing** for I/O operations
- **Batch processing** for large data operations
- **Memory optimization** for resource usage
- **CPU optimization** for compute-intensive tasks

---

## 🎯 NEXT STEPS

### **Immediate Actions**
1. **Restructure existing code** to match recommended structure
2. **Set up monitoring stack** with Prometheus and Grafana
3. **Implement comprehensive testing** strategy
4. **Create deployment pipelines** with CI/CD

### **Medium-term Goals**
1. **Scale to multiple cities** and data sources
2. **Implement advanced data quality** checks
3. **Add ML capabilities** for predictive analytics
4. **Optimize performance** for production workloads

### **Long-term Vision**
1. **Expand to multiple regions** globally
2. **Add real-time data processing** capabilities
3. **Implement advanced AI/ML** features
4. **Create ecosystem integrations** with third-party services

---

## 📝 CONCLUSION

Cấu trúc thư mục được đề xuất này được thiết kế để hỗ trợ:

✅ **Enterprise-grade scalability** - Hỗ trợ millions of POI records  
✅ **Production-ready deployment** - Docker + Kubernetes + Terraform  
✅ **Comprehensive monitoring** - Prometheus + Grafana + ELK Stack  
✅ **Robust testing** - Unit + Integration + E2E tests  
✅ **Security-first approach** - Authentication + Authorization + Encryption  
✅ **Developer experience** - Clear structure + Good tooling  

**Đây là cấu trúc phù hợp cho một Smart Tourism Data Platform production-ready với mindset Senior Data Engineer + Platform Architect!** 🚀
