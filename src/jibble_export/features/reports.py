from jibble_export.client import AuthorizedJibbleClient
from jibble_export.models.responses import TrackedTimeReport
from pprint import pprint

"https://workspace.prod.jibble.io/v1/TimeOffPolicies?$filter=status eq 'Active'"

def get_time_attendance_report():
    client = AuthorizedJibbleClient()
    resp = client.get(
        subdomain="time-attendance",
        relative_path="/v1/TrackedTimeReport",
        params={
            "from": "2026-02-17",
            "to": "2026-02-18",
            "groupBy": "Member",
            "subGroupBy": "Date",
            "$expand": "Subject,Items($expand=Subject)",
        },
        response_model=TrackedTimeReport,
    )
    return resp

if __name__ == "__main__":
    resp = get_time_attendance_report()
    pprint(resp)
