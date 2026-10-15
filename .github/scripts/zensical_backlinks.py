import os
import re

# Speicher für den Link-Graphen: { ziel_url: [liste_von_quell_seiten] }
LINK_GRAPH = {}

def on_env(env, config, files):
    """
    Schritt 1: Durchläuft alle Markdown-Dateien vor dem Build,
    um die internen Verlinkungen zu analysieren.
    """
    global LINK_GRAPH
    LINK_GRAPH.clear()
    
    # Regulärer Ausdruck für Standard-Markdown-Links [Text](Ziel)
    # Ignoriert externe Links (http/https) und reine Anker (#)
    link_pattern = re.compile(r'\[.*?\]\((?!https?://|#)(.*?)\)')

    for f in files:
        if not f.is_documentation_page():
            continue
            
        try:
            with open(f.abs_src_path, 'r', encoding='utf-8') as src:
                content = src.read()
                links = link_pattern.findall(content)
                
                for target in links:
                    # Bereinige den Link-Pfad (entferne Anker und Query-Parameter)
                    clean_target = target.split('#')[0].split('?')[0]
                    if not clean_target:
                        continue
                        
                    # Bestimme den relativen Pfad zum Ziel von der Wurzel aus
                    # Falls der Link relativ zur aktuellen Datei ist, auflösen:
                    base_dir = os.path.dirname(f.src_uri)
                    target_uri = os.path.normpath(os.path.join(base_dir, clean_target)).replace('\\', '/')
                    
                    if target_uri not in LINK_GRAPH:
                        LINK_GRAPH[target_uri] = set()
                    
                    # Füge die aktuelle Seite als Backlink für das Ziel hinzu
                    LINK_GRAPH[target_uri].add(f)
        except Exception:
            pass # Ignoriere fehlerhafte Dateien robust
    return env

def on_page_content(html, page, config, files):
    """
    Schritt 2: Injiziert die gesammelten Backlinks am Ende des Contents,
    bevor Zensical die finale HTML-Datei schreibt.
    """
    global LINK_GRAPH
    
    # Bestimme die URI der aktuellen Seite (z.B. 'index.md' oder 'folder/page.md')
    current_uri = page.file.src_uri
    
    # Prüfe, ob es Backlinks für diese Seite gibt
    backlinks = LINK_GRAPH.get(current_uri, set())
    
    # Verhindere, dass eine Seite sich selbst backlinkt
    backlinks = [b for b in backlinks if b.src_uri != current_uri]
    
    if backlinks:
        # Generiere das HTML für die Backlinks-Sektion
        backlinks_html = ['<div class="zensical-backlinks">', '<h2>Backlinks</h2>', '<ul>']
        
        for source_file in backlinks:
            # Berechne den relativen Pfad von der aktuellen Seite zur Quellseite
            # Damit die Links auch im lokalen Preview-Server funktionieren
            relative_url = page.url_relative_to(source_file.url)
            
            # Falls der Seitentitel leer ist, nutze den Dateinamen
            title = source_file.page.title if (hasattr(source_file, 'page') and source_file.page and source_file.page.title) else source_file.name
            
            backlinks_html.append(f'<li><a href="{relative_url}">{title}</a></li>')
            
        backlinks_html.append('</ul></div>')
        
        # Füge die Sektion am Ende des Contents an
        html += '\n' + '\n'.join(backlinks_html)
        
    return html