# 每日天气日报

GitHub Actions 每天北京时间 21:00（UTC 13:00）抓取武汉、东京、伦敦从次日起三天的 Open-Meteo 天气预报，生成中文建议及机器可读 JSON。也可在 Actions 页面手动运行工作流。

结果：[`weather.json`](weather.json) · [`weather-report.md`](weather-report.md)

数据来源：Open-Meteo Forecast API。仓库和日报数据为公开内容。ChatGPT 自动化不会因此自动读取这些文件；外部 URL 读取能力需在现有自动化中另行验证。