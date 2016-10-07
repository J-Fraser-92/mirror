import json

SERVED_SESSIONS = json.dumps(
    {
        "exit_code": 0,
        "out": [],
        "error": [],
        "today": 8393,
        "yesterday": 7937,
        "last_week": 52860,
        "week_so_far": 43790,
        "quarter": 8393,
        "last_quarter": 521932
    }
)

GRID_IDLE_TIME = json.dumps(
    {
        "nodes": [
            {
                "host": "10.101.10.001",
                "hostname": "SSDVWUK1SEL001",
                "status": "idle",
                "idle_time": "150",
                "busy_time": "0",
                "browser_active": "false"
            }
        ]
    }
)