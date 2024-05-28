import re
import boto3
from datetime import datetime
import pytz
from urllib.request import Request, urlopen
import json
import logging

slack_webhook_url = "slack_url"
ses_client = boto3.client("ses", region_name="ap-northeast-2")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# UTC → KST 변환 함수
def time_convert(aws_time):
    utc_time = datetime.strptime(aws_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=pytz.utc
    )
    kst = pytz.timezone("Asia/Seoul")
    kst_time = utc_time.astimezone(kst)
    return kst_time.strftime("%Y년 %m월 %d일 %H시 %M분")

# 메인 람다 함수(이벤트 로그 파싱 후 슬랙에 전달)
def Message(event, context):
    result = event["Records"]
    logger.info("Event: " + str(event))
    logger.info("Message " + str(result))
    
    if "alert threshold" in str(result[0]["Sns"]["Subject"]):
    # 계정, 시간
        account_id = (re.split(":", result[0]["EventSubscriptionArn"]))[4]
        time = time_convert(result[0]["Sns"]["Timestamp"])
        
    # 슬랙으로 전송할 비용 관련 항목 추출하여 변수에 저장
    budgeted_amount = re.search(r"Budgeted Amount: (\$[\d,]+\.\d{2})", result[0]["Sns"]["Message"])
    alert_threshold = re.search(r"Alert Threshold: > (\$[\d,]+\.\d{2})", result[0]["Sns"]["Message"]    )
    actual_amount = re.search(r"ACTUAL Amount: (\$[\d,]+\.\d{2})", result[0]["Sns"]["Message"])

    if budgeted_amount and alert_threshold and actual_amount :
        budgeted_amount = budgeted_amount.group(1)
        alert_threshold = alert_threshold.group(1)
        actual_amount = actual_amount.group(1)

    slack_message = {
        "text": (
            "*%s 계정 Budget 알림*\n\n"
            ">>>*발생 날짜 :* %s\n"
            "*예산 금액 :* %s\n"
            "*임계 금액 :* %s\n"
            "*실제 금액 :* %s\n\n"
            "%s"
        ) % (
            account_id,
            time,
            budgeted_amount,
            alert_threshold,
            actual_amount,
            f"설정한 예산을 초과하는 비용이 발생했습니다. 특이사항이 발생했는지 확인이 필요합니다.\nhttp://us-east-1.console.aws.amazon.com/costmanagement/home?region=ap-northeast-2#/cost-explorer"
        )
    }
    req = Request(slack_webhook_url, json.dumps(slack_message).encode("utf-8"))
    response = urlopen(req)
    response.read()