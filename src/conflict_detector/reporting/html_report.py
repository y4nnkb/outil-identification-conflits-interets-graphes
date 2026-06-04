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
    "beneficiaire_effectif": "Bénéficiaire effectif",
    "date_cadeau": "Date du cadeau",
    "date_transaction": "Date de transaction",
    "employee_count": "Nombre d'employés",
    "gift_delay_days": "Délai cadeau/transaction",
    "is_boite_postale": "Boîte postale",
    "link_types": "Types de liens",
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
    "value": "Valeur détectée",
}


def render_html_report(alerts: list[dict], path: str | Path, config: dict | None = None) -> None:
    config = config or {}
    reporting_config = config.get("reporting", {})
    top_alerts = int(reporting_config.get("top_alerts", 20))
    top_employees = int(reporting_config.get("top_employees", 15))
    employee_rows = aggregate_alerts_by_employee(alerts)
    alert_rows = sorted(alerts, key=lambda alert: (-float(alert.get("score") or 0), str(alert.get("scenario_id"))))
    Path(path).write_text(_report_page(alerts, employee_rows, alert_rows, top_alerts, top_employees), encoding="utf-8")


def render_scenario_documentation(path: str | Path) -> None:
    Path(path).write_text(_scenario_documentation_page(), encoding="utf-8")


def render_employee_detail_pages(alerts: list[dict], output_dir: str | Path, config: dict | None = None) -> None:
    target = Path(output_dir) / "employees"
    target.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = {}
    labels: dict[str, str] = {}
    for alert in alerts:
        for entity in _employee_entities(alert):
            employee_id = _entity_id(entity)
            grouped.setdefault(employee_id, []).append(alert)
            labels.setdefault(employee_id, str(entity.get("label") or employee_id))
    for employee_id, employee_alerts in grouped.items():
        rows = sorted(employee_alerts, key=lambda alert: (-float(alert.get("score") or 0), str(alert.get("scenario_id"))))
        (target / f"{employee_id}.html").write_text(
            _employee_detail_page(employee_id, labels[employee_id], rows),
            encoding="utf-8",
        )


def aggregate_alerts_by_employee(alerts: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for alert in alerts:
        suppliers = [_supplier_label(entity) for entity in alert.get("entities", []) if _entity_id(entity).startswith("FOU")]
        for employee in _employee_entities(alert):
            employee_id = _entity_id(employee)
            row = grouped.setdefault(
                employee_id,
                {
                    "employee_id": employee_id,
                    "employee_label": employee.get("label") or employee_id,
                    "employee_page": f"employees/{employee_id}.html",
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


def _report_page(alerts: list[dict], employee_rows: list[dict], alert_rows: list[dict], top_alerts: int, top_employees: int) -> str:
    total = len(alerts)
    high = sum(1 for alert in alerts if alert.get("severity") == "HIGH")
    medium = sum(1 for alert in alerts if alert.get("severity") == "MEDIUM")
    low = sum(1 for alert in alerts if alert.get("severity") == "LOW")
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Rapport d'alertes - conflits d'intérêts</title>
  {_style()}
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
  {_filters()}
  <h2>Top {top_employees} employés à investiguer</h2>
  {_employee_table(employee_rows, top_employees)}
  <h2>Top {top_alerts} alertes prioritaires</h2>
  {_alert_table(alert_rows, top_alerts)}
  {_script()}
</body>
</html>
"""


def _employee_detail_page(employee_id: str, employee_label: str, alerts: list[dict]) -> str:
    high = sum(1 for alert in alerts if alert.get("severity") == "HIGH")
    medium = sum(1 for alert in alerts if alert.get("severity") == "MEDIUM")
    suppliers = sorted({_supplier_label(entity) for alert in alerts for entity in alert.get("entities", []) if _entity_id(entity).startswith("FOU")})
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Alertes employé - {escape(employee_id)}</title>
  {_style()}
</head>
<body>
  <p><a href="../report.html">Retour au rapport principal</a></p>
  <h1>{escape(employee_label)} <span class="muted">({escape(employee_id)})</span></h1>
  <section class="kpis">
    <div class="kpi">Alertes liées<strong>{len(alerts)}</strong></div>
    <div class="kpi">Gravité haute<strong>{high}</strong></div>
    <div class="kpi">Gravité moyenne<strong>{medium}</strong></div>
    <div class="kpi">Fournisseurs liés<strong>{len(suppliers)}</strong></div>
  </section>
  <p><strong>Fournisseurs concernés :</strong> {escape(', '.join(suppliers) or 'Aucun fournisseur identifié')}</p>
  {_filters()}
  <h2>Alertes liées à cet employé</h2>
  {_alert_table(alerts, len(alerts))}
  {_script()}
</body>
</html>
"""


def _filters() -> str:
    scenario_options = "".join(
        f'<option value="{escape(scenario_id)}">{escape(definition.label)}</option>'
        for scenario_id, definition in SCENARIO_CATALOG.items()
    )
    return f"""<section class="filters">
    <label>Recherche <input type="search" data-search-input placeholder="Employé, fournisseur, preuve..."></label>
    <label>Gravité
      <select data-severity-filter>
        <option value="">Toutes</option>
        <option value="HIGH">HIGH</option>
        <option value="MEDIUM">MEDIUM</option>
        <option value="LOW">LOW</option>
      </select>
    </label>
    <label>Scénario
      <select data-scenario-filter>
        <option value="">Tous</option>
        {scenario_options}
      </select>
    </label>
  </section>"""


def _employee_table(rows: list[dict], initial_visible: int) -> str:
    body = "".join(
        f"<tr{_row_attributes(index, initial_visible, row['scenarios'], '', row)}>"
        f"<td><a href=\"{escape(str(row['employee_page']))}\">{escape(row['employee_id'])}</a></td>"
        f"<td><a href=\"{escape(str(row['employee_page']))}\">{escape(str(row['employee_label']))}</a></td>"
        f"<td data-sort-value=\"{row['alert_count']}\">{row['alert_count']}</td>"
        f"<td data-sort-value=\"{row['high_count']}\">{row['high_count']}</td>"
        f"<td data-sort-value=\"{row['medium_count']}\">{row['medium_count']}</td>"
        f"<td data-sort-value=\"{row['max_score']}\">{row['max_score']}</td>"
        f"<td data-sort-value=\"{row['average_score']}\">{row['average_score']}</td>"
        f"<td>{escape(str(row['scenarios']))}</td>"
        f"<td>{escape(str(row['suppliers']))}</td>"
        "</tr>"
        for index, row in enumerate(rows)
    )
    return _table_section(
        (
            "<table data-sortable><thead><tr>"
            "<th data-sort-type=\"text\">ID</th><th data-sort-type=\"text\">Employé</th>"
            "<th data-sort-type=\"number\">Alertes</th><th data-sort-type=\"number\">HIGH</th><th data-sort-type=\"number\">MEDIUM</th>"
            "<th data-sort-type=\"number\">Score max</th><th data-sort-type=\"number\">Score moyen</th>"
            "<th data-sort-type=\"text\">Scénarios</th><th data-sort-type=\"text\">Fournisseurs liés</th>"
            "</tr></thead>"
            f"<tbody>{body}</tbody></table>"
        ),
        rows,
        initial_visible,
        "employés",
    )


def _alert_table(rows: list[dict], initial_visible: int) -> str:
    body = "".join(
        f"<tr{_row_attributes(index, initial_visible, alert.get('scenario_id'), alert.get('severity'), alert)}>"
        f"<td>{escape(_scenario_label(alert.get('scenario_id', '')))}</td>"
        f"<td data-sort-value=\"{float(alert.get('score') or 0)}\">{escape(str(alert.get('score', '')))}</td>"
        f"<td class=\"sev-{escape(str(alert.get('severity', '')))}\">{escape(str(alert.get('severity', '')))}</td>"
        f"<td>{escape(_entities(alert))}</td>"
        f"<td>{escape(_source_rows(alert))}</td>"
        f"<td>{escape(_alert_reason(alert))}</td>"
        f"<td>{_evidence_details(alert)}</td>"
        "</tr>"
        for index, alert in enumerate(rows)
    )
    return _table_section(
        (
            "<table data-sortable><thead><tr>"
            "<th data-sort-type=\"text\">Scénario</th><th data-sort-type=\"number\">Score</th><th data-sort-type=\"text\">Gravité</th>"
            "<th data-sort-type=\"text\">Entités</th><th data-sort-type=\"text\">Lignes source</th>"
            "<th data-sort-type=\"text\">Pourquoi l'alerte ?</th><th data-sort-type=\"text\">Preuves</th>"
            "</tr></thead>"
            f"<tbody>{body}</tbody></table>"
        ),
        rows,
        initial_visible,
        "alertes",
    )


def _row_attributes(index: int, initial_visible: int, scenario: object, severity: object, payload: dict) -> str:
    classes = ["is-hidden"] if index >= initial_visible else []
    return (
        f' class="{" ".join(classes)}"'
        f' data-row'
        f' data-scenario="{escape(str(scenario or ""))}"'
        f' data-severity="{escape(str(severity or ""))}"'
        f' data-search="{escape(_search_text(payload))}"'
    )


def _table_section(table_html: str, rows: list[dict], initial_visible: int, label: str) -> str:
    visible_count = min(initial_visible, len(rows))
    button = ""
    if len(rows) > visible_count:
        button = f'<button type="button" class="show-more" data-show-more>↓ Afficher 5 {escape(label)} de plus</button>'
    return (
        f'<div data-table-section data-visible="{visible_count}" data-initial-visible="{visible_count}" data-step="5">'
        f"{table_html}{button}"
        "</div>"
    )


def _evidence_details(alert: dict) -> str:
    return f"<details><summary>Voir les preuves</summary>{_evidence_html(alert)}</details>"


def _evidence_html(alert: dict) -> str:
    evidence = alert.get("evidence", {})
    if not isinstance(evidence, dict) or not evidence:
        return '<span class="muted">Aucune preuve détaillée</span>'
    items = []
    for key, value in sorted(evidence.items()):
        label = EVIDENCE_LABELS.get(str(key), str(key).replace("_", " ").capitalize())
        items.append(f"<dt>{escape(label)}</dt><dd>{escape(_format_evidence_value(value))}</dd>")
    return f"<dl class=\"evidence\">{''.join(items)}</dl>"


def _alert_reason(alert: dict) -> str:
    scenario = _scenario_name(alert.get("scenario_id"))
    evidence = alert.get("evidence", {})
    parts = [scenario]
    if isinstance(evidence, dict):
        if evidence.get("attribute"):
            parts.append(f"attribut commun {evidence['attribute']}")
        if evidence.get("shared_attributes"):
            parts.append(f"attributs communs: {_format_evidence_value(evidence['shared_attributes'])}")
        if evidence.get("transaction_count"):
            parts.append(f"{evidence['transaction_count']} transaction(s)")
        if evidence.get("total_amount"):
            parts.append(f"montant total {evidence['total_amount']}")
        if evidence.get("gift_delay_days") is not None:
            parts.append(f"cadeau {evidence['gift_delay_days']} jour(s) avant la transaction")
        if evidence.get("manager_id"):
            parts.append(f"hiérarchie manager {evidence['manager_id']}")
    return " | ".join(str(part) for part in parts)


def _format_evidence_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{key}: {item}" for key, item in sorted(value.items()))
    return str(value)


def _search_text(payload: dict) -> str:
    if "employee_id" in payload:
        values = [
            payload.get("employee_id"),
            payload.get("employee_label"),
            payload.get("scenarios"),
            payload.get("suppliers"),
        ]
    else:
        values = [
            payload.get("scenario_id"),
            payload.get("severity"),
            _entities(payload),
            _source_rows(payload),
            _alert_reason(payload),
            _format_evidence_value(payload.get("evidence", {})),
        ]
    return " ".join(str(value or "") for value in values).lower()


def _employee_entities(alert: dict) -> list[dict]:
    return [entity for entity in alert.get("entities", []) if _entity_id(entity).startswith("EMP")]


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
  {_style()}
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


def _style() -> str:
    return """<style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f7f9fc; }
    h1, h2 { color: #123b7a; }
    a { color: #174ea6; font-weight: bold; }
    .kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }
    .kpi { background: white; border: 1px solid #d7deea; border-radius: 8px; padding: 14px; }
    .kpi strong { display: block; font-size: 24px; margin-top: 4px; }
    .filters { display: flex; flex-wrap: wrap; gap: 12px; background: white; border: 1px solid #d7deea; border-radius: 8px; padding: 12px; margin: 20px 0; }
    .filters label { display: grid; gap: 4px; color: #475569; font-size: 12px; font-weight: bold; }
    .filters input, .filters select { min-width: 210px; padding: 8px; border: 1px solid #b9c7dc; border-radius: 6px; }
    table { width: 100%; border-collapse: collapse; background: white; margin-bottom: 28px; }
    th, td { border: 1px solid #d7deea; padding: 8px 10px; text-align: left; vertical-align: top; font-size: 13px; }
    th { background: #eaf0f8; color: #123b7a; cursor: pointer; user-select: none; }
    tr.is-hidden, tr.is-filtered { display: none; }
    details summary { color: #174ea6; cursor: pointer; font-weight: bold; }
    .show-more { display: block; margin: -14px 0 28px auto; border: 1px solid #b9c7dc; border-radius: 6px; background: white; color: #123b7a; padding: 8px 12px; cursor: pointer; font-weight: bold; }
    .show-more:hover { background: #eaf0f8; }
    .evidence { margin: 8px 0 0; display: grid; grid-template-columns: max-content 1fr; gap: 4px 10px; }
    .evidence dt { color: #475569; font-weight: bold; }
    .evidence dd { margin: 0; }
    .sev-HIGH { color: #9f1d1d; font-weight: bold; }
    .sev-MEDIUM { color: #9a5b00; font-weight: bold; }
    .sev-LOW { color: #2d6a35; font-weight: bold; }
    .muted { color: #64748b; font-size: 12px; }
  </style>"""


def _script() -> str:
    return """<script>
    function applyTableState(section) {
      const search = (document.querySelector('[data-search-input]')?.value || '').toLowerCase();
      const severity = document.querySelector('[data-severity-filter]')?.value || '';
      const scenario = document.querySelector('[data-scenario-filter]')?.value || '';
      const rows = Array.from(section.querySelectorAll('tbody tr'));
      const visibleLimit = Number(section.dataset.visible);
      let visibleMatched = 0;
      rows.forEach((row) => {
        const matchesSearch = !search || row.dataset.search.includes(search);
        const matchesSeverity = !severity || row.dataset.severity === severity;
        const matchesScenario = !scenario || row.dataset.scenario === scenario || row.dataset.scenario.includes(scenario);
        const filtered = !(matchesSearch && matchesSeverity && matchesScenario);
        row.classList.toggle('is-filtered', filtered);
        if (filtered) {
          row.classList.add('is-hidden');
          return;
        }
        visibleMatched += 1;
        row.classList.toggle('is-hidden', visibleMatched > visibleLimit);
      });
      const button = section.querySelector('[data-show-more]');
      if (button) {
        button.style.display = visibleMatched > visibleLimit ? 'block' : 'none';
      }
    }
    document.querySelectorAll('[data-table-section]').forEach((section) => applyTableState(section));
    document.querySelectorAll('[data-search-input], [data-severity-filter], [data-scenario-filter]').forEach((input) => {
      input.addEventListener('input', () => {
        document.querySelectorAll('[data-table-section]').forEach((section) => {
          section.dataset.visible = section.dataset.initialVisible;
          applyTableState(section);
        });
      });
    });
    document.querySelectorAll('[data-show-more]').forEach((button) => {
      button.addEventListener('click', () => {
        const section = button.closest('[data-table-section]');
        section.dataset.visible = String(Number(section.dataset.visible) + Number(section.dataset.step));
        applyTableState(section);
      });
    });
    document.querySelectorAll('table[data-sortable] th').forEach((header, columnIndex) => {
      header.addEventListener('click', () => {
        const table = header.closest('table');
        const tbody = table.querySelector('tbody');
        const direction = header.dataset.direction === 'asc' ? 'desc' : 'asc';
        table.querySelectorAll('th').forEach((item) => delete item.dataset.direction);
        header.dataset.direction = direction;
        const type = header.dataset.sortType || 'text';
        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort((a, b) => {
          const aCell = a.children[columnIndex];
          const bCell = b.children[columnIndex];
          const aValue = aCell.dataset.sortValue || aCell.textContent.trim();
          const bValue = bCell.dataset.sortValue || bCell.textContent.trim();
          const result = type === 'number'
            ? Number(aValue) - Number(bValue)
            : aValue.localeCompare(bValue, 'fr', { numeric: true });
          return direction === 'asc' ? result : -result;
        });
        rows.forEach((row) => tbody.appendChild(row));
        document.querySelectorAll('[data-table-section]').forEach((section) => applyTableState(section));
      });
    });
  </script>"""
