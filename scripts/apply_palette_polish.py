from pathlib import Path

path = Path('figures/materialize.py')
text = path.read_text()
old = '''    handles = []
    labels = []
    if spec["renderer"] == "timeseries_bar":
        measurement, dates, values, unit_label, family = prepared[0]
        bar_width = 0.8 if measurement.frequency == "daily" else 24
        handle = axes[family].bar(
            dates, values, width=bar_width, label=measurement.indicator_label
        )
        handles.append(handle)
        labels.append(measurement.indicator_label)
        if spec.get("overrides", {}).get("zero_baseline"):
            axes[family].axhline(0, linewidth=1.0, alpha=0.65)
    else:
        for measurement, dates, values, _, family in prepared:
            (line,) = axes[family].plot(
                dates, values, linewidth=2.0, label=measurement.indicator_label
            )
            handles.append(line)
            labels.append(measurement.indicator_label)
'''
new = '''    handles = []
    labels = []
    # A twinned Matplotlib Axes owns an independent property cycle. Assign
    # colors from one figure-level cycle so series stay visually distinct
    # even when they live on different y axes.
    palette = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])

    def series_color(index: int):
        return palette[index % len(palette)] if palette else None

    if spec["renderer"] == "timeseries_bar":
        measurement, dates, values, unit_label, family = prepared[0]
        bar_width = 0.8 if measurement.frequency == "daily" else 24
        kwargs = {"color": series_color(0)} if palette else {}
        handle = axes[family].bar(
            dates, values, width=bar_width, label=measurement.indicator_label, **kwargs
        )
        handles.append(handle)
        labels.append(measurement.indicator_label)
        if spec.get("overrides", {}).get("zero_baseline"):
            axes[family].axhline(0, linewidth=1.0, alpha=0.65)
    else:
        for index, (measurement, dates, values, _, family) in enumerate(prepared):
            kwargs = {"color": series_color(index)} if palette else {}
            (line,) = axes[family].plot(
                dates, values, linewidth=2.0, label=measurement.indicator_label, **kwargs
            )
            handles.append(line)
            labels.append(measurement.indicator_label)
'''
if old not in text:
    raise SystemExit('target renderer block not found')
path.write_text(text.replace(old, new))
print('PASS: applied figure-level series color cycle')
