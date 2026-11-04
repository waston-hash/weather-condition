#!/usr/bin/env python3
"""Fetch a three-day Wuhan/Tokyo/London forecast and write JSON + Chinese report."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

ROOT = Path(__file__).resolve().parent
CITIES = {
    "武汉": (30.5928, 114.3055, "Asia/Shanghai"),
    "东京": (35.6762, 139.6503, "Asia/Tokyo"),
    "伦敦": (51.5072, -0.1276, "Europe/London"),
}
DAILY = ["weather_code", "temperature_2m_max", "temperature_2m_min",
         "precipitation_probability_max", "wind_speed_10m_max"]
LABELS = {0:"晴",1:"大致晴朗",2:"局部多云",3:"阴",45:"有雾",48:"雾凇",
          51:"毛毛雨",53:"毛毛雨",55:"毛毛雨",56:"冻毛毛雨",57:"冻毛毛雨",
          61:"小雨",63:"中雨",65:"大雨",66:"冻雨",67:"冻雨",71:"小雪",73:"中雪",75:"大雪",
          77:"雪粒",80:"阵雨",81:"阵雨",82:"强阵雨",85:"阵雪",86:"强阵雪",
          95:"雷暴",96:"雷暴伴冰雹",99:"强雷暴伴冰雹"}

def advice(code, rain, high, wind):
    umbrella = (rain is not None and rain >= 35) or code in range(51, 68) or code in range(80, 83)
    clothes = "厚外套或保暖层" if high < 10 else "外套" if high < 18 else "薄外套" if high < 24 else "轻薄透气衣物"
    commute = "雨天预留通勤时间，注意路滑" if umbrella else "适合常规通勤"
    outdoor = "减少长时间户外活动，留意天气变化" if code >= 95 or wind >= 45 else ("户外活动注意避雨" if umbrella else "适合安排户外活动")
    return {"穿衣": clothes, "带伞": "建议携带" if umbrella else "通常无需，按需备伞",
            "通勤": commute, "户外": outdoor}

def fetch(city, coords, dates):
    lat, lon, tz = coords
    query = urlencode({"latitude":lat,"longitude":lon,"daily":",".join(DAILY),
                       "timezone":tz,"start_date":dates[0],"end_date":dates[-1]})
    req = Request("https://api.open-meteo.com/v1/forecast?"+query,
                  headers={"User-Agent":"weather-daily/1.0","Accept":"application/json"})
    with urlopen(req, timeout=30) as response:
        return json.load(response)

def main():
    now = datetime.now(timezone(timedelta(hours=8)))
    generated = now.isoformat(timespec="seconds")
    dates = [(now.date() + timedelta(days=i)).isoformat() for i in range(1, 4)]
    data = {"generated_at":generated,"source":"Open-Meteo Forecast API (https://open-meteo.com/)","target_dates":dates,"cities":[]}
    lines = ["# 武汉 · 东京 · 伦敦天气日报", f"生成时间：{generated}", f"预报范围：按北京时间运行日的次日起连续三天（{dates[0]} 至 {dates[-1]}）；每日数据按各城市当地日期统计。", "数据来源：Open-Meteo Forecast API（https://open-meteo.com/）。降水概率为每日最高值，风速为每日最大值。"]
    for city, coords in CITIES.items():
        raw = fetch(city, coords, dates)
        d = raw["daily"]
        if d["time"] != dates:
            raise ValueError(f"{city}: forecast dates do not match {dates}")
        for key in DAILY:
            values = d[key]
            if len(values) != 3 or any(v is None for v in values):
                raise ValueError(f"{city}: incomplete {key}")
        for i in range(3):
            if not (0 <= d["precipitation_probability_max"][i] <= 100):
                raise ValueError(f"{city}: invalid precipitation probability")
            if d["temperature_2m_min"][i] > d["temperature_2m_max"][i] or d["wind_speed_10m_max"][i] < 0:
                raise ValueError(f"{city}: invalid temperature or wind")
        entry = {"city":city,"timezone":raw.get("timezone"),"coordinates":{"latitude":coords[0],"longitude":coords[1]},
                 "fetched_at":datetime.now().astimezone().isoformat(timespec="seconds"),"daily":[]}
        lines += ["", f"## {city}"]
        for i in range(3):
            code=d["weather_code"][i]; hi=d["temperature_2m_max"][i]; lo=d["temperature_2m_min"][i]
            rain=d["precipitation_probability_max"][i]; wind=d["wind_speed_10m_max"][i]
            day={"date":d["time"][i],"weather_code":code,"condition":LABELS.get(code,"天气状况代码"+str(code)),
                 "temperature_max_c":hi,"temperature_min_c":lo,"precipitation_probability_max_percent":rain,
                 "wind_speed_max_kmh":wind,"advice":advice(code,rain,hi,wind)}
            entry["daily"].append(day)
            lines.append(f"- {day['date']}：{day['condition']}，{lo}–{hi}°C；降水概率最高 {rain}%；最大风速 {wind} km/h。穿衣：{day['advice']['穿衣']}；{day['advice']['带伞']}；{day['advice']['通勤']}；{day['advice']['户外']}。")
        data["cities"].append(entry)
    data["note"]="各城市 fetched_at 为本次成功抓取时间；预报为模型预测，可能变化。温度和降水数值由 Open-Meteo 返回。"
    (ROOT/"weather.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"weather-report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("Wrote weather.json and weather-report.md")

if __name__ == "__main__":
    main()

