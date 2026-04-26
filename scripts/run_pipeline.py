import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import logging
import sys
import subprocess

# Configure Structured Logging (via standard logging for now, extensible to structlog)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PipelineEngine")

async def run_step(name, script_path):
    logger.info(f">>> STARTING STEP: {name}")
    try:
        # Chạy script Python theo batch
        process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        if process.returncode == 0:
            logger.info(f"✅ STEP {name} COMPLETED")
        else:
            logger.error(f"❌ STEP {name} FAILED: {err.decode()}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error in {name}: {e}")
        return False
    return True

async def run_end_to_end():
    logger.info("🚀 INITIATING END-TO-END DATA PIPELINE (PHASE 1)")
    
    # STEP 1: BRONZE (Ingestion)
    if not await run_step("BRONZE_INGESTION", "run_bronze.py"): return
    
    # STEP 2: SILVER (Processing & Quality)
    if not await run_step("SILVER_PROCESSING", "run_silver.py"): return
    
    # STEP 3: SERVING (Postgres Load)
    if not await run_step("POSTGRES_LOAD", "run_postgres_loader.py"): return
    
    # STEP 4: GOLD (Analytics)
    if not await run_step("GOLD_ANALYTICS", "run_gold.py"): return

    logger.info("🏆 PIPELINE RUN FINISHED SUCCESSFULLY")

if __name__ == "__main__":
    asyncio.run(run_end_to_end())
