from google.adk.agents import Agent
import datetime

# --- カスタムツール1: 位置情報をチェック ---
def get_location_status() -> dict:
    """
    現在の位置情報を取得し、学校（〒135-0044 東京都江東区越中島２丁目１−６）にいるか判定。
    判定基準：この住所の範囲にいる時 at_school=True。それ以外は at_school=False。
    """
    print("DEBUG: 位置情報をチェックしています...")
    # 実際はAPI等で判定。ここでは常に「学校外」返す例。
    return {"status": "success", "at_school": False, "location_description": "自宅（学校外）"}

# --- カスタムツール2: 教授にメールを送信 ---
def send_professor_email(professor_email_address: str, subject: str, body: str) -> dict:
    """
    Gmail経由で指定教授へメール送信。
    Args:
        professor_email_address (str): 例: kubo@logopt.com
        subject (str): 本日の授業について
        body (str): 久保先生、2323025の鈴木夏大です。本日の授業は体調不良のため欠席させていただきます。
    """
    print(f"DEBUG: {professor_email_address} 教授にメールを送信しています...")
    print(f"DEBUG: 件名: {subject}")
    print(f"DEBUG: 本文: {body}")
    # Gmail送信ロジック（コメント参照）
    return {"status": "success", "message": f"{professor_email_address} 教授にメールを送信しました。"}

# --- ルートエージェント定義 ---
root_agent = Agent(
    name="professor_notification_agent",
    model="gemini-2.0-flash",
    description="月曜13時に学校にいない場合のみ教授へ自動メールを送信するエージェント。",
    instruction="""
    あなたは、ユーザーからの指示を受け、毎週月曜日の午後1時（13:00）に現在位置情報を確認し、
    学校（〒135-0044 東京都江東区越中島２丁目１−６）にいない場合のみ、教授へ自動メールを送信するアシスタントです。

    タスク:
    1. 現在の曜日と時刻を取得し、「月曜13時」である場合のみ次の処理に進んでください。
    2. get_location_statusツールで現在地が学校内か判定。
    3. 学校外の場合のみ、kubo@logopt.com へ以下の内容でGmail送信してください。
       - 件名: 本日の授業について
       - 本文: 久保先生、2323025の鈴木夏大です。本日の授業は体調不良のため欠席させていただきます。
       - 送信には send_professor_email ツールを使うこと。
    4. それ以外の曜日・時刻、または学校内の場合はメール送信不要。その旨をユーザーに伝えてください。
    5. 回答は簡潔にまとめてください。
    """,
    tools=[
        get_location_status,
        send_professor_email
    ],
)