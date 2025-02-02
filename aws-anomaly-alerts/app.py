import boto3
import logging
import json

ses_client = boto3.client("ses", region_name="ap-northeast-2")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_email(html_content):
    sender_email = ""
    recipient_email = [""]
    email_subject = f"[Anomaly Notify] AWS 계정 비용 이상탐지 알람"

    response = ses_client.send_email(
        Source=sender_email,
        Destination={"ToAddresses": recipient_email},
        Message={"Subject": {"Data": email_subject}, "Body": {"Html": {"Data": html_content}}},
    )
    print("Email Sent Response:", response)


def lambda_handler(event, context):
    print(event)
    print(type(event))

    try:
        message = event["Records"][0]["Sns"]["Message"]
        print(message)
        print(type(message))
    except Exception as e:
        print(e)

    try:
        data = json.loads(message)
        print(data)
        print(type(data))
    except Exception as e:
        print(e)

    anomalyStartDate = data["anomalyStartDate"]
    anomalyEndDate = data["anomalyEndDate"]
    dimensionalValue = data["dimensionalValue"]
    totalExpectedSpend = str(data["impact"]["totalExpectedSpend"])
    totalActualSpend = str(data["impact"]["totalActualSpend"])
    totalImpact = str(data["impact"]["totalImpact"])
    totalImpactPercentage = str(data["impact"]["totalImpactPercentage"])

    with open("./template.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    html_content = html_content.replace("{{dimensionalValue}}", dimensionalValue)
    html_content = html_content.replace("{{anomalyStartDate}}", anomalyStartDate)
    html_content = html_content.replace("{{anomalyEndDate}}", anomalyEndDate)
    html_content = html_content.replace("{{totalExpectedSpend}}", totalExpectedSpend)
    html_content = html_content.replace("{{totalActualSpend}}", totalActualSpend)
    html_content = html_content.replace("{{totalImpact}}", totalImpact)
    html_content = html_content.replace("{{totalImpactPercentage}}", totalImpactPercentage)

    tbody_content = ""

    for causes in data["rootCauses"]:
        service = causes["service"]
        region = causes["region"]
        linkedAccount = causes["linkedAccount"]
        linkedAccountName = causes["linkedAccountName"]
        usageType = causes["usageType"]
        impactContribution = round(causes["impactContribution"], 2)
        tbody_content += f"""
            <tr>
                <td>${impactContribution}</td>
                <td>{service}</td>
                <td>{linkedAccountName} ({linkedAccount})</td>
                <td>{region}</td>
                <td>{usageType}</td>
            </tr>
        """
    html_content = html_content.replace("<tbody>", f"<tbody>{tbody_content}")
    send_email(html_content)
