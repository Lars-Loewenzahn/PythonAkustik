import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime
import matplotlib.dates as mdates
import json
import os


def draw_gantt_schedule(
    save_path="gantt.png",
    show=True,
    json_path="gantt_data.json",
    write_json=True,
    title_fontsize=16,
    axis_label_fontsize=10,
    xtick_fontsize=9,
    ytick_fontsize=7,
    milestone_fontsize=9,
    left_margin=0.35,
    aggregate_by_phase=False,
    merge_gap_days=2.0,
    milestone_stack=True,
    milestone_min_days=2.0,
    milestone_rowspace=0.35,
    milestone_rotation=0,
):
    fig, ax = plt.subplots(figsize=(12, 6), dpi=200)
    if not os.path.isabs(json_path):
        if os.path.exists(json_path):
            pass
        else:
            json_path = os.path.join(os.path.dirname(__file__), json_path)

    phase_order = ["Konzept", "Prototyping", "Producing", "Testing", "Finalisierung"]
    phase_colors = {
        "Konzept": "#4e79a7",
        "Prototyping": "#C20E1A",
        "Producing": "#ff8c00",
        "Testing": "#F1C40F",
        "Finalisierung": "#2ca02c",
    }

    tasks = []

    data_from_json = None
    if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data_from_json = json.load(f)
            if isinstance(data_from_json, dict):
                if "phase_order" in data_from_json and isinstance(data_from_json["phase_order"], list):
                    phase_order = data_from_json["phase_order"]
                if "phase_colors" in data_from_json and isinstance(data_from_json["phase_colors"], dict):
                    phase_colors = data_from_json["phase_colors"]
                task_items = data_from_json.get("tasks", [])
            else:
                task_items = data_from_json
            if task_items:
                loaded_tasks = []
                for t in task_items:
                    s = datetime.fromisoformat(t["start"]) if isinstance(t.get("start"), str) else t.get("start")
                    e = datetime.fromisoformat(t["end"]) if isinstance(t.get("end"), str) else t.get("end")
                    loaded_tasks.append({"phase": t["phase"], "task": t["task"], "start": s, "end": e})
                tasks = loaded_tasks
        except Exception:
            pass

    order_map = {p: i for i, p in enumerate(phase_order)}
    tasks = sorted(tasks, key=lambda t: (order_map.get(t["phase"], len(phase_order)), t["start"]))

    orig_tasks = list(tasks)

    # Auto-aggregate if we're rendering the overall plan
    auto_overall = "overall" in os.path.basename(json_path).lower()
    do_aggregate = aggregate_by_phase or auto_overall
    gap_days = merge_gap_days if not auto_overall else max(merge_gap_days, 3.0)

    if do_aggregate:
        # Build intervals per phase and merge close ones
        by_phase = {}
        for t in tasks:
            by_phase.setdefault(t["phase"], []).append((t["start"], t["end"]))

        merged_by_phase = {}
        gap = gap_days
        for ph, intervals in by_phase.items():
            # sort by start
            intervals = sorted(intervals, key=lambda se: se[0])
            merged = []
            for s, e in intervals:
                if not merged:
                    merged.append([s, e])
                else:
                    prev_s, prev_e = merged[-1]
                    # compare in days
                    if (mdates.date2num(s) - mdates.date2num(prev_e)) <= gap:
                        # extend
                        if e > prev_e:
                            merged[-1][1] = e
                    else:
                        merged.append([s, e])
            merged_by_phase[ph] = merged

        # Recreate task list from merged intervals
        tasks = []
        used_phases = [p for p in phase_order if p in merged_by_phase]
        for ph in used_phases:
            for s, e in merged_by_phase[ph]:
                tasks.append({"phase": ph, "task": ph, "start": s, "end": e})

        # Determine y by phase and count items per phase for labels
        y_labels = used_phases
        counts = {ph: len(by_phase.get(ph, [])) for ph in used_phases}
        y_positions_map = {ph: y for y, ph in zip(range(len(y_labels))[::-1], y_labels)}

        for t in tasks:
            y = y_positions_map[t["phase"]]
            start = mdates.date2num(t["start"])
            end = mdates.date2num(t["end"])
            duration = end - start
            ax.barh(
                y,
                duration,
                left=start,
                height=0.6,
                color=phase_colors.get(t["phase"], "#777777"),
                edgecolor="black",
                linewidth=0.8,
            )

        ax.set_yticks(list(y_positions_map.values()))
        # Sort labels in the same order as ticks (top to bottom) and add counts
        ylabels_sorted = [f"{ph} ({counts.get(ph, 0)})" for ph, y in sorted(y_positions_map.items(), key=lambda kv: -kv[1])]
        ax.set_yticklabels(ylabels_sorted, fontsize=ytick_fontsize)
        n_rows_for_labels = len(y_labels)
    else:
        y_positions = list(range(len(tasks)))[::-1]
        for y, t in zip(y_positions, tasks):
            start = mdates.date2num(t["start"])
            end = mdates.date2num(t["end"])
            duration = end - start
            ax.barh(
                y,
                duration,
                left=start,
                height=0.6,
                color=phase_colors.get(t["phase"], "#777777"),
                edgecolor="black",
                linewidth=0.8,
            )
        ax.set_yticks(y_positions)
        ax.set_yticklabels([f'{t["phase"]}: {t["task"]}' for t in tasks], fontsize=ytick_fontsize)
        n_rows_for_labels = len(tasks)

    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%y"))
    ax.tick_params(axis="x", labelsize=xtick_fontsize)

    ax.grid(axis="x", alpha=0.3)
    ax.set_title(
        "Gantt-Diagramm Projektplanung",
        fontsize=title_fontsize,
        weight="bold",
        pad=25
    )
    ax.set_xlabel("Datum", fontsize=axis_label_fontsize)

    milestones = [
        (datetime(2026, 5, 18), "Zwischenbericht #1"),
        (datetime(2026, 6, 1), "Review #2"),
        (datetime(2026, 6, 15), "Review #3"),
        (datetime(2026, 6, 29), "Review #4"),
        (datetime(2026, 6, 30), "Semesterende"),
        (datetime(2026, 7, 4), "Abgabe 00:01"),
    ]

    if isinstance(data_from_json, dict) and data_from_json.get("milestones"):
        ms = []
        for m in data_from_json["milestones"]:
            try:
                d = datetime.fromisoformat(m["date"]) if isinstance(m.get("date"), str) else m.get("date")
            except Exception:
                d = None
            if d is not None:
                ms.append((d, m.get("label", "")))
        if ms:
            milestones = ms

    # Draw milestone lines and place labels, stacked to avoid overlap
    # 1) draw all lines
    ms_sorted = sorted(milestones, key=lambda ml: ml[0])
    for date, _ in ms_sorted:
        x = mdates.date2num(date)
        ax.axvline(x, color="#444444", linestyle="--", linewidth=1.2)

    # 2) place labels with stacking by min day separation
    label_positions = []  # list of (x, y, text)
    level_last_x = []  # last x per level in date units
    for date, label in ms_sorted:
        x = mdates.date2num(date)
        if milestone_stack:
            placed_level = None
            for li, lastx in enumerate(level_last_x):
                if (x - lastx) > milestone_min_days:
                    placed_level = li
                    level_last_x[li] = x
                    break
            if placed_level is None:
                level_last_x.append(x)
                placed_level = len(level_last_x) - 1
            y = n_rows_for_labels + 0.2 + placed_level * milestone_rowspace
        else:
            y = n_rows_for_labels + 0.2
        label_positions.append((x, y, label))

    for x, y, text in label_positions:
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="bottom",
            fontsize=milestone_fontsize,
            rotation=milestone_rotation,
        )

    # Ensure there is enough top space for stacked labels
    if milestone_stack and level_last_x:
        yl = ax.get_ylim()
        needed_top = n_rows_for_labels + 1 + (len(level_last_x) - 1) * milestone_rowspace
        if yl[1] < needed_top:
            ax.set_ylim(yl[0], needed_top)

    fig.autofmt_xdate()
    fig.tight_layout()
    plt.subplots_adjust(left=left_margin)
    fig.savefig(save_path, dpi=200, bbox_inches="tight")

    if write_json:
        try:
            out = {
                "phase_order": phase_order,
                "phase_colors": phase_colors,
                "tasks": [
                    {
                        "phase": t["phase"],
                        "task": t["task"],
                        "start": (t["start"].date().isoformat() if isinstance(t["start"], datetime) else str(t["start"])) ,
                        "end": (t["end"].date().isoformat() if isinstance(t["end"], datetime) else str(t["end"])) ,
                    }
                    for t in (orig_tasks if aggregate_by_phase else tasks)
                ],
                "milestones": [
                    {
                        "date": (d.date().isoformat() if isinstance(d, datetime) else str(d)),
                        "label": label,
                    }
                    for d, label in milestones
                ],
            }
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    if show:
        plt.show()

    plt.close(fig)


if __name__ == "__main__":
    draw_gantt_schedule()