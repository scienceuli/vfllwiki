für Monitoring:

- SSH Login Attempts
- System Logs
- Docker Container logs
- Kernel Logs

![[attachments/grafana_log.png]]

![[attachments/grafana_dashboard.png]]

- **Grafana** for visualization and dashboards
- **Loki** for log aggregation and analysis
- **Promtail** for log shipping


```
┌─────────────────────────────────────────────────────────────┐
│                    LOG MONITORING SERVER                   │
│  ┌─────────────┐ ┌─────────────────────┐                   │
│  │   Grafana   │ │        Loki         │                   │
│  │    :3000    │ │       :3100         │                   │
│  └─────────────┘ └─────────────────────┘                   │
│  ┌─────────────────────┐                                   │
│  │      Promtail       │                                   │
│  │    (log shipper)    │                                   │
│  └─────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Network
                              │
┌─────────────────────────────────────────────────────────────┐
│                    REMOTE SERVERS                          │
│  ┌─────────────────────┐                                   │
│  │      Promtail       │                                   │
│  │    (log shipper)    │                                   │
│  └─────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Log Aggregation**: Promtail ships logs from Application Servers to Loki
2. **Visualization**: Grafana queries Loki for log dashboards and analysis
3. **Alerting**: Grafana evaluates log-based rules and sends alerts via configured channels

The deployment structure includes:

```
├── deploy-remote.sh
├── docker-compose-remote.yml
├── docker-compose.yml
├── grafana\
│   └── provisioning\
│       ├── alerting\
│       ├── dashboards\
│       └── datasources\
├── loki\
│   └── local-config.yaml
└── promtail\
    └── config.yml
```



