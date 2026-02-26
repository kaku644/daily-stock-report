import yfinance as yf
import feedparser
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
import pandas as pd

# =============================
# 监控股票
# =============================
STOCKS = {
    "エンプラス": "6961.T",
    "オキサイド": "6521.T",
    "日本電波工業": "6779.T",
    "イビデン": "4062.T",
    "味の素": "2802.T",
    "テクセンドフォトマスク": "429A.T",
    "富士フイルム": "4901.T",
    "TOPPAN": "7911.T",
    "キヤノン": "7751.T",
    "日本電気硝子": "5214.T",
    "AGC": "5201.T",
    "大日本印刷": "7912.T",
    "村田製作所": "6981.T",
    "JX金属": "5713.T",
    "日東紡績": "3110.T",
    "山一電機": "6941.T",
    "アルプスアルパイン": "6770.T",
    "安川電機": "6506.T",
    "三菱重工": "7011.T",
    "IHI": "7013.T",
    "古河電工": "5801.T"
}

# =============================
# 指数
# =============================
INDEXES = {
    "日经225": "^N225",
    "TOPIX": "^TOPX",
    "SOX半导体": "^SOX"
}

KEYWORDS = ["CoWoS", "ASIC", "CPO", "HBM", "玻璃基板"]

EMAIL_SENDER = os.environ["EMAIL_SENDER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]

# =============================
# 获取价格
# =============================
def get_price_info(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="3mo")

    if len(data) < 30:
        return None

    latest = data.iloc[-1]
    prev = data.iloc[-2]

    change = latest["Close"] - prev["Close"]
    pct = (change / prev["Close"]) * 100

    ma5 = data["Close"].rolling(5).mean().iloc[-1]
    ma25 = data["Close"].rolling(25).mean().iloc[-1]

    # RSI计算
    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_latest = rsi.iloc[-1]

    trend = "多头" if ma5 > ma25 else "空头"
    rsi_signal = "超买⚠️" if rsi_latest > 70 else "超卖🔥" if rsi_latest < 30 else "中性"

    return {
        "close": round(latest["Close"], 2),
        "pct": round(pct, 2),
        "trend": trend,
        "rsi": round(rsi_latest, 1),
        "rsi_signal": rsi_signal
    }

# =============================
# 新闻
# =============================
def get_news(company):
    url = f"https://news.google.com/rss/search?q={company}"
    feed = feedparser.parse(url)

    news_output = []
    keyword_hit = []

    for entry in feed.entries[:8]:
        title = entry.title
        news_output.append(f"- {title}")
        for k in KEYWORDS:
            if k.lower() in title.lower():
                keyword_hit.append(f"🔥关键词命中: {k}")

    return news_output, keyword_hit

# =============================
# 生成报告
# =============================
def generate_report():
    today = datetime.now().strftime("%Y-%m-%d")
    report = f"📊 半导体投资监控日报 ({today})\n\n"

    report += "===== 📈 个股 =====\n"
    for name, ticker in STOCKS.items():
        info = get_price_info(ticker)
        if info:
            report += f"\n【{name}】\n"
            report += f"收盘: {info['close']}  涨跌: {info['pct']}%\n"
            report += f"趋势: {info['trend']}  RSI: {info['rsi']} ({info['rsi_signal']})\n"

            news, keywords = get_news(name)
            for n in news:
                report += n + "\n"
            for k in keywords:
                report += k + "\n"

    report += "\n===== 🌏 指数 =====\n"
    for name, ticker in INDEXES.items():
        info = get_price_info(ticker)
        if info:
            report += f"{name}: {info['pct']}%\n"

    return report

# =============================
# 邮件
# =============================
def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = "半导体投资监控日报"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    server.quit()

if __name__ == "__main__":
    report = generate_report()
    send_email(report)
