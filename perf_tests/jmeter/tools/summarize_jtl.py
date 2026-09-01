from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Stats:
    samples: int
    errors: int
    avg: float
    minimum: int
    maximum: int
    p90: int
    p95: int
    p99: int
    throughput: float


def percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0

    ordered = sorted(values)
    index = int(round((pct / 100) * (len(ordered) - 1)))
    return ordered[index]


def build_stats(rows: list[dict[str, str]]) -> Stats:
    if not rows:
        return Stats(0, 0, 0, 0, 0, 0, 0, 0, 0)

    elapsed_values = [int(row["elapsed"]) for row in rows]
    start_times = [int(row["timeStamp"]) for row in rows]
    end_times = [
        int(row["timeStamp"]) + int(row["elapsed"])
        for row in rows
    ]
    duration_seconds = max((max(end_times) - min(start_times)) / 1000, 0.001)
    errors = sum(1 for row in rows if row.get("success", "").lower() != "true")

    return Stats(
        samples=len(rows),
        errors=errors,
        avg=sum(elapsed_values) / len(elapsed_values),
        minimum=min(elapsed_values),
        maximum=max(elapsed_values),
        p90=percentile(elapsed_values, 90),
        p95=percentile(elapsed_values, 95),
        p99=percentile(elapsed_values, 99),
        throughput=len(rows) / duration_seconds,
    )


def format_stats_row(name: str, stats: Stats) -> str:
    error_rate = (stats.errors / stats.samples * 100) if stats.samples else 0
    return (
        f"| {name} | {stats.samples} | {stats.errors} | {error_rate:.2f}% | "
        f"{stats.avg:.2f} | {stats.minimum} | {stats.maximum} | "
        f"{stats.p90} | {stats.p95} | {stats.p99} | {stats.throughput:.2f} |"
    )


def load_rows(jtl_path: Path) -> list[dict[str, str]]:
    with jtl_path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def build_markdown(
    *,
    rows: list[dict[str, str]],
    plan: str,
    threads: int,
    ramp_up: int,
    loop_count: int,
    duration: int | None,
    target_rps: float | None,
    jtl_path: Path,
) -> str:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("label", "UNKNOWN")].append(row)

    overall = build_stats(rows)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# 性能测试结果汇总 - {plan}",
        "",
        "## 测试配置",
        "",
        f"- 生成时间：{generated_at}",
        f"- 测试计划：`{plan}`",
        f"- 线程数：{threads}",
        f"- Ramp-Up：{ramp_up} 秒",
        f"- 循环次数：{loop_count}",
        f"- JTL 文件：`{jtl_path}`",
        "",
        "## 汇总指标",
        "",
        "| 接口/事务 | Samples | Errors | Error % | Avg(ms) | Min(ms) | Max(ms) | P90(ms) | P95(ms) | P99(ms) | Throughput/s |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        format_stats_row("整体", overall),
    ]

    if duration:
        lines.insert(10, f"- 持续时间：{duration} 秒")
    if target_rps:
        lines.insert(11 if duration else 10, f"- 目标吞吐量：{target_rps:g} req/s")

    for label in sorted(grouped):
        lines.append(format_stats_row(label, build_stats(grouped[label])))

    lines.extend(
        [
            "",
            "## 初步结论",
            "",
            "- 错误率需要结合业务预期判断；如果出现 429，通常说明触发了后端限流。",
            "- Avg 反映平均响应时间，P95/P99 更适合观察大部分用户的慢请求体验。",
            "- 具体场景是否达标，需要结合 `performance_test_plan.md` 中对应压力模型和通过标准判断。",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jtl", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--threads", required=True, type=int)
    parser.add_argument("--ramp-up", required=True, type=int)
    parser.add_argument("--loop-count", required=True, type=int)
    parser.add_argument("--duration", type=int)
    parser.add_argument("--target-rps", type=float)
    args = parser.parse_args()

    rows = load_rows(args.jtl)
    content = build_markdown(
        rows=rows,
        plan=args.plan,
        threads=args.threads,
        ramp_up=args.ramp_up,
        loop_count=args.loop_count,
        duration=args.duration,
        target_rps=args.target_rps,
        jtl_path=args.jtl,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
