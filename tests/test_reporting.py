from conflict_detector.reporting.html_report import (
    aggregate_alerts_by_employee,
    render_html_report,
    render_scenario_documentation,
)


def test_aggregate_alerts_by_employee_groups_scores_and_scenarios() -> None:
    alerts = [
        {
            "scenario_id": "identity_match",
            "score": 18,
            "severity": "HIGH",
            "entities": [
                {"id": "EMP001", "type": "Employe", "label": "Alice Martin"},
                {"id": "FOU001", "type": "Fournisseur", "label": "Alpha"},
            ],
        },
        {
            "scenario_id": "direct_link",
            "score": 10,
            "severity": "MEDIUM",
            "entities": [
                {"id": "EMP001", "type": "Employe", "label": "Alice Martin"},
                {"id": "FOU002", "type": "Fournisseur", "label": "Beta"},
            ],
        },
    ]

    rows = aggregate_alerts_by_employee(alerts)

    assert rows[0]["employee_id"] == "EMP001"
    assert rows[0]["alert_count"] == 2
    assert rows[0]["max_score"] == 18
    assert rows[0]["average_score"] == 14
    assert rows[0]["high_count"] == 1
    assert rows[0]["medium_count"] == 1
    assert "Correspondance d'identités" in rows[0]["scenarios"]
    assert "Lien direct" in rows[0]["scenarios"]
    assert "FOU001 - Alpha" in rows[0]["suppliers"]
    assert "FOU002 - Beta" in rows[0]["suppliers"]


def test_render_html_report_writes_top_alerts(tmp_path) -> None:
    alerts = [
        {
            "scenario_id": "identity_match",
            "score": 18,
            "severity": "HIGH",
            "entities": [{"id": "EMP001", "type": "Employe", "label": "Alice Martin"}],
            "evidence": {"attribute": "iban"},
            "source_rows": ["TRX001"],
        }
    ]
    target = tmp_path / "report.html"

    render_html_report(alerts, target, {"reporting": {"top_alerts": 1, "top_employees": 1}})

    html = target.read_text(encoding="utf-8")
    assert "Rapport d'alertes" in html
    assert "Correspondance d&#x27;identités (identity_match)" in html
    assert "Voir la documentation des scénarios" in html
    assert "Attribut commun" in html
    assert "iban" in html
    assert "EMP001" in html


def test_render_html_report_can_reveal_more_rows(tmp_path) -> None:
    alerts = [
        {
            "scenario_id": "identity_match",
            "score": 20 - index,
            "severity": "HIGH",
            "entities": [
                {"id": f"EMP{index:03d}", "type": "Employe", "label": f"Employe {index}"},
                {"id": f"FOU{index:03d}", "type": "Fournisseur", "label": f"Fournisseur {index}"},
            ],
            "evidence": {"attribute": "iban"},
            "source_rows": [f"TRX{index:03d}"],
        }
        for index in range(1, 5)
    ]
    target = tmp_path / "report.html"

    render_html_report(alerts, target, {"reporting": {"top_alerts": 2, "top_employees": 2}})

    html = target.read_text(encoding="utf-8")
    assert html.count('class="is-hidden"') >= 4
    assert "↓ Afficher 5 employés de plus" in html
    assert "↓ Afficher 5 alertes de plus" in html
    assert 'data-step="5"' in html


def test_render_scenario_documentation_writes_business_definitions(tmp_path) -> None:
    target = tmp_path / "scenarios.html"

    render_scenario_documentation(target)

    html = target.read_text(encoding="utf-8")
    assert "Documentation des scénarios" in html
    assert "Fournisseur fantôme" in html
    assert "ghost_supplier" in html
    assert "Définition métier" in html
