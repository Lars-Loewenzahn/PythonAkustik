from Presentation_1.gant import draw_gantt_schedule
for i in range(1, 8):
    draw_gantt_schedule(
        save_path=f"Presentation_1/gantt_sprint_{i}.png",
        show=False,
        json_path=f"Presentation_1/gantt_sprint_{i}.json"
    )
draw_gantt_schedule(
    save_path="Presentation_1/gantt_overall.png",
    show=False,
    json_path="Presentation_1/gantt_overall.json"
)