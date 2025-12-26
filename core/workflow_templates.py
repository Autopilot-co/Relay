"""
Relay - n8n Workflow Templates
Common workflow patterns for AI to learn from and adapt

These templates represent real, working n8n workflows that AI can use as reference
when generating new workflows based on user requests.
"""

# Template 1: Schedule + HTTP Request (API monitoring, data fetching)
SCHEDULE_HTTP_TEMPLATE = {
    "name": "Schedule + HTTP Request",
    "nodes": [
        {
            "id": "schedule-1",
            "name": "Schedule Trigger",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1,
            "position": [250, 300],
            "parameters": {
                "rule": {
                    "interval": [
                        {"field": "hours", "hoursInterval": 1}
                    ]
                }
            }
        },
        {
            "id": "http-1",
            "name": "HTTP Request",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [450, 300],
            "parameters": {
                "method": "GET",
                "url": "https://api.example.com/data",
                "authentication": "none",
                "options": {}
            }
        }
    ],
    "connections": {
        "Schedule Trigger": {
            "main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]
        }
    },
    "active": False
}

# Template 2: Webhook + Process + Response (API endpoints, webhooks)
WEBHOOK_TEMPLATE = {
    "name": "Webhook Handler",
    "nodes": [
        {
            "id": "webhook-1",
            "name": "Webhook",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [250, 300],
            "parameters": {
                "path": "my-webhook",
                "responseMode": "lastNode",
                "options": {}
            },
            "webhookId": "example-webhook-id"
        },
        {
            "id": "code-1",
            "name": "Process Data",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [450, 300],
            "parameters": {
                "jsCode": "// Process incoming webhook data\\nreturn items;"
            }
        },
        {
            "id": "respond-1",
            "name": "Respond to Webhook",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [650, 300],
            "parameters": {
                "options": {}
            }
        }
    ],
    "connections": {
        "Webhook": {
            "main": [[{"node": "Process Data", "type": "main", "index": 0}]]
        },
        "Process Data": {
            "main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]
        }
    },
    "active": False
}

# Template 3: Schedule + Database Query + Email (Reports, alerts)
SCHEDULE_DB_EMAIL_TEMPLATE = {
    "name": "Database Report Email",
    "nodes": [
        {
            "id": "schedule-1",
            "name": "Daily at 9 AM",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1,
            "position": [250, 300],
            "parameters": {
                "rule": {
                    "interval": [
                        {"field": "cronExpression", "expression": "0 9 * * *"}
                    ]
                }
            }
        },
        {
            "id": "postgres-1",
            "name": "Query Database",
            "type": "n8n-nodes-base.postgres",
            "typeVersion": 2,
            "position": [450, 300],
            "parameters": {
                "operation": "executeQuery",
                "query": "SELECT * FROM users WHERE created_at > NOW() - INTERVAL '24 hours'"
            },
            "credentials": {
                "postgres": {
                    "id": "CREDENTIAL_ID_PLACEHOLDER",
                    "name": "PostgreSQL account"
                }
            }
        },
        {
            "id": "email-1",
            "name": "Send Email",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2,
            "position": [650, 300],
            "parameters": {
                "fromEmail": "reports@company.com",
                "toEmail": "team@company.com",
                "subject": "Daily User Report",
                "emailFormat": "html",
                "message": "={{$json.body}}"
            },
            "credentials": {
                "smtp": {
                    "id": "CREDENTIAL_ID_PLACEHOLDER",
                    "name": "SMTP account"
                }
            }
        }
    ],
    "connections": {
        "Daily at 9 AM": {
            "main": [[{"node": "Query Database", "type": "main", "index": 0}]]
        },
        "Query Database": {
            "main": [[{"node": "Send Email", "type": "main", "index": 0}]]
        }
    },
    "active": False
}

# Template 4: HTTP Request + IF + Multiple Actions (Conditional logic)
CONDITIONAL_TEMPLATE = {
    "name": "Conditional Processing",
    "nodes": [
        {
            "id": "http-1",
            "name": "Fetch Data",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [250, 300],
            "parameters": {
                "method": "GET",
                "url": "https://api.example.com/status"
            }
        },
        {
            "id": "if-1",
            "name": "Check Status",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [450, 300],
            "parameters": {
                "conditions": {
                    "string": [
                        {
                            "value1": "={{$json.status}}",
                            "operation": "equals",
                            "value2": "success"
                        }
                    ]
                }
            }
        },
        {
            "id": "action-success",
            "name": "Success Action",
            "type": "n8n-nodes-base.noOp",
            "typeVersion": 1,
            "position": [650, 200]
        },
        {
            "id": "action-fail",
            "name": "Failure Action",
            "type": "n8n-nodes-base.noOp",
            "typeVersion": 1,
            "position": [650, 400]
        }
    ],
    "connections": {
        "Fetch Data": {
            "main": [[{"node": "Check Status", "type": "main", "index": 0}]]
        },
        "Check Status": {
            "main": [
                [{"node": "Success Action", "type": "main", "index": 0}],
                [{"node": "Failure Action", "type": "main", "index": 0}]
            ]
        }
    },
    "active": False
}

# Template 5: Google Sheets Read + Process + Update (Spreadsheet automation)
GOOGLE_SHEETS_TEMPLATE = {
    "name": "Google Sheets Automation",
    "nodes": [
        {
            "id": "sheets-read",
            "name": "Read Sheet",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4,
            "position": [250, 300],
            "parameters": {
                "operation": "read",
                "sheetName": "Sheet1",
                "options": {}
            },
            "credentials": {
                "googleSheetsOAuth2Api": {
                    "id": "CREDENTIAL_ID_PLACEHOLDER",
                    "name": "Google Sheets account"
                }
            }
        },
        {
            "id": "code-1",
            "name": "Process Rows",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [450, 300],
            "parameters": {
                "jsCode": "// Process each row\\nfor (const item of items) {\\n  item.json.processed = true;\\n}\\nreturn items;"
            }
        },
        {
            "id": "sheets-write",
            "name": "Update Sheet",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4,
            "position": [650, 300],
            "parameters": {
                "operation": "update",
                "sheetName": "Sheet1",
                "options": {}
            },
            "credentials": {
                "googleSheetsOAuth2Api": {
                    "id": "CREDENTIAL_ID_PLACEHOLDER",
                    "name": "Google Sheets account"
                }
            }
        }
    ],
    "connections": {
        "Read Sheet": {
            "main": [[{"node": "Process Rows", "type": "main", "index": 0}]]
        },
        "Process Rows": {
            "main": [[{"node": "Update Sheet", "type": "main", "index": 0}]]
        }
    },
    "active": False
}

# Template selector function
def get_template_for_use_case(description: str) -> dict:
    """
    Select appropriate template based on use case description

    Args:
        description: User's description of what they want to build

    Returns:
        Base template to start from
    """
    description_lower = description.lower()

    # Schedule-based automations
    if any(word in description_lower for word in ["schedule", "daily", "hourly", "cron", "every"]):
        if any(word in description_lower for word in ["email", "send", "notify"]):
            return SCHEDULE_DB_EMAIL_TEMPLATE.copy()
        else:
            return SCHEDULE_HTTP_TEMPLATE.copy()

    # Webhook/API endpoints
    if any(word in description_lower for word in ["webhook", "api endpoint", "receive"]):
        return WEBHOOK_TEMPLATE.copy()

    # Conditional logic
    if any(word in description_lower for word in ["if", "condition", "check", "when"]):
        return CONDITIONAL_TEMPLATE.copy()

    # Spreadsheet automations
    if any(word in description_lower for word in ["google sheets", "spreadsheet", "excel"]):
        return GOOGLE_SHEETS_TEMPLATE.copy()

    # Default: simple schedule + HTTP
    return SCHEDULE_HTTP_TEMPLATE.copy()


# All templates for reference
ALL_TEMPLATES = {
    "schedule_http": SCHEDULE_HTTP_TEMPLATE,
    "webhook": WEBHOOK_TEMPLATE,
    "schedule_db_email": SCHEDULE_DB_EMAIL_TEMPLATE,
    "conditional": CONDITIONAL_TEMPLATE,
    "google_sheets": GOOGLE_SHEETS_TEMPLATE
}
