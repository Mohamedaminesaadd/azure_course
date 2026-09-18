Yes — **absolutely**. And it's actually a very good extension of your Lab 15.

The architecture can be:

```text
Azure Resources
      │
      ▼
Azure Monitor
      │
      ▼
Log Analytics Workspace
      │
      ▼
     KQL
      │
      ▼
Power BI
      │
      ├── Charts
      ├── KPIs
      ├── Trends
      └── Dashboards
```

Microsoft officially supports integrating **Azure Monitor Logs / Log Analytics with Power BI**. You can export a KQL query from Log Analytics to Power BI Desktop, or create a Power BI dataset directly from a Log Analytics query. ([Microsoft Learn][1])

## What I'd recommend for your lab

Don't connect Power BI directly to raw Azure logs and throw everything into a dashboard.

Instead, learn this professional workflow:

```text
Raw logs
   ↓
Log Analytics
   ↓
KQL transformation
   ↓
Clean analytical dataset
   ↓
Power BI
   ↓
Dashboard
```

For example, suppose `AzureActivity` contains thousands of events.

Instead of sending everything to Power BI, write:

```kusto
AzureActivity
| where TimeGenerated > ago(7d)
| summarize
    Operations = count()
    by bin(TimeGenerated, 1h), ActivityStatusValue
| order by TimeGenerated asc
```

Power BI can then visualize:

```text
Azure Operations — Last 7 Days

Operations
  │
80│             ╭──╮
60│      ╭──────╯  ╰──╮
40│──────╯             ╰──
20│
  └────────────────────────
        Time
```

You could also create KPIs:

```text
┌─────────────────┐
│ Total Operations│
│      1,284      │
└─────────────────┘

┌─────────────────┐
│ Failed          │
│       17        │
└─────────────────┘

┌─────────────────┐
│ Success Rate    │
│      98.7%      │
└─────────────────┘
```

### Two ways to connect

**Option 1 — Power BI Desktop**

From Log Analytics:

**Logs → write KQL → Run → Export → Power BI**

Microsoft provides a **Power BI (as an M query)** export option that you can open in Power BI Desktop. ([Microsoft Learn][1])

**Option 2 — Power BI Service**

Log Analytics can also create a new Power BI dataset directly from a query. Some advanced Power BI capabilities—such as sharing, scheduled refresh, dataflows, and incremental refresh—can require appropriate Power BI licensing. ([Microsoft Learn][1])

### One important distinction

Don't confuse:

**"Power BI → Log Analytics"**

with:

**"Log Analytics → Power BI."**

For **our current lab**, we're doing:

```text
Azure Monitor
      ↓
Log Analytics
      ↓
KQL
      ↓
Power BI
```

There is also a separate Microsoft integration where **Power BI itself sends certain activity/semantic-model logs into Log Analytics**. That's a different use case. ([Microsoft Learn][2])

---

## I suggest we add this to Lab 15

```text
LAB 15 — AZURE MONITOR
│
├── Metrics
│
├── Alerts
│
├── Log Analytics Workspace
│
├── KQL ⭐
│   ├── where
│   ├── project
│   ├── summarize
│   ├── count
│   ├── bin
│   └── ago
│
├── Diagnostic Settings
│
├── Azure Monitor Agent
│
├── Data Collection Rules
│
└── Power BI ⭐
    ├── KQL dataset
    ├── Power BI Desktop
    ├── Data modeling
    ├── KPIs
    ├── Charts
    └── Azure monitoring dashboard
```

That will give you a much more complete understanding of **Azure observability + analytics**.

**Next, we can build the actual Power BI dashboard from your `AzureActivity` KQL query**, step by step, rather than just discussing it.

[1]: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-powerbi?utm_source=chatgpt.com "Log Analytics integration with Power BI - Azure Monitor | Microsoft Learn"
[2]: https://learn.microsoft.com/en-us/power-bi/transform-model/log-analytics/desktop-loganalytics-reportguide-datasets?utm_source=chatgpt.com "Using Azure Log Analytics in Power BI - Power BI | Microsoft Learn"
