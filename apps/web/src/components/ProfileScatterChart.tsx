import { useEffect, useRef } from "react";
import * as echarts from "echarts";

import type { AssessmentProfileCluster, AssessmentProfilePosition } from "../../../../shared/types/api";

interface ProfileScatterChartProps {
  profile: AssessmentProfilePosition | null;
}

function clusterPoint(cluster: AssessmentProfileCluster) {
  return cluster.pca_centroid
    ? [cluster.pca_centroid.pc1 ?? 0, cluster.pca_centroid.pc2 ?? 0, cluster.profile_name]
    : null;
}

export function ProfileScatterChart({ profile }: ProfileScatterChartProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chartRef.current || !profile?.available || !profile.position) {
      return;
    }

    const chart = echarts.init(chartRef.current);
    const clusterData = (profile.clusters || []).map(clusterPoint).filter(Boolean);
    const userPoint = [profile.position.pc1 ?? 0, profile.position.pc2 ?? 0, "当前填写"];

    chart.setOption({
      color: ["#5f8d72", "#d68c45"],
      tooltip: {
        trigger: "item",
        formatter: (params: { data?: unknown[] }) => {
          const data = params.data || [];
          return `${data[2] || "位置"}<br/>PC1 ${data[0]}<br/>PC2 ${data[1]}`;
        },
      },
      grid: { left: 38, right: 18, top: 26, bottom: 34 },
      xAxis: { name: "PC1", type: "value", splitLine: { lineStyle: { color: "#eadfce" } } },
      yAxis: { name: "PC2", type: "value", splitLine: { lineStyle: { color: "#eadfce" } } },
      series: [
        {
          name: "群体画像中心",
          type: "scatter",
          data: clusterData,
          symbolSize: 18,
          label: { show: true, formatter: (params: { data?: unknown[] }) => String(params.data?.[2] || ""), position: "top" },
        },
        {
          name: "您在这里",
          type: "scatter",
          data: [userPoint],
          symbolSize: 28,
          itemStyle: { borderColor: "#fff8ee", borderWidth: 3 },
          label: { show: true, formatter: "您在这里", position: "right", fontWeight: 700 },
        },
      ],
    });

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [profile]);

  if (!profile?.available) {
    return <div className="emptyState">{profile?.reason || "暂无画像位置数据。"}</div>;
  }

  return <div ref={chartRef} className="profileChart" aria-label="画像散点落点图" />;
}
