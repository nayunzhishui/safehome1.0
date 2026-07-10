import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";

import type { AssessmentProfilePosition } from "../../../../shared/types/api";
import { VisualizationState } from "./VisualizationState";

interface ProfileRadarChartProps {
  profile: AssessmentProfilePosition | null;
}

function clampRadarValue(value: number) {
  return Math.max(0, Math.min(100, Math.round((value + 3) * (100 / 6))));
}

export function ProfileRadarChart({ profile }: ProfileRadarChartProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const features = useMemo(() => {
    const selectedCluster = (profile?.clusters || []).find(
      (cluster) => cluster.cluster_id === profile?.position?.cluster_id,
    );
    const dimensionRows = profile?.radar_support?.dimensions || [];
    const dimensions = dimensionRows
      .map((dimension) => ({
        feature_id: dimension.code,
        label: dimension.code,
        z_score: selectedCluster?.dimension_z?.[dimension.code],
      }))
      .filter((dimension): dimension is { feature_id: string; label: string; z_score: number } => typeof dimension.z_score === "number")
      .slice(0, 10);
    if (dimensions.length >= 3) {
      return dimensions;
    }
    return (profile?.feature_profile || []).slice(0, 10);
  }, [profile]);

  useEffect(() => {
    if (!chartRef.current || !profile?.available || features.length === 0) {
      return;
    }

    const chart = echarts.init(chartRef.current);
    chart.setOption({
      color: ["#5f8d72"],
      tooltip: {},
      radar: {
        radius: "64%",
        indicator: features.map((feature) => ({ name: feature.label, max: 100 })),
        axisName: { color: "#5f4d3f", fontSize: 11 },
        splitLine: { lineStyle: { color: "#eadfce" } },
        splitArea: { areaStyle: { color: ["#fffdf8", "#f7efe1"] } },
        axisLine: { lineStyle: { color: "#d6c8b6" } },
      },
      series: [
        {
          type: "radar",
          data: [
            {
              name: "当前填写",
              value: features.map((feature) => clampRadarValue(feature.z_score)),
              areaStyle: { opacity: 0.22 },
            },
          ],
        },
      ],
    });

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [features, profile]);

  if (!profile?.available) {
    return <VisualizationState state="insufficient" message={profile?.reason || "暂无维度雷达数据。"} />;
  }
  if (features.length === 0) {
    return <VisualizationState state="insufficient" message="这条结果缺少可用于雷达图的维度数据。" />;
  }

  const interpretationState = profile.interpretation?.status || profile.position?.interpretation_status || "usable";
  return (
    <>
      {interpretationState !== "usable" ? <VisualizationState state={interpretationState} message={profile.interpretation?.message} /> : null}
      <div ref={chartRef} className="profileChart" aria-label="画像维度雷达图" />
    </>
  );
}
