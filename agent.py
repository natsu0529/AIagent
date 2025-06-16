import datetime
import schedule
import time
from typing import Dict
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class ProfessorNotificationAgent:
    def __init__(self):
        self.school_coordinates = {
            "lat": 35.6699,  # 東京海洋大学越中島キャンパス
            "lon": 139.7951
        }
        self.professor_email = "kubo@logopt.com"
        self.student_id = "2323025"
        self.student_name = "鈴木夏大"
        
        # Gmail設定（環境変数から取得）
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD')

    def get_location_status(self) -> Dict:
        """
        現在の位置情報を取得し、学校にいるか判定
        """
        try:
            print("DEBUG: 位置情報をチェックしています...")
            
            # IP-based location API使用
            response = requests.get('http://ip-api.com/json/', timeout=10)
            data = response.json()
            
            if data['status'] == 'success':
                user_lat = data['lat']
                user_lon = data['lon']
                
                # 距離計算（簡易版）
                lat_diff = abs(self.school_coordinates['lat'] - user_lat)
                lon_diff = abs(self.school_coordinates['lon'] - user_lon)
                distance = (lat_diff**2 + lon_diff**2)**0.5
                
                # 0.01度以内（約1km）を学校内と判定
                at_school = distance < 0.01
                
                location_desc = f"{data.get('city', '不明')}, {data.get('country', '不明')}"
                
                return {
                    "status": "success",
                    "at_school": at_school,
                    "location_description": location_desc,
                    "coordinates": {"lat": user_lat, "lon": user_lon},
                    "distance_from_school": distance
                }
            else:
                raise Exception("位置情報取得失敗")
                
        except Exception as e:
            print(f"ERROR: 位置情報取得エラー: {e}")
            # エラー時は学校外として扱う
            return {
                "status": "error", 
                "at_school": False, 
                "location_description": "位置情報取得失敗（学校外として処理）",
                "error": str(e)
            }

    def send_professor_email(self, professor_email_address: str, subject: str, body: str) -> Dict:
        """
        Gmail経由で教授にメール送信
        """
        try:
            print(f"DEBUG: {professor_email_address} 教授にメールを送信しています...")
            print(f"DEBUG: 件名: {subject}")
            print(f"DEBUG: 本文: {body}")
            
            # Gmail認証情報の確認
            if not self.gmail_user or not self.gmail_password:
                return {
                    "status": "error",
                    "message": "Gmail認証情報が設定されていません (.envファイルを確認してください)"
                }
            
            # メール作成
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = professor_email_address
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Gmail SMTP経由で送信
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            
            return {
                "status": "success",
                "message": f"{professor_email_address} 教授にメールを送信しました。"
            }
            
        except Exception as e:
            print(f"ERROR: メール送信エラー: {e}")
            return {
                "status": "error",
                "message": f"メール送信失敗: {str(e)}"
            }

    def check_monday_1pm(self) -> bool:
        """
        現在が月曜日13時かチェック
        """
        now = datetime.datetime.now()
        is_monday = now.weekday() == 0  # 月曜日 = 0
        is_1pm = now.hour == 13
        return is_monday and is_1pm

    def run_notification_check(self):
        """
        メイン処理：条件チェックしてメール送信判定
        """
        print(f"\n=== 通知チェック実行 {datetime.datetime.now()} ===")
        
        # 1. 時刻・曜日チェック
        if not self.check_monday_1pm():
            current_time = datetime.datetime.now()
            print(f"現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S (%A)')}")
            print("月曜日13時ではないため、メール送信をスキップします。")
            return
        
        print("✓ 月曜日13時です。位置情報をチェックします。")
        
        # 2. 位置情報チェック
        location_result = self.get_location_status()
        
        if location_result["status"] == "error":
            print(f"⚠ 位置情報取得エラー: {location_result.get('error')}")
        
        print(f"現在地: {location_result['location_description']}")
        print(f"学校内判定: {'はい' if location_result['at_school'] else 'いいえ'}")
        
        # 3. メール送信判定
        if location_result["at_school"]:
            print("✓ 学校内にいるため、メール送信は不要です。")
            return
        
        print("! 学校外にいます。教授にメールを送信します。")
        
        # 4. メール送信
        subject = "本日の授業について"
        body = f"久保先生、{self.student_id}の{self.student_name}です。本日の授業は体調不良のため欠席させていただきます。"
        
        email_result = self.send_professor_email(self.professor_email, subject, body)
        
        if email_result["status"] == "success":
            print(f"✓ {email_result['message']}")
        else:
            print(f"✗ {email_result['message']}")

    def start_scheduler(self):
        """
        スケジューラー開始（毎週月曜13:00に実行）
        """
        print("=== 教授通知エージェント開始 ===")
        print("毎週月曜日13:00に自動実行します...")
        print("手動テスト実行: python -c 'from professor_notification_agent import ProfessorNotificationAgent; agent = ProfessorNotificationAgent(); agent.run_notification_check()'")
        
        # 毎週月曜13:00にスケジュール
        schedule.every().monday.at("13:00").do(self.run_notification_check)
        
        # テスト用: 毎分実行（デバッグ用）
        # schedule.every().minute.do(self.run_notification_check)
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分間隔でチェック

# 直接実行時の処理
if __name__ == "__main__":
    agent = ProfessorNotificationAgent()
    
    # テスト実行か常駐実行かを選択
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("=== テスト実行モード ===")
        agent.run_notification_check()
    else:
        print("=== 常駐実行モード ===")
        agent.start_scheduler()