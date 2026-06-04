from html import escape
from pathlib import Path
from statistics import mean

from conflict_detector.domain.scenario_catalog import build_scenario_catalog


SCENARIO_CATALOG = {scenario.id.value: scenario for scenario in build_scenario_catalog().values()}
SCENARIO_LABELS = {scenario_id: scenario.label for scenario_id, scenario in SCENARIO_CATALOG.items()}
EVIDENCE_LABELS = {
    "address_employee_count": "Employés à cette adresse",
    "address_supplier_count": "Fournisseurs à cette adresse",
    "attribute": "Attribut commun",
    "average_amount": "Montant moyen",
    "date_cadeau": "Date du cadeau",
    "date_transaction": "Date de transaction",
    "employee_count": "Nombre d'employés",
    "gift_delay_days": "Délai cadeau/transaction",
    "manager_id": "Manager concerné",
    "montant_cadeau": "Montant du cadeau",
    "rule_id": "Règle technique",
    "shared_address": "Adresse commune",
    "shared_addresses": "Adresses communes",
    "shared_attributes": "Attributs communs",
    "shared_ibans": "IBAN communs",
    "shared_values": "Valeurs communes",
    "supplier_count": "Nombre de fournisseurs",
    "total_amount": "Montant total",
    "transaction_count": "Nombre de transactions",
}


def render_html_report(alerts: list[dict], path: str | Path, config: dict | None = None) -> None:
    config = config or {}
    reporting_config = config.get("reporting", {})
    top_alerts = int(reporting_config.get("top_alerts", 20))
    top_employees = int(reporting_config.get("top_employees", 15))
    employee_rows = aggregate_alerts_by_employee(alerts)
    alert_rows = sorted(alerts, key=lambda alert: (-float(alert.get("score") or 0), str(alert.get("scenario_id"))))
    Path(path).write_text(_page(alerts, employee_rows, alert_rows, top_alerts, top_employees), encoding="utf-8")


def render_scenario_documentation(path: str | Path) -> None:
    Path(path).write_text(_scenario_documentation_page(), encoding="utf-8")


def aggregate_alerts_by_employee(alerts: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for alert in alerts:
        employees = [entity for entity in alert.get("entities", []) if _entity_id(entity).startswith("EMP")]
        suppliers = [_supplier_label(entity) for entity in alert.get("entities", []) if _entity_id(entity).startswith("FOU")]
        for employee in employees:
            employee_id = _entity_id(employee)
            row = grouped.setdefault(
                employee_id,
                {
                    "employee_id": employee_id,
                    "employee_label": employee.get("label") or employee_id,
                    "alert_count": 0,
                    "high_count": 0,
                    "medium_count": 0,
                    "scores": [],
                    "scenarios": set(),
                    "suppliers": set(),
                },
            )
            row["alert_count"] += 1
            row["high_count"] += 1 if alert.get("severity") == "HIGH" else 0
            row["medium_count"] += 1 if alert.get("severity") == "MEDIUM" else 0
            row["scores"].append(float(alert.get("score") or 0))
            row["scenarios"].add(_scenario_name(alert.get("scenario_id")))
            row["suppliers"].update(suppliers)
    rows = []
    for row in grouped.values():
        scores = row.pop("scores")
        row["max_score"] = round(max(scores), 2) if scores else 0
        row["average_score"] = round(mean(scores), 2) if scores else 0
        row["scenarios"] = ", ".join(sorted(row["scenarios"]))
        row["suppliers"] = ", ".join(sorted(row["suppliers"]))
        rows.append(row)
    return sorted(rows, key=lambda item: (-item["max_score"], -item["alert_count"], item["employee_id"]))


def _page(alerts: list[dict], employee_rows: list[dict], alert_rows: list[dict], top_alerts: int, top_employees: int) -> str:
    total = len(alerts)
    high = sum(1 for alert in alerts if alert.get("severity") == "HIGH")
    medium = sum(1 for alert in alerts if alert.get("severity") == "MEDIUM")
    low = sum(1 for alert in alerts if alert.get("severity") == "LOW")
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Rapport d'alertes - conflits d'intérêts</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f7f9fc; }}
    h1, h2 {{ color: #123b7a; }}
    a {{ color: #174ea6; font-weight: bold; }}
    .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }}
    .kpi {{ background: white; border: 1px solid #d7deea; border-radius: 8px; padding: 14px; }}
    .kpi strong {{ display: block; font-size: 24px; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; margin-bottom: 28px; }}
    th, td {{ border: 1px solid #d7deea; padding: 8px 10px; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: #eaf0f8; color: #123b7a; }}
    tr.is-hidden {{ display: none; }}
    .show-more {{ display: block; margin: -14px 0 28px auto; border: 1px solid #b9c7dc; border-radius: 6px; background: white; color: #123b7a; padding: 8px 12px; cursor: pointer; font-weight: bold; }}
    .show-more:hover {{ background: #eaf0f8; }}
    .evidence {{ margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 4px 10px; }}
    .evidence dt {{ color: #475569; font-weight: bold; }}
    .evidence dd {{ margin: 0; }}
    .sev-HIGH {{ color: #9f1d1d; font-weight: bold; }}
    .sev-MEDIUM {{ color: #9a5b00; font-weight: bold; }}
    .sev-LOW {{ color: #2d6a35; font-weight: bold; }}
    .muted {{ color: #64748b; font-size: 12px; }}
  </style>
</head>
<body>
  <h1>Rapport d'alertes - conflits d'intérêts</h1>
  <p class="muted">Rapport généré automatiquement à partir des alertes détectées et scorées. <a href="scenarios.html">Voir la documentation des scénarios</a>.</p>
  <section class="kpis">
    <div class="kpi">Alertes totales<strong>{total}</strong></div>
    <div class="kpi">Gravité haute<strong>{high}</strong></div>
    <div class="kpi">Gravité moyenne<strong>{medium}</strong></div>
    <div class="kpi">Gravité basse<strong>{low}</strong></div>
  </section>
  <h2>Top {top_employees} employés à investiguer</h2>
  {_employee_table(employee_rows, top_employees)}
  <h2>Top {top_alerts} alertes prioritaires</h2>
  {_alert_table(alert_rows, top_alerts)}
  <script>
    document.querySelectorAll('[data-show-more]').forEach((button) => {{
      button.addEventListener('click', () => {{
        const section = button.closest('[data-table-section]');
        const rows = Array.from(section.querySelectorAll('tbody tr'));
        const step = Number(section.dataset.step);
        const visible = Number(section.dataset.visible);
        const nextVisible = visible + step;
        rows.forEach((row, index) => row.classList.toggle('is-hidden', index >= nextVisible));
        section.dataset.visible = String(nextVisible);
        if (nextVisible >= rows.length) {{
          button.remove();
        }}
      }});
    }});
  </script>
</body>
</html>
"""


def _employee_table(rows: list[dict], initial_visible: int) -> str:
    body = "".join(
        f"<tr{_hidden_row_attribute(index, initial_visible)}>"
        f"<td>{escape(row['employee_id'])}</td>"
        f"<td>{escape(str(row['employee_label']))}</td>"
        f"<td>{row['alert_count']}</td>"
        f"<td>{row['high_count']}</td>"
        f"<td>{row['medium_count']}</td>"
        f"<td>{row['max_score']}</td>"
        f"<td>{row['average_score']}</td>"
        f"<td>{escape(str(row['scenarios']))}</td>"
        f"<td>{escape(str(row['suppliers']))}</td>"
        "</tr>"
        for index, row in enumerate(rows)
    )
    return _table_section(
        (
            "<table><thead><tr><th>ID</th><th>Employé</th><th>Alertes</th><th>HIGH</th><th>MEDIUM</th>"
        "<th>Score max</th><th>Score moyen</th><th>Scénarios</th><th>Fournisseurs liés</th></tr></thead>"
            f"<tbody>{body}</tbody></table>"
        ),
        rows,
        initial_visible,
        "employés",
    )


def _alert_table(rows: list[dict], initial_visible: int) -> str:
    body = "".join(
        f"<tr{_hidden_row_attribute(index, initial_visible)}>"
        f"<td>{escape(_scenario_label(alert.get('scenario_id', '')))}</td>"
        f"<td>{escape(str(alert.get('score', '')))}</td>"
        f"<td class=\"sev-{escape(str(alert.get('severity', '')))}\">{escape(str(alert.get('severity', '')))}</td>"
        f"<td>{escape(_entities(alert))}</td>"
        f"<td>{escape(_source_rows(alert))}</td>"
        f"<td>{_evidence_html(alert)}</td>"
        "</tr>"
        for index, alert in enumerate(rows)
    )
    return _table_section(
        (
            "<table><thead><tr><th>Scénario</th><th>Score</th><th>Gravité</th><th>Entités</th>"
            "<th>Lignes source</th><th>Preuves</th></tr></thead>"
            f"<tbody>{body}</tbody></table>"
        ),
        rows,
        initial_visible,
        "alertes",
    )


def _hidden_row_attribute(index: int, initial_visible: int) -> str:
    if index >= initial_visible:
        return ' class="is-hidden"'
    return ""


def _table_section(table_html: str, rows: list[dict], initial_visible: int, label: str) -> str:
    visible_count = min(initial_visible, len(rows))
    button = ""
    if len(rows) > visible_count:
        button = f'<button type="button" class="show-more" data-show-more>↓ Afficher 5 {escape(label)} de plus</button>'
    return (
        f'<div data-table-section data-visible="{visible_count}" data-step="5">'
        f"{table_html}{button}"
        "</div>"
    )


def _entity_id(entity: dict) -> str:
    return str(entity.get("id", ""))


def _supplier_label(entity: dict) -> str:
    supplier_id = _entity_id(entity)
    label = str(entity.get("label") or "").strip()
    if label:
        return f"{supplier_id} - {label}"
    return supplier_id


def _scenario_name(scenario_id: object) -> str:
    scenario_key = str(scenario_id or "")
    return SCENARIO_LABELS.get(scenario_key, scenario_key)


def _scenario_label(scenario_id: object) -> str:
    scenario_key = str(scenario_id or "")
    scenario_name = _scenario_name(scenario_key)
    if scenario_name == scenario_key:
        return scenario_key
    return f"{scenario_name} ({scenario_key})"


def _entities(alert: dict) -> str:
    return " | ".join(
        f"{entity.get('type', '')}:{entity.get('id', '')} {entity.get('label', '')}".strip()
        for entity in alert.get("entities", [])
    )


def _source_rows(alert: dict) -> str:
    return ", ".join(str(row) for row in alert.get("source_rows", []))


def _evidence_html(alert: dict) -> str:
    evidence = alert.get("evidence", {})
    if not isinstance(evidence, dict) or not evidence:
        return '<span class="muted">Aucune preuve détaillée</span>'
    items = []
    for key, value in sorted(evidence.items()):
        label = EVIDENCE_LABELS.get(str(key), str(key).replace("_", " ").capitalize())
        items.append(f"<dt>{escape(label)}</dt><dd>{escape(_format_evidence_value(value))}</dd>")
    return f"<dl class=\"evidence\">{''.join(items)}</dl>"


def _format_evidence_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{key}: {item}" for key, item in sorted(value.items()))
    return str(value)


def _scenario_documentation_page() -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(scenario.label)}</td>"
        f"<td><code>{escape(scenario.id.value)}</code></td>"
        f"<td>{escape(scenario.description)}</td>"
        f"<td>{escape(', '.join(scenario.required_tables))}</td>"
        "</tr>"
        for scenario in SCENARIO_CATALOG.values()
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Documentation des scénarios</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f7f9fc; }}
    h1 {{ color: #123b7a; }}
    a {{ color: #174ea6; font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; background: white; margin-top: 20px; }}
    th, td {{ border: 1px solid #d7deea; padding: 10px 12px; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: #eaf0f8; color: #123b7a; }}
    code {{ color: #334155; }}
    .muted {{ color: #64748b; font-size: 12px; }}
  </style>
</head>
<body>
  <h1>Documentation des scénarios</h1>
  <p class="muted">Cette page est générée à partir de <code>scenario_catalog.py</code>.</p>
  <p><a href="report.html">Retour au rapport d'alertes</a></p>
  <table>
    <thead>
      <tr><th>Scénario</th><th>Identifiant</th><th>Définition métier</th><th>Données utilisées</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""
