import { Router, type IRouter } from "express";
import healthRouter from "./health";
import dataRouter from "./data";
import smarttravelRouter from "./smarttravel";

const router: IRouter = Router();

router.use(healthRouter);
router.use(dataRouter);
router.use(smarttravelRouter);

export default router;
