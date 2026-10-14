"""GhostTrace package exports."""
from ghosttrace.engine import (
    audit,
    analyze_burstiness,
    calculate_score,
    latex_prose,
    markdown_prose,
    visible_text_html,
    humanize_text,
    detect_watermarks,
    sanitize_watermarks,
    get_suggestions,
    generate_heatmap_html,
    main,
)

__all__ = [
    "audit",
    "analyze_burstiness",
    "calculate_score",
    "latex_prose",
    "markdown_prose",
    "visible_text_html",
    "humanize_text",
    "detect_watermarks",
    "sanitize_watermarks",
    "get_suggestions",
    "generate_heatmap_html",
    "main",
]
