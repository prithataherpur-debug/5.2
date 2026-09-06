import { useState } from "react";
import { View, LayoutChangeEvent } from "react-native";
import Svg, { Polyline, Line, Circle, Text as SvgText } from "react-native-svg";
import { theme } from "@/src/lib/theme";

export type ChartPoint = { label: string; value: number };

function compact(n: number): string {
  const a = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  if (a >= 10000000) return `${sign}₹${(a / 10000000).toFixed(1)}Cr`;
  if (a >= 100000) return `${sign}₹${(a / 100000).toFixed(1)}L`;
  if (a >= 1000) return `${sign}₹${(a / 1000).toFixed(1)}k`;
  return `${sign}₹${Math.round(a)}`;
}

export default function NetProfitChart({ data, height = 180 }: { data: ChartPoint[]; height?: number }) {
  const [w, setW] = useState(0);
  const onLayout = (e: LayoutChangeEvent) => setW(e.nativeEvent.layout.width);

  const n = data.length;
  const padL = 8;
  const padR = 12;
  const padT = 18;
  const padB = 26;
  const plotW = Math.max(0, w - padL - padR);
  const plotH = height - padT - padB;

  const values = data.map((d) => d.value);
  let yMax = Math.max(0, ...values);
  let yMin = Math.min(0, ...values);
  if (yMax === yMin) { yMax += 1; yMin -= 1; }
  const pad = (yMax - yMin) * 0.15;
  yMax += pad; yMin -= pad;

  const x = (i: number) => padL + (n <= 1 ? plotW / 2 : (i / (n - 1)) * plotW);
  const y = (v: number) => padT + (1 - (v - yMin) / (yMax - yMin)) * plotH;

  const points = data.map((d, i) => `${x(i)},${y(d.value)}`).join(" ");
  const zeroY = y(0);
  const showZero = yMin < 0 && yMax > 0;
  const last = data[n - 1];

  return (
    <View onLayout={onLayout} style={{ height }} testID="net-profit-chart">
      {w > 0 && n > 0 ? (
        <Svg width={w} height={height}>
          {showZero ? (
            <Line x1={padL} y1={zeroY} x2={w - padR} y2={zeroY} stroke={theme.color.border} strokeWidth={1} strokeDasharray="4 4" />
          ) : null}
          {n > 1 ? (
            <Polyline
              points={points}
              fill="none"
              stroke={theme.color.brand}
              strokeWidth={2.5}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ) : null}
          {data.map((d, i) => (
            <Circle
              key={`c${i}`}
              cx={x(i)}
              cy={y(d.value)}
              r={3.5}
              fill={d.value < 0 ? theme.color.error : theme.color.success}
              stroke={theme.color.surface}
              strokeWidth={1.5}
            />
          ))}
          {data.map((d, i) => (
            i === 0 || i === n - 1 || n <= 6 ? (
              <SvgText key={`x${i}`} x={x(i)} y={height - 9} fontSize={9} fill={theme.color.muted} textAnchor="middle">
                {d.label}
              </SvgText>
            ) : null
          ))}
          {last ? (
            <SvgText
              x={x(n - 1)}
              y={Math.max(12, y(last.value) - 9)}
              fontSize={10}
              fontWeight="bold"
              fill={last.value < 0 ? theme.color.error : theme.color.onSurface}
              textAnchor="end"
            >
              {compact(last.value)}
            </SvgText>
          ) : null}
        </Svg>
      ) : null}
    </View>
  );
}
