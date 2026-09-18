Absolutely. Let's move to **Lab 15 — Azure Monitor**.

This lab is important because we're moving from **building Azure resources** to **observing and operating them**.

# 🧪 Lab 15 — Azure Monitor

The goal is to understand three things:

```text
Metrics → Logs → Alerts
```

Think of Azure Monitor as the **eyes and ears of your Azure infrastructure**.

---

# 1. What is Azure Monitor?

Imagine you have:

```text
                  Your Azure application
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
         VM          Azure SQL       Cosmos DB
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                   Azure Monitor
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Metrics       Logs       Alerts
```

Azure Monitor collects and analyzes telemetry from Azure resources and applications. It includes metrics, logs, alerts, and related monitoring capabilities.

---

# 2. The three concepts ⭐

## Metrics

**Metrics = numbers measured over time.**

For example, for a VM:

```text
CPU = 72%
Memory = 65%
Network In = 10 MB
Network Out = 4 MB
```

You can visualize:

```text
CPU
100% │                 ╭─╮
 80% │          ╭──────╯ ╰─╮
 60% │     ╭────╯           ╰──
 40% │─────╯
     └──────────────────────────
              Time
```

Metrics are excellent for seeing **how much** something is being used.

---

# 3. Logs

Logs are more detailed records/events.

For example:

```text
2026-09-17 10:20:01 INFO User logged in
2026-09-17 10:20:05 INFO Request received
2026-09-17 10:20:07 ERROR Database connection failed
```

Logs answer questions like:

> **What happened?**

Azure Monitor uses **Log Analytics workspaces** and **Kusto Query Language (KQL)** to query many types of collected logs.

So:

```text
Metric:
CPU = 95%

Log:
2026-09-17 10:30
Python worker failed
```

Metrics tell you **something is wrong**.

Logs can help you understand **what happened**.

---

# 4. Alerts

Alerts allow Azure to react when a condition is met.

Example:

```text
CPU > 80%
     │
     ▼
Azure Monitor
     │
     ▼
Alert
     │
     ▼
Notification
```

For example:

```text
IF CPU > 80%
FOR 5 minutes
THEN create alert
```

You can then configure an action such as an email notification or another supported action.

---

# 5. Our practical lab

We'll use your existing Azure resources rather than creating unnecessary infrastructure.

You already have resources such as:

```text
Resource Group: amine_saad
│
├── VM
├── Storage Account
├── Azure SQL
├── Cosmos DB
└── Key Vault
```

We'll start with the **VM**, because it makes metrics easy to understand.

---

# 6. Open your VM

Azure Portal:

**Virtual machines → your VM**

Then find:

**Monitoring → Metrics**

You'll see something similar to:

```text
Metric
│
├── Percentage CPU
├── Network In Total
├── Network Out Total
├── Disk Read Bytes
└── Disk Write Bytes
```

Select:

> **Percentage CPU**

Set:

> Time range → Last 30 minutes

You should get a graph.

---

# 7. Generate some CPU activity

SSH into your Ubuntu VM.

Then run:

```bash
top
```

You can also generate CPU activity for testing:

```bash
yes > /dev/null &
```

Check:

```bash
top
```

You should see CPU utilization increase.

Stop it afterward:

```bash
pkill yes
```

Now return to:

**Azure Portal → VM → Metrics**

and observe:

```text
CPU
│
│             ███
│           ███████
│        ███████████
│___________
└────────────────────
        time
```

You've just created your first monitoring experiment.

---

# 8. Metric dimensions

You'll notice Azure metrics can have different dimensions depending on the resource.

Conceptually:

```text
Metric
  │
  ├── CPU
  │
  ├── Network
  │
  └── Disk
```

This is different from logs.

Metrics are generally optimized for **time-series numerical measurements**.

---

# 9. Create your first alert 🚨

Now go to:

**VM → Alerts → Create → Alert rule**

You'll configure something like:

### Scope

Your VM.

### Condition

Select:

> Percentage CPU

Condition:

```text
Greater than
```

Threshold:

```text
80
```

For the first lab, you can use a short evaluation period so you can test it.

Conceptually:

```text
CPU > 80%
    │
    │ condition true
    ▼
Azure Monitor
    │
    ▼
Alert rule
    │
    ▼
Action Group
```

---

# 10. What is an Action Group?

An alert itself isn't necessarily the notification destination.

An **Action Group** defines what happens when the alert fires.

For example:

```text
Alert
 │
 ▼
Action Group
 │
 ├── Email
 ├── SMS
 ├── Push notification
 └── Other supported actions
```

For your lab, configure an **email notification** to an address you control.

---

# 11. Your first monitoring architecture

After this lab, you should understand:

```text
                    Azure VM
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
        CPU          Network       Disk
          │            │            │
          └────────────┼────────────┘
                       ▼
                 Azure Monitor
                       │
              ┌────────┴────────┐
              ▼                 ▼
           Metrics             Logs
              │                 │
              └────────┬────────┘
                       ▼
                    Alerts
                       │
                       ▼
                  Action Group
                       │
                       ▼
                    Email
```

---

# 12. Then we'll learn Log Analytics + KQL

This is the next important part.

We'll create/use a:

> **Log Analytics Workspace**

Then you'll learn KQL.

For example:

```kusto
AzureActivity
| take 10
```

or:

```kusto
AzureActivity
| where ActivityStatusValue == "Failed"
| take 20
```

This is where Azure monitoring starts becoming much more powerful.

---

# 13. Don't confuse these services

You now have several Azure services that can seem similar:

```text
Azure Monitor
     │
     ├── Metrics
     ├── Logs
     ├── Alerts
     └── Log Analytics
```

while:

```text
Application Insights
     │
     ├── Requests
     ├── Exceptions
     ├── Dependencies
     ├── Traces
     └── Application performance
```

So **Lab 15 = infrastructure/resource monitoring**.

**Lab 16 = application monitoring**.

We'll see the difference clearly when we put a Python/FastAPI application under Application Insights.

---

## Lab 15 roadmap

```text
LAB 15 — AZURE MONITOR
│
├── 1. Understand Monitor             ✅ theory
│
├── 2. Metrics
│   └── VM CPU                         ← NOW
│
├── 3. Generate CPU activity
│
├── 4. Create Alert
│
├── 5. Action Group
│
├── 6. Log Analytics Workspace
│
├── 7. Logs
│
├── 8. KQL ⭐
│
├── 9. Query Azure activity
│
└── 10. Monitoring architecture
```

**Start with Step 2:** open your existing VM → **Monitoring → Metrics → Percentage CPU → Last 30 minutes**. Once you have the graph, we'll create the CPU alert and then move into **Log Analytics + KQL**, which is the more important part of this lab.



Absolutely. From here I'll keep the labs **concept-first, then hands-on, then troubleshooting, then architecture**.

# Lab 15 — Log Analytics + KQL

This is the part of Azure Monitor where you start learning **real observability** rather than just looking at CPU graphs.

Microsoft's current architecture separates the concepts like this:

* **Azure Monitor** = overall monitoring platform
* **Log Analytics workspace** = central store for log data
* **Log Analytics** = portal tool used to query/analyze that data
* **KQL** = language used to query the logs
* **Alerts/Workbooks** = things you can build using those queries ([Microsoft Learn][1])

---

# 1. First: understand the architecture

Think of it as a pipeline:

```text
Azure resources
     │
     │ telemetry / logs
     ▼
Azure Monitor
     │
     │ collection
     ▼
Log Analytics Workspace
     │
     ├── AzureActivity
     ├── Heartbeat
     ├── Syslog
     ├── Perf
     ├── SecurityEvent
     └── ...
          │
          ▼
         KQL
          │
          ▼
   Analysis / Charts / Alerts
```

A Log Analytics workspace is essentially a **central data store for logs** from Azure and non-Azure resources. The workspace organizes data into tables. ([Microsoft Learn][2])

---

# 2. Very important: Metrics ≠ Logs

You've already seen metrics.

### Metrics

Example:

```text
CPU = 73%
```

It's a numerical measurement over time.

### Logs

Example:

```text
TimeGenerated: 10:32:14
Operation: Create Virtual Machine
Status: Succeeded
Resource: VM01
Caller: amine@...
```

A log contains much richer contextual information.

So:

```text
Metric:
"What is happening?"

Log:
"What happened, when, where, and with what details?"
```

That's a simplified mental model, but it's useful.

---

# 3. Create a Log Analytics Workspace

Go to:

**Azure Portal → Search → Log Analytics workspaces → Create**

Use:

| Setting        | Value                  |
| -------------- | ---------------------- |
| Subscription   | `Azure subscription 1` |
| Resource group | `amine_saad`           |
| Workspace name | `law-amine-lab`        |
| Region         | `South Africa North`   |

If Azure requires a unique name, use something like:

```text
law-amine-lab-2026
```

Then:

**Review + create → Create**

Microsoft recommends a workspace as the central destination for collected log data, and there's no direct charge merely for creating/maintaining the workspace; costs are primarily associated with data ingestion and retention. ([Microsoft Learn][2])

---

# 4. Important distinction: workspace vs Log Analytics

This confuses many beginners.

They're related but not identical.

```text
Log Analytics Workspace
        │
        │ stores
        ▼
Azure Monitor Logs
        │
        │ queried by
        ▼
Log Analytics
        │
        │ using
        ▼
KQL
```

So:

> **Workspace = where the data lives**

> **Log Analytics = the tool/interface used to query it**

> **KQL = the language used to query it**

---

# 5. Now we need data

Creating the workspace alone doesn't magically give you all resource logs.

Azure resources can generate resource logs, but you need to configure collection/routing, typically through **Diagnostic settings**, to send those logs to a Log Analytics workspace. ([Microsoft Learn][3])

We'll start with something extremely useful:

## Azure Activity Log

The Activity Log records **management/control-plane operations** on Azure resources.

Examples:

```text
Create VM
Delete storage account
Change NSG
Create Key Vault
Modify firewall
Start VM
Stop VM
```

This is very different from application logs.

---

# 6. Go to Log Analytics

Open:

**Azure Portal → Monitor → Logs**

You should see the Log Analytics query interface.

Make sure the selected scope is:

```text
law-amine-lab
```

or your actual workspace name.

Microsoft's Log Analytics interface supports both Simple mode and KQL mode; we'll use **KQL mode** because your goal is to learn the actual language. ([Microsoft Learn][4])

---

# 7. Your first KQL query ⭐

Enter:

```kusto
AzureActivity
| take 10
```

Then click:

**Run**

This means:

```text
AzureActivity
     │
     ▼
take 10
     │
     ▼
Return 10 records
```

This is your first KQL query.

---

# 8. Understand the KQL structure

This is fundamental.

```kusto
AzureActivity
| take 10
```

Think:

```text
TABLE
  │
  ▼
AzureActivity
  │
  │ |
  ▼
OPERATOR
  │
  ▼
take 10
```

The `|` is called the **pipe**.

It means:

> Take the result from the previous operation and pass it to the next operation.

This makes KQL very readable.

---

# 9. See only selected columns

Try:

```kusto
AzureActivity
| project TimeGenerated, OperationNameValue, ActivityStatusValue
| take 20
```

Now we're using:

```text
project
```

`project` means:

> Select the columns I want.

Conceptually:

```text
AzureActivity
     │
     ▼
project
     │
     ├── TimeGenerated
     ├── OperationNameValue
     └── ActivityStatusValue
```

---

# 10. Filter logs with `where`

Now:

```kusto
AzureActivity
| where ActivityStatusValue == "Failed"
| project TimeGenerated, OperationNameValue, ActivityStatusValue
| take 20
```

This means:

```text
AzureActivity
      │
      ▼
WHERE status = Failed
      │
      ▼
PROJECT selected columns
      │
      ▼
20 records
```

This is already much more powerful.

You can ask:

> "Show me Azure operations that failed."

---

# 11. Filter by time

KQL has a very useful function:

```text
ago()
```

For example:

```kusto
AzureActivity
| where TimeGenerated > ago(1h)
| take 50
```

Meaning:

> Give me records from the last hour.

You can also use:

```kusto
ago(30m)
```

for 30 minutes.

```kusto
ago(24h)
```

for 24 hours.

```kusto
ago(7d)
```

for 7 days.

---

# 12. Combine filters

Now:

```kusto
AzureActivity
| where TimeGenerated > ago(24h)
| where ActivityStatusValue == "Failed"
| project
    TimeGenerated,
    Caller,
    OperationNameValue,
    ActivityStatusValue
| order by TimeGenerated desc
```

Read it from top to bottom:

```text
AzureActivity
      ↓
last 24 hours
      ↓
failed operations
      ↓
select useful columns
      ↓
newest first
```

This is the way I want you to learn KQL: **read the query as a pipeline.**

---

# 13. Aggregation — where KQL becomes powerful

Suppose you want to know:

> How many operations occurred for each status?

Try:

```kusto
AzureActivity
| summarize count() by ActivityStatusValue
```

You might get:

```text
ActivityStatusValue    Count
--------------------    -----
Succeeded               150
Failed                    12
Started                   20
```

The exact numbers depend on your environment.

The important operator is:

```text
summarize
```

It means:

> Aggregate data.

---

# 14. Count failures

```kusto
AzureActivity
| where ActivityStatusValue == "Failed"
| summarize FailureCount = count()
```

Now KQL calculates a single value.

```text
FailureCount
------------
12
```

This is extremely useful for monitoring.

---

# 15. Group failures by operation

```kusto
AzureActivity
| where ActivityStatusValue == "Failed"
| summarize FailureCount = count()
    by OperationNameValue
| order by FailureCount desc
```

Now you can see something like:

```text
Operation                              Failures
------------------------------------   --------
Microsoft.Compute/...                   8
Microsoft.KeyVault/...                  3
Microsoft.Storage/...                   1
```

Again, your actual values will differ.

---

# 16. Group by resource

Try:

```kusto
AzureActivity
| where ActivityStatusValue == "Failed"
| summarize FailureCount = count()
    by ResourceGroup
| order by FailureCount desc
```

Now you're asking:

> Which resource groups are producing the most failed operations?

This is already an operational troubleshooting query.

---

# 17. Time-series analysis ⭐

Now we start thinking like an SRE/Cloud Engineer.

Try:

```kusto
AzureActivity
| summarize Operations = count()
    by bin(TimeGenerated, 1h)
| order by TimeGenerated asc
```

The important function is:

```text
bin(TimeGenerated, 1h)
```

It groups timestamps into **one-hour buckets**.

Conceptually:

```text
10:00 ── 25 operations
11:00 ── 40 operations
12:00 ── 18 operations
13:00 ── 72 operations
```

Now you can visualize activity over time.

---

# 18. The KQL mental model

At this point, memorize these operators:

| KQL         | Meaning             |
| ----------- | ------------------- |
| `where`     | Filter rows         |
| `project`   | Select columns      |
| `take`      | Return sample rows  |
| `order by`  | Sort                |
| `summarize` | Aggregate           |
| `count()`   | Count records       |
| `by`        | Group               |
| `bin()`     | Create time buckets |
| `ago()`     | Relative time       |

These are your **KQL fundamentals**.

---

# 19. The most important conceptual difference

Don't think of KQL as SQL.

They look similar:

```sql
SELECT *
FROM Customers
WHERE age > 20;
```

KQL:

```kusto
Customers
| where age > 20
```

But KQL is designed around a **pipeline**.

Think:

```text
Table
  ↓
Filter
  ↓
Transform
  ↓
Aggregate
  ↓
Sort
  ↓
Visualize
```

That's why this is so readable:

```kusto
AzureActivity
| where TimeGenerated > ago(24h)
| where ActivityStatusValue == "Failed"
| summarize count() by OperationNameValue
| order by count_ desc
```

---

# 20. What we will do next

Now that you have the foundation, we'll build a **real monitoring lab**:

```text
                    Azure VM
                       │
                       ▼
                Azure Monitor
                       │
                       ▼
             Azure Monitor Agent
                       │
                       ▼
            Data Collection Rule
                       │
                       ▼
             Log Analytics
               Workspace
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Syslog       Perf       Heartbeat
          │            │            │
          └────────────┼────────────┘
                       ▼
                      KQL
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Queries       Charts       Alerts
```

The modern Azure Monitor architecture uses data collection mechanisms such as **Data Collection Rules (DCRs)** to control what telemetry is collected and where it goes. ([Microsoft Learn][5])

And there's an important distinction: **Log Analytics workspaces are for logs/traces queried with KQL**, while **Azure Monitor workspaces are currently focused on Prometheus metrics**. Don't confuse the two just because their names are similar. ([Microsoft Learn][6])

### Your immediate exercise

Open **Monitor → Logs**, select your new workspace, and run these **in order**:

```kusto
AzureActivity
| take 10
```

```kusto
AzureActivity
| project TimeGenerated, OperationNameValue, ActivityStatusValue
| take 20
```

```kusto
AzureActivity
| where ActivityStatusValue == "Failed"
| project TimeGenerated, Caller, OperationNameValue
| order by TimeGenerated desc
```

```kusto
AzureActivity
| summarize count() by ActivityStatusValue
```

If `AzureActivity` has no results, that's not necessarily a problem—the workspace may simply not have the relevant data in its current scope/time range. We'll then configure the appropriate data collection/diagnostic settings rather than guessing. Azure resource logs can take several minutes to appear after collection is configured. ([Microsoft Learn][7])

[Microsoft Learn — Log queries in Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-query-overview?utm_source=chatgpt.com)
[Microsoft Learn — Log Analytics workspace overview](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-workspace-overview?utm_source=chatgpt.com)

[1]: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-query-overview?utm_source=chatgpt.com "Log queries in Azure Monitor - Azure Monitor | Microsoft Learn"
[2]: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-workspace-overview?utm_source=chatgpt.com "Log Analytics workspace overview - Azure Monitor | Microsoft Learn"
[3]: https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/monitor-azure-resource?utm_source=chatgpt.com "Monitor Azure resources with Azure Monitor - Azure Monitor | Microsoft Learn"
[4]: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-overview?toc=%2Fazure%2Fnetwork-watcher%2Ftoc.json&utm_source=chatgpt.com "Overview of Log Analytics in Azure Monitor - Azure Monitor | Microsoft Learn"
[5]: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-platform-logs?utm_source=chatgpt.com "Azure Monitor Logs - Azure Monitor | Microsoft Learn"
[6]: https://learn.microsoft.com/en-us/azure/application-insights/?utm_source=chatgpt.com "Azure Monitor overview - Azure Monitor | Microsoft Learn"
[7]: https://learn.microsoft.com/en-us/azure/azure-monitor/platform/tutorial-resource-logs?utm_source=chatgpt.com "Collect resource logs from an Azure resource - Azure Monitor | Microsoft Learn"
