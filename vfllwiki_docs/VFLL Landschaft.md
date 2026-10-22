Überblick über Webservices, Servers, User ... der VFLL-IT-Landschaft

```mermaid
%% VFLL / science-and-more – Infrastruktur-Landschaft
flowchart LR

  %% ================= Personen =================
  subgraph PEOPLE["👥 Personen"]
    direction TB
    uli(["scienceuli"])
    nn(["NN"])
    gs(["GS"])
    annika(["Annika"])
    fobi(["FOBI"])
    cms(["CMS"])
    kt(["KT"])
    blog(["Blog"])
    users(["öffentl. Nutzer:innen"])
  end

  %% ================= Code & Orchestrierung =================
  subgraph GH["GitHub · scienceuli"]
    direction TB
    r_cms["vfllcms"]
    r_fobi["vfllfobi"]
    r_admin["vflladmin"]
    r_koll["vfllkoll"]
    r_wiki["vfllwiki"]
    r_more["…"]
    r_ansible[["⚙️ Ansible.Build"]]
  end

  subgraph CB["Codeberg · scienceuli"]
    inv[("🔒 Inventories<br/>(privat)")]
  end
  
  subgraph PD["Proton Drive"]
    keepass[("🔐 KeePass-Datenbank<br/>Passwörter (verschlüsselt)")]
  end

  subgraph VC["Vercel"]
    vc_wiki["VFLL-Wiki<br/>(Zensical-Build)<br/>Domain: wiki.vfll.de"]
  end

  %% ================= Webdienste =================
  subgraph SVC["🌐 Webdienste XY.vfll.de"]
    direction TB
    s_www["www.vfll.de"]
    s_fobi["veranstaltungskalender.vfll.de"]
    s_admin["memberadmin.vfll.de"]
    s_koll["kolltool.vfll.de"]
    s_blog["lektorenverband.de"]
    s_more["… .vfll.de"]
  end

  %% ================= all-inkl =================
  subgraph AI["all-inkl"]
    direction TB
    dns_vfll{{"Domain vfll.de<br/>DNS: A-Records"}}
    mail["✉️ Mailserver vfll.de"]
  end

  %% ================= Netcup =================
  subgraph NC["Netcup"]
    direction TB
    dom_sam{{"Domain science-and-more.com"}}
    subgraph APPSRV["App-Server"]
      direction TB
      euler["euler.science-and-more.com"]
      faraday["faraday.science-and-more.com"]
      nc_more["… .science-and-more.com"]
    end
    monitor["📈 monitor.sam-projekte.de<br/>Grafana"]
    backup[("💾 backup.science-and-more.com<br/>DB- & File-Backups")]
  end

  subgraph NCF["Netcup · Account fobi"]
    moodle["🎓 moodle.vfll.de"]
  end

  %% ================= Hetzner =================
  subgraph HZ["Hetzner"]
    direction TB
    hz_srv["Server …"]
    storagebox[("Storage Box")]
  end

  %% ================= Deploy / Build =================
  r_cms --> s_www
  r_fobi --> s_fobi
  r_admin --> s_admin
  r_koll --> s_koll
  r_more --> s_more
  r_wiki -->|"GitHub Action<br/>(Zensical)"| vc_wiki

  %% ================= DNS =================
  SVC -.->|"Namensauflösung"| dns_vfll
  dns_vfll -.->|"A-Records"| APPSRV
  dom_sam -.- APPSRV

  %% ================= Orchestrierung =================
  r_ansible === inv
  r_ansible ==>|"provisioniert<br/>Hosts & Apps"| APPSRV
  r_ansible ==> monitor
  r_ansible ==> backup
  r_ansible ==> hz_srv

  %% ================= Monitoring & Backup =================
  monitor -.->|"überwacht"| APPSRV
  monitor -.->|"überwacht"| hz_srv
  APPSRV -->|"Backups"| backup
  hz_srv -->|"Backups"| backup
  backup -->|"Spiegelung"| storagebox

  %% ================= Zugriffe =================
  uli & nn -.->|"Repos"| GH
  uli & nn -.->|"Inventories"| inv
  uli & gs -.->|"SCP/CCP"| NC
  uli & nn -.->|"Zugang"| monitor
  uli -.->|"Zugang"| backup
  uli & annika -.->|"Zugang"| moodle
  uli & gs -.->|"Zugang"| s_admin
  uli & kt -.->|"Zugang"| s_koll
  uli & cms -.-> |"Zugang"| s_www
  uli & fobi -.-> |"Zugang"| s_fobi
  blog -.-> |"Zugang"| s_blog
  users -.->|"nutzen"| SVC

  %% ================= Styles =================
  classDef person fill:#fde68a,stroke:#b45309,color:#000
  classDef repo fill:#e0e7ff,stroke:#4338ca,color:#000
  classDef special fill:#c7d2fe,stroke:#312e81,stroke-width:2px,color:#000
  classDef server fill:#dcfce7,stroke:#15803d,color:#000
  classDef infra fill:#fee2e2,stroke:#b91c1c,color:#000
  classDef domain fill:#f3f4f6,stroke:#6b7280,color:#000
  classDef svc fill:#e0f2fe,stroke:#0369a1,color:#000

  class uli,nn,gs,annika,users person
  class r_cms,r_fobi,r_admin,r_koll,r_wiki,r_more repo
  class r_ansible,inv special
  class euler,faraday,nc_more,hz_srv,moodle server
  class monitor,backup,storagebox infra
  class dns_vfll,dom_sam,mail domain
  class s_www,s_fobi,s_admin,s_koll,s_more,vc_wiki svc

```


### Anmerkungen

- Ein Subgraph pro Provider (GitHub, Codeberg, ProtonDrive, Vercel, all-inkl, Netcup, Netcup·fobi, Hetzner), 
- `XY.vfll.de` steht für die Vfll Web Services. Die Kanten-Stile haben folgende Bedeutungen:

- **Duurchgezogene Pfeile** zeigen Deployments, Backups and Mirror-Flows.
- **Dicke Pfeile** zeigen die Ansible-Orchestrierung. `Ansible.Build` it mit den Inventories auf Codeberg verknüpft.
- **Gepunktete Pfeile** zeigen DNS-Auflösungen, Monitoring and User-Zugänge an.

