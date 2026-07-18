import { RadarChart, ScatterChart } from "echarts/charts";
import { GridComponent, RadarComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  RadarChart,
  ScatterChart,
  GridComponent,
  RadarComponent,
  TooltipComponent,
  CanvasRenderer,
]);

export { echarts };
