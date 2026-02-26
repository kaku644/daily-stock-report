import yfinance as yf
import feedparser
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

STOCKS = {
    "エンプラス": "6961.T",
    "オキサイド": "6521.T",
    "日本電波工業": "6779.T"
}

EMAIL_SENDER = os.environ["EMAIL_SENDER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]

def get_stock_info(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="2d")
    if len(data) < 2:
        return None

    yesterday = data.iloc[-1]
    prev = data.iloc[-2]

    change = yesterday["Close"] - prev["Close"]
    pct = (change / prev["Close"]) * 100

    return {
        "close": round(yesterday["Close"], 2),
        "change": round(change, 2),
        "pct": round(pct, 2),
        "volume": int(yesterday["Volume"])
    }

def get_news(company_name):
    url = f"https://news.google.com/rss/search?q={company_name}"
    feed = feedparser.parse(url)
    news_list = []
    for entry in feed.entries[:5]:
        news_list.append(f"- {entry.title}")
    return news_list

def generate_report():
    today = datetime.now().strftime("%Y-%m-%d")
    report = f"📊 每日股票监控报告 ({today})\n\n"

    for name, ticker in STOCKS.items():
        info = get_stock_info(ticker)
        if info:
            report += f"【{name}】\n"
            report += f"收盘价: {info['close']}\n"
            report += f"涨跌: {info['change']} ({info['pct']}%)\n"
            report += f"成交量: {info['volume']}\n"

            news = get_news(name)
            report += "相关新闻:\n"
            for n in news:
                report += n + "\n"

            report += "\n----------------------\n\n"

    return report

def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = "每日股票监控报告"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    server.quit()

if __name__ == "__main__":
    report = generate_report()
    send_email(report)
