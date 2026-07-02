"""
Regénère index.html bilingue à partir de _source_cv_fr.html (source FR validée localement).

Workflow :
  1. Modifier _source_cv_fr.html OU index.html puis : python build_bilingual.py --bootstrap
  2. Vérifier en local (fichier index.html)
  3. Pousser sur GitHub seulement quand vous validez
"""
import re
import shutil
import sys
from pathlib import Path

publish = Path(__file__).parent
source_fr = publish / "_source_cv_fr.html"
doc_cv = Path(
    r"C:\Users\ntpar\Dev_IT\Projet_depo\Projet_IA\LLM Security Gateway"
    r"\LLM_Security_Gateway_Core_Prive\doc\cv"
)

# Contenu figé — ne pas écraser via des remplacements automatiques
LOCKED_MARKERS = [
    ("AI Product Builder", "Titre / subtitle"),
    ("Je transforme vos idées en produits Web, SaaS", "Promesse (header)"),
    ("produits numériques utilisables et évolutifs", "Section Profil"),
]

GRETIA_FORMATION_FR = (
    '<div class="edu-hi"><strong>IA appliquée &amp; Data Analyse</strong> — GRETA · Attestation · 20/02/2026 · stage Assistant IA — KSPR Consulting · 20/01–20/02/2026</div>'
)
GRETIA_FORMATION_EN = (
    '<div class="edu-hi"><strong>Applied AI &amp; Data Analysis</strong> — GRETA · Certificate · 20/02/2026 · AI Assistant internship — KSPR Consulting · 20/01–20/02/2026</div>'
)

LLM_LINKEDIN_DEMO = "https://www.linkedin.com/feed/update/urn:li:activity:7468573770484617216/"
LLM_GITHUB = "https://github.com/ta-dev-ai/llm-security-gateway-showcase"
LLM_RESULT_EN = (
    f'<p class="project__row"><span class="k">Result:</span> MVP prototype demonstrated — active development. '
    f'<a href="{LLM_LINKEDIN_DEMO}">LinkedIn demo</a> · <a href="{LLM_GITHUB}">GitHub showcase</a>.</p>'
)
LLM_RESULT_EN_PARTIAL = (
    f'<p class="project__row"><span class="k">Result:</span> prototype MVP démontré — développement actif. '
    f'<a href="{LLM_LINKEDIN_DEMO}">Démo LinkedIn</a> · <a href="{LLM_GITHUB}">Vitrine GitHub</a>.</p>'
)


def extract_cv_article(html: str) -> str:
    for marker in ('<article class="cv">', '<article class="cv cv-lang active" id="cv-fr"'):
        start = html.find(marker)
        if start != -1:
            break
    else:
        raise SystemExit("CV article not found")
    footer_start = html.find('<footer id="cv-footer">', start)
    end = html.find("</article>", footer_start)
    if footer_start == -1 or end == -1:
        raise SystemExit("CV article boundaries not found")
    block = html[start : end + len("</article>")]
    return block.replace(
        '<article class="cv cv-lang active" id="cv-fr" lang="fr">',
        '<article class="cv">',
        1,
    )


def bootstrap_source_from_index() -> None:
    index = (publish / "index.html").read_text(encoding="utf-8")
    head = re.search(r"<head>.*?</head>", index, re.S)
    if not head:
        raise SystemExit("head not found in index.html")
    head_html = head.group(0)
    head_html = re.sub(
        r"\n\s*\.cv-toolbar.*?(?=\n\s*</style>)",
        "",
        head_html,
        flags=re.S,
    )
    head_html = head_html.replace(
        "<title>CV — Tayier NIMAIT | FR / EN</title>",
        "<title>CV — Tayier NIMAIT | Hybrid 2026 FINAL 2</title>",
    )
    article = extract_cv_article(index)
    out = f"<!DOCTYPE html>\n<html lang=\"fr\">\n{head_html}\n<body>\n{article}\n</body>\n</html>"
    source_fr.write_text(out, encoding="utf-8")
    print(f"Source FR figée : {source_fr}")


def assert_locked_content(html: str) -> None:
    for needle, label in LOCKED_MARKERS:
        if needle not in html:
            raise SystemExit(f"ERREUR contenu verrouillé manquant ({label}) : {needle!r}")
    profile = re.search(r'<section id="profile".*?</section>', html, re.S)
    if profile and "Je transforme vos idées en produits Web, SaaS" in profile.group(0):
        raise SystemExit(
            "ERREUR : la promesse du header a été copiée dans la section Profil — corrigez _source_cv_fr.html"
        )


def reorder_experience(html: str, kspr_title: str, greta_title: str) -> str:
    kspr_re = re.compile(
        rf'<article class="job">\s*<p class="job__title">{re.escape(kspr_title)}</p>.*?</article>',
        re.S,
    )
    greta_re = re.compile(
        rf'<article class="job">\s*<p class="job__title">{re.escape(greta_title)}</p>.*?</article>',
        re.S,
    )
    m_kspr = kspr_re.search(html)
    m_greta = greta_re.search(html)
    if not m_kspr or not m_greta or m_greta.start() < m_kspr.start():
        return html
    return (
        html[: m_kspr.start()]
        + m_greta.group(0)
        + "\n            "
        + m_kspr.group(0)
        + html[m_greta.end() :]
    )


def build() -> None:
    if "--bootstrap" in sys.argv or not source_fr.exists():
        bootstrap_source_from_index()
    fr_html = source_fr.read_text(encoding="utf-8")
    assert_locked_content(fr_html)

    en_html = fr_html
    repl_en = [
        ('<html lang="fr">', '<html lang="en">'),
        (
            "AI Product Builder <span>· Python · FastAPI · React · .NET</span>",
            "AI Product Builder <span>· Python · FastAPI · React · .NET · Open to Opportunities</span>",
        ),
        (
            "Je transforme vos idées en produits Web, SaaS &amp; IA.",
            "I transform your ideas into Web, SaaS &amp; AI products.",
        ),
        (
            '<p class="section__body">J\'aide les entreprises et les entrepreneurs à transformer leurs idées en produits numériques utilisables et évolutifs.</p>',
            '<p class="section__body">I help companies and entrepreneurs turn their ideas into usable, scalable digital products.</p>',
        ),
        ("Disponible pour CDI, missions et collaborations", "Available for full-time, freelance and collaborations"),
        ("Portfolio et démonstrations sur demande", "Portfolio and demos on request"),
        ('<h2 class="section__head">Profil</h2>', '<h2 class="section__head">Profile</h2>'),
        ("Idée → Conception → Prototype IA → MVP → Industrialisation", "Idea → Design → AI Prototype → MVP → Scale"),
        ('<h2 class="section__head">Compétences</h2>', '<h2 class="section__head">Skills</h2>'),
        ("<h3>Ce que je livre</h3>", "<h3>What I deliver</h3>"),
        (
            "Applications IA prêtes au déploiement : sécurité documentaire, agents conversationnels",
            "Production-ready AI apps: document security, conversational agents",
        ),
        (
            "SaaS et applications web/mobile, du prototype à l'industrialisation",
            "SaaS and web/mobile apps, from prototype to production",
        ),
        ('<h2 class="section__head">Expérience professionnelle</h2>', '<h2 class="section__head">Professional experience</h2>'),
        ('<span class="lbl">Résultat :</span>', '<span class="lbl">Result:</span>'),
        ('<span class="lbl">Développement :</span>', '<span class="lbl">Delivery:</span>'),
        ('<span class="lbl">Évolution :</span>', '<span class="lbl">Evolution:</span>'),
        ("prototype IA validé avec les utilisateurs finaux.", "AI prototype validated with end users."),
        ("cycle Agile complet — accessibilité web par langage naturel.", "full Agile cycle — web accessibility via natural language."),
        ("Stage pratique Cybersécurité &amp; IA — GRETA", "Cybersecurity &amp; AI internship — GRETA"),
        ("sujet choisi, mené en autonomie de l'idée au produit testable.", "self-led topic from idea to testable product."),
        ("V2 personnelle vers SaaS B2B (traçabilité, anonymisation, suivi).", "personal V2 toward B2B SaaS (traceability, anonymization, tracking)."),
        ("Développeur Full Stack — Cegi Santé", "Full Stack Developer — Cegi Santé"),
        ("Juin 2023 — Octobre 2023", "Jun 2023 — Oct 2023"),
        ("+50&nbsp;% de traçabilité médicale.", "+50% medical traceability."),
        ("applications C# / .NET et React — traçabilité interne insuffisante corrigée.", "C# / .NET and React apps — fixed insufficient internal traceability."),
        ("Développeur Full Stack (Stage) — Omnilia", "Full Stack Developer (Intern) — Omnilia"),
        ("fonctionnalités back et front livrées sur plateforme SaaS e-commerce.", "back-end and front-end features on SaaS e-commerce platform."),
        ("participation complète côté serveur et interface.", "full contribution on server and UI."),
        ('<h2 class="section__head">Projets phares 2026</h2>', '<h2 class="section__head">Key projects 2026</h2>'),
        ("1er projet phare · développement actif", "1st key project · active development"),
        ("sécurité documentaire IA", "AI document security"),
        ('<span class="k">Problème :</span>', '<span class="k">Problem:</span>'),
        ('<span class="k">Solution :</span>', '<span class="k">Solution:</span>'),
        ('<span class="k">Résultat :</span>', '<span class="k">Result:</span>'),
        ('<span class="k">Contexte :</span>', '<span class="k">Context:</span>'),
        ('<span class="k">Évolution :</span>', '<span class="k">Evolution:</span>'),
        (
            "les entreprises utilisent des LLM sans moyen simple de filtrer documents risqués et attaques par prompt injection.",
            "companies use LLMs without a simple way to filter risky documents and prompt injection attacks.",
        ),
        (
            "plateforme d'analyse qui localise visuellement la zone à risque dans le document (pas une simple classification), détecte les attaques en 20 langues, et génère un résumé du document.",
            "analysis platform that visually locates risk zones, detects attacks in 20 languages, and generates summaries.",
        ),
        (
            "stage cybersécurité &amp; IA — Python &amp; Objets connectés (GRETA, 04/05–04/06/2026).",
            "cybersecurity &amp; AI internship — Python &amp; IoT (GRETA, May–Jun 2026).",
        ),
        (
            "V2 personnelle vers SaaS B2B — traçabilité par document, suivi de progression, anonymisation des données confidentielles.",
            "personal V2 toward B2B SaaS — traceability, progress tracking, data anonymization.",
        ),
        ("2e projet phare · MVP en ~2 jours", "2nd key project · MVP in ~2 days"),
        ("contenus longs impossibles à consommer en déplacement.", "long content hard to consume on the go."),
        ("manuscrit → audio local + lecteur synchronisé texte-voix + export ZIP.", "manuscript → local audio + synced text-voice player + ZIP export."),
        ("prototype fonctionnel livré en 2 jours.", "working prototype delivered in 2 days."),
        ("Démo LinkedIn (40 s)", "LinkedIn demo (40s)"),
        ("projet personnel — CDC étudié, développé en autonomie (juin 2026).", "personal project — spec reviewed, built independently (Jun 2026)."),
        ("vers une version SaaS, puis desktop.", "toward SaaS, then desktop."),
        ('<h2 class="section__head">Autres réalisations</h2>', '<h2 class="section__head">Other achievements</h2>'),
        ("seul, 15 jours : 10 ans de données rendues lisibles. Évolution agent IA conversationnel.", "solo, 15 days: 10 years of data made readable. Evolving to conversational AI agent."),
        ("réduit la saisie manuelle de facturation PME.", "reduces manual SME invoicing."),
        ("orchestration multi-modèles, recherche documentaire IA.", "multi-model orchestration, AI document search."),
        ("transforme contenus et workflows en outils utilisables.", "turns content and workflows into usable tools."),
        ("<span>Formation</span>", "<span>Education</span>"),
        ("<span>Langues</span>", "<span>Languages</span>"),
        ("Paris et périphérie", "Paris &amp; surrounding area"),
        ("Ouïghour (maternelle)", "Uyghur (native)"),
        ("Français (courant)", "French (fluent)"),
        ("Anglais (professionnel)", "English (professional)"),
        ("Chinois (courant)", "Chinese (fluent)"),
        ("Turc (courant)", "Turkish (fluent)"),
        (
            "MVP LLM Security Gateway livré — filtrage documentaire et prompt injection.",
            "LLM Security Gateway MVP — document filtering and prompt injection.",
        ),
    ]
    for old, new in repl_en:
        en_html = en_html.replace(old, new)

    en_html = en_html.replace(GRETIA_FORMATION_FR, GRETIA_FORMATION_EN)
    en_html = en_html.replace(LLM_RESULT_EN_PARTIAL, LLM_RESULT_EN)
    en_html = reorder_experience(
        en_html,
        "Assistant IA (Stage) — KSPR Consulting",
        "Cybersecurity &amp; AI internship — GRETA",
    )

    m_fr = extract_cv_article(fr_html)
    m_en = extract_cv_article(en_html)
    m_head = re.search(r"<head>.*?</head>", fr_html, re.S)
    if not (m_fr and m_en and m_head):
        raise SystemExit("parse failed")

    fr_body = m_fr.replace('<article class="cv">', '<article class="cv cv-lang active" id="cv-fr" lang="fr">', 1)
    en_body = m_en.replace('<article class="cv">', '<article class="cv cv-lang" id="cv-en" lang="en">', 1)
    head = m_head.group(0).replace(
        "<title>CV — Tayier NIMAIT | Hybrid 2026 FINAL 2</title>",
        "<title>CV — Tayier NIMAIT | FR / EN</title>",
    )

    toolbar_css = """
  .cv-toolbar { position: sticky; top: 0; z-index: 1001; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; max-width: 210mm; margin: 8px auto 0; padding: 8px 10px; background: #fff; border: 1px solid #ddd; border-radius: 8px 8px 0 0; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
  .lang-tabs { display: flex; gap: 0; }
  .lang-tab { padding: 8px 18px; border: none; background: transparent; cursor: pointer; font-family: Inter, sans-serif; font-size: 10pt; font-weight: 600; color: #666; border-bottom: 3px solid transparent; }
  .lang-tab.active[data-lang="fr"] { color: #0a66c2; border-bottom-color: #0a66c2; }
  .lang-tab.active[data-lang="en"] { color: #057642; border-bottom-color: #057642; }
  .dl-btns { display: flex; gap: 8px; flex-wrap: wrap; }
  .dl-btn { display: inline-flex; align-items: center; gap: 5px; padding: 8px 14px; border: none; border-radius: 6px; font-family: Inter, sans-serif; font-size: 9pt; font-weight: 700; cursor: pointer; color: #fff; }
  .dl-btn-fr { background: #0a66c2; }
  .dl-btn-en { background: #057642; }
  .dl-btn:hover { filter: brightness(1.08); }
  .cv-lang { display: none; }
  .cv-lang.active { display: flex; }
  .print-btn { display: none !important; }
  @media print { .cv-toolbar { display: none !important; } .cv-lang { display: none !important; } .cv-lang.print-target { display: flex !important; } }
"""
    head = head.replace("</style>", toolbar_css + "\n  </style>")

    out = f"""<!DOCTYPE html>
<html lang="fr">
{head}
<body>
  <div class="cv-toolbar">
    <div class="lang-tabs">
      <button type="button" class="lang-tab active" data-lang="fr" onclick="showLang('fr')">Français</button>
      <button type="button" class="lang-tab" data-lang="en" onclick="showLang('en')">English</button>
    </div>
    <div class="dl-btns">
      <button type="button" class="dl-btn dl-btn-fr" onclick="downloadCv('fr')">⬇ Télécharger le CV (FR)</button>
      <button type="button" class="dl-btn dl-btn-en" onclick="downloadCv('en')">⬇ Download CV (EN)</button>
    </div>
  </div>
{fr_body}
{en_body}
  <script>
    function showLang(lang) {{
      document.querySelectorAll('.cv-lang').forEach(function(el) {{ el.classList.remove('active'); }});
      document.getElementById('cv-' + lang).classList.add('active');
      document.querySelectorAll('.lang-tab').forEach(function(btn) {{
        btn.classList.toggle('active', btn.dataset.lang === lang);
      }});
      document.documentElement.lang = lang;
    }}
    function downloadCv(lang) {{
      document.querySelectorAll('.cv-lang').forEach(function(el) {{ el.classList.remove('active', 'print-target'); }});
      var target = document.getElementById('cv-' + lang);
      target.classList.add('active', 'print-target');
      window.print();
      setTimeout(function() {{ target.classList.remove('print-target'); showLang(lang); }}, 500);
    }}
  </script>
</body>
</html>"""

    (publish / "index.html").write_text(out, encoding="utf-8")
    shutil.copy(publish / "index.html", publish / "CV_Hybrid_2026_FINAL_2.html")
    if doc_cv.exists():
        shutil.copy(publish / "index.html", doc_cv / "CV_Hybrid_2026_FINAL_2.html")
    assert_locked_content(out)
    print("OK", len(out), "— vérifié localement, pas de push automatique")


if __name__ == "__main__":
    build()
