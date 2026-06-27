#!/usr/bin/python3
# -*- coding:utf-8 -*-
import calendar
import math

OPENAI_CONF = {}
ENABLE_CLAUDE = False
ENABLE_OPENAI = False

draw_icon = None
draw_sparkline = None
get_weather_icon = None
time_until = None
compact_number = None
format_model_label = None
format_window_label = None


def configure(draw_icon_fn, draw_sparkline_fn, get_weather_icon_fn, time_until_fn,
              compact_number_fn, format_model_label_fn, format_window_label_fn,
              openai_conf, enable_claude, enable_openai):
    global draw_icon, draw_sparkline, get_weather_icon, time_until
    global compact_number, format_model_label, format_window_label
    global OPENAI_CONF, ENABLE_CLAUDE, ENABLE_OPENAI

    draw_icon = draw_icon_fn
    draw_sparkline = draw_sparkline_fn
    get_weather_icon = get_weather_icon_fn
    time_until = time_until_fn
    compact_number = compact_number_fn
    format_model_label = format_model_label_fn
    format_window_label = format_window_label_fn
    OPENAI_CONF = openai_conf
    ENABLE_CLAUDE = enable_claude
    ENABLE_OPENAI = enable_openai


def draw_progress_bar(draw, x, y, width, height, percent):
    draw.rectangle((x, y, x + width, y + height), outline=0, width=2)
    fill_w = int((width - 4) * min(max(percent, 0) / 100.0, 1.0))
    if fill_w > 0:
        draw.rectangle((x + 2, y + 2, x + 2 + fill_w, y + height - 2), fill=0)


def draw_strava_widget(draw, fonts, state, x, y):
    strava = state['strava']
    draw_icon(draw, x, y, "icon_strava", (60, 60))
    draw.text((x + 70, y), "STRAVA STATS", font=fonts['28'], fill=0)

    now_y = state['now'].year
    draw.text((x + 70, y + 35),
              f"{now_y}: {strava.get('distance_curr', 0)} km | {now_y - 1}: {strava.get('distance_prev', 0)} km",
              font=fonts['20'], fill=0)
    draw.text((x + 70, y + 60),
              f"Total: {strava.get('total_distance', 0)} km | {strava.get('rides', 0)} acts",
              font=fonts['20'], fill=0)

    draw_icon(draw, x + 70, y + 85, "icon_bike", (30, 30))
    draw.text((x + 105, y + 90), f"{strava.get('bike_total', 0)} km", font=fonts['20'], fill=0)

    draw_icon(draw, x + 220, y + 85, "icon_hike", (30, 30))
    draw.text((x + 255, y + 90), f"{strava.get('hike_total', 0)} km", font=fonts['20'], fill=0)


def draw_sysload_widget(draw, fonts, state, x, y):
    sysload = state['sysload']
    draw_icon(draw, x, y, "icon_cpu", (50, 50))
    draw.text((x + 60, y), f"SYSTEM LOAD: {sysload['cpu']}%", font=fonts['28'], fill=0)
    draw.text((x + 60, y + 35), f"RAM Free: {sysload['ram_free']} MB", font=fonts['20'], fill=0)
    draw_sparkline(draw, x + 60, y + 60, sysload['history'], max_items=30, width=350, height=40, style="bar")


def draw_bambu_widget(draw, fonts, state, x, y):
    printer = state['printer']
    p_status = str(printer.get('status', 'OFFLINE')).upper()
    draw_icon(draw, x, y, "icon_3d", (60, 60))
    draw.text((x + 70, y), f"PRINTER: {p_status}", font=fonts['28'], fill=0)
    if p_status not in ["OFFLINE", "UNKNOWN", "FINISH"]:
        percent = printer.get('percentage', 0)
        draw.rectangle((x + 70, y + 40, x + 400, y + 60), outline=0)
        draw.rectangle((x + 70, y + 40, x + 70 + int(330 * (percent / 100)), y + 60), fill=0)
        draw.text((x + 70, y + 70),
                  f"{percent}% | Rem: {printer.get('remaining_time', '0')}m | {printer.get('layers', '0/0')} L",
                  font=fonts['20'], fill=0)


def draw_crypto_widget(draw, fonts, state, x, y):
    crypto = state['crypto']
    draw_icon(draw, x, y, "icon_btc", (50, 50))
    draw.text((x + 60, y), f"BTC: ${crypto['btc']}", font=fonts['28'], fill=0)
    draw_sparkline(draw, x + 60, y + 35, crypto['btc_hist'], max_items=50, width=350, height=35, style="bar")

    draw_icon(draw, x, y + 80, "icon_eth", (50, 50))
    draw.text((x + 60, y + 80), f"ETH: ${crypto['eth']}", font=fonts['28'], fill=0)
    draw_sparkline(draw, x + 60, y + 115, crypto['eth_hist'], max_items=50, width=350, height=35, style="bar")


def draw_roborock_widget(draw, fonts, state, x, y):
    rob = state['roborock']
    draw_icon(draw, x, y, "icon_roborock", (50, 50))
    draw.text((x + 60, y), f"Bat: {rob['battery']}% | {rob['status']}", font=fonts['28'], fill=0)
    if rob['is_cleaning']:
        draw.text((x + 60, y + 35), f"Clean: {rob['current_area']:.1f} m2 ({rob['pct']:.0f}%)",
                  font=fonts['24'], fill=0)
        draw_progress_bar(draw, x + 60, y + 70, 330, 20, rob['pct'])
    else:
        draw.text((x + 60, y + 35), f"Last: {rob['last_date']} | {rob['ref_area']:.1f} m2", font=fonts['24'], fill=0)


def draw_antigravity_widget(draw, fonts, state, x, y):
    antigravity = state['antigravity']
    draw_icon(draw, x, y, "icon_cpu", (50, 50))
    draw.text((x + 60, y), "ANTIGRAVITY USAGE", font=fonts['28'], fill=0)

    if antigravity.get('error'):
        draw.text((x + 60, y + 35), "Error loading data", font=fonts['20'], fill=0)
        return

    models = antigravity.get('models', [])
    opus = next((m for m in models if m.get('modelId') == 'claude-opus-4-6-thinking'), None)
    gemini = next((m for m in models if m.get('modelId') == 'gemini-3-pro-high'), None)

    y_off = y + 35
    for m_data in (opus, gemini):
        if m_data:
            label = "Opus 4.6" if m_data.get('modelId') == 'claude-opus-4-6-thinking' else "Gemini 3Pro"
            pct = m_data.get('usedPercentage', 0)
            rem_time = time_until(m_data.get('resetDate'))

            draw.text((x + 60, y_off), f"{label} {pct}% | In {rem_time}", font=fonts['20'], fill=0)
            draw_progress_bar(draw, x + 60, y_off + 25, 330, 15, pct)
            y_off += 50


def draw_ping_widget(draw, fonts, state, x, y):
    ping = state['ping']
    draw_icon(draw, x, y, "icon_wifi", (50, 50))
    draw.text((x + 60, y), f"Internet Quality: {ping['current']} ms", font=fonts['28'], fill=0)
    draw_sparkline(draw, x, y + 60, ping['history'], max_items=50, width=400, height=40, style="bar")


def draw_weather_panel(draw, fonts, state, x, col_w):
    weather = state['weather']
    aqi = state['aqi']
    if 'current' not in weather:
        return

    cur = weather['current']
    temp = cur.get('temperature_2m', 0)
    hum = cur.get('relative_humidity_2m', 0)
    pres = cur.get('surface_pressure', 0)
    w_code = cur.get('weather_code', 0)
    wind_dir = cur.get('wind_direction_10m', 0)
    wind_spd = cur.get('wind_speed_10m', 0)
    is_day = cur.get('is_day', 1)
    uv_index = cur.get('uv_index', 0.0)

    temp_rounded = math.floor(temp + 0.5)

    draw_icon(draw, x, 20, get_weather_icon(w_code, is_day), (90, 90))
    draw.text((x + 100, 10), f"{temp_rounded}°C", font=fonts['80'], fill=0)

    uv_x, uv_y = x + 320, 25
    uv_rounded = math.floor(uv_index + 0.5)
    draw.text((uv_x, uv_y), "UV", font=fonts['28'], fill=0)
    uv_val_str = str(uv_rounded)
    try:
        bbox = draw.textbbox((0, 0), uv_val_str, font=fonts['60'])
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = draw.textsize(uv_val_str, font=fonts['60'])

    uv_val_x, uv_val_y = uv_x + 45, 5
    if uv_rounded >= 6:
        pad = 5
        draw.rectangle((uv_val_x - pad, uv_val_y - pad + 10, uv_val_x + tw + pad, uv_val_y + th + pad), fill=0)
        draw.text((uv_val_x, uv_val_y), uv_val_str, font=fonts['60'], fill=255)
    else:
        draw.text((uv_val_x, uv_val_y), uv_val_str, font=fonts['60'], fill=0)

    draw.text((x + 100, 95), f"Humidity: {hum}%", font=fonts['20'], fill=0)
    draw.text((x + 100, 120), f"Press: {pres} hPa", font=fonts['20'], fill=0)

    draw.line((x, 140, x + col_w - 40, 140), fill=0, width=2)

    y_c2 = 160
    draw_icon(draw, x + 5, y_c2, "icon_wind", (30, 30))

    cx, cy, r = x + 80, y_c2 + 80, 60
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=0, width=2)

    for angle in range(0, 360, 45):
        rad_tick = math.radians(angle)
        inner_r = r - 8 if angle % 90 == 0 else r - 4
        tx1, ty1 = cx + inner_r * math.cos(rad_tick), cy + inner_r * math.sin(rad_tick)
        tx2, ty2 = cx + r * math.cos(rad_tick), cy + r * math.sin(rad_tick)
        draw.line((tx1, ty1, tx2, ty2), fill=0, width=2)

    draw.text((cx - 8, cy - r - 22), "N", font=fonts['20'], fill=0)
    draw.text((cx - 8, cy + r + 4), "S", font=fonts['20'], fill=0)
    draw.text((cx + r + 6, cy - 10), "E", font=fonts['20'], fill=0)
    draw.text((cx - r - 24, cy - 10), "W", font=fonts['20'], fill=0)

    rad_arrow = math.radians(wind_dir - 90)
    tip_x = cx + (r - 12) * math.cos(rad_arrow)
    tip_y = cy + (r - 12) * math.sin(rad_arrow)
    base_angle = math.radians(150)
    left_x = cx + 20 * math.cos(rad_arrow + base_angle)
    left_y = cy + 20 * math.sin(rad_arrow + base_angle)
    right_x = cx + 20 * math.cos(rad_arrow - base_angle)
    right_y = cy + 20 * math.sin(rad_arrow - base_angle)
    draw.polygon([(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], fill=0)
    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=0)

    spd_text = f"{wind_spd} km/h"
    try:
        bbox = draw.textbbox((0, 0), spd_text, font=fonts['20'])
        tw = bbox[2] - bbox[0]
    except AttributeError:
        tw = draw.textsize(spd_text, font=fonts['20'])[0]

    draw.text((cx - tw / 2, cy + 25), spd_text, font=fonts['20'], fill=0)

    aqi_x = x + 180
    draw.text((aqi_x, y_c2 + 10), "AIR QUALITY", font=fonts['20'], fill=0)
    draw.text((aqi_x, y_c2 + 55), "AQI:", font=fonts['28'], fill=0)

    aqi_str = str(aqi)
    try:
        bbox = draw.textbbox((0, 0), aqi_str, font=fonts['80'])
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = draw.textsize(aqi_str, font=fonts['80'])

    val_x, val_y = aqi_x + 80, y_c2 + 66

    if aqi >= 50:
        pad = 20
        draw.rectangle((val_x - pad, val_y - pad + 15, val_x + tw + pad, val_y + th + pad - 5), fill=0)
        draw.text((val_x, val_y), aqi_str, font=fonts['80'], fill=255)
    else:
        draw.text((val_x, val_y), aqi_str, font=fonts['80'], fill=0)

    draw.line((x, 320, x + col_w - 40, 320), fill=0, width=2)

    hourly = weather.get('hourly', {})
    times = hourly.get('time', [])
    temps = hourly.get('temperature_2m', [])
    codes = hourly.get('weather_code', [])

    cur_iso = state['now'].strftime("%Y-%m-%dT%H:00")
    try:
        start_idx = times.index(cur_iso) + 1
    except:
        start_idx = 0

    for i in range(4):
        idx = start_idx + i
        if idx < len(times):
            off_x = x + (i * 105)
            draw.text((off_x + 10, 340), f"{times[idx].split('T')[1][:5]}", font=fonts['24'], fill=0)
            draw_icon(draw, off_x + 15, 375, get_weather_icon(codes[idx], 1), (60, 60))
            f_temp = math.floor(temps[idx] + 0.5)
            draw.text((off_x + 15, 440), f"{f_temp}°C", font=fonts['24'], fill=0)


def draw_time_header(draw, fonts, state, x):
    dt = state['now']
    draw.text((x, 10), dt.strftime("%H:%M"), font=fonts['clock'], fill=0)
    draw.text((x, 170), dt.strftime("%d %B %Y"), font=fonts['32'], fill=0)
    draw.text((x + 340, 170), dt.strftime("%a").upper(), font=fonts['32'], fill=0)


def draw_ai_usage_widget(draw, fonts, state, x, y):
    claude = state['claude']
    openai = state['openai']

    if ENABLE_CLAUDE and ENABLE_OPENAI:
        draw.text((x, y), "AI PROVIDER USAGE", font=fonts['28'], fill=0)

        if claude.get('error'):
            draw.text((x, y + 35), "Claude: Usage unavailable", font=fonts['20'], fill=0)
            draw.text((x, y + 58), "Check claude_creds.json / usage.json", font=fonts['20'], fill=0)
        else:
            pct_5h = claude.get('five_hour', {}).get('utilization', 0)
            pct_7d = claude.get('seven_day', {}).get('utilization', 0)
            rem_5h = time_until(claude.get('five_hour', {}).get('resets_at'))
            rem_7d = time_until(claude.get('seven_day', {}).get('resets_at'))
            draw.text((x, y + 35), f"Claude 5h {pct_5h}% | 7d {pct_7d}%", font=fonts['20'], fill=0)
            draw.text((x, y + 58), f"Resets {rem_5h} / {rem_7d}", font=fonts['20'], fill=0)

        openai_label = openai.get('label', OPENAI_CONF.get('LABEL', 'OPENAI / CODEX'))
        if openai.get('error'):
            draw.text((x, y + 86), f"{openai_label}: Usage unavailable", font=fonts['20'], fill=0)
            draw.text((x, y + 109), "Check openai_creds.json / openai_usage.json", font=fonts['20'], fill=0)
        else:
            if openai.get('mode') == 'codex_chatgpt':
                primary = openai.get('primary_window', {})
                secondary = openai.get('secondary_window', {})
                draw.text((x, y + 86),
                          f"Codex {primary.get('used_percent', 0)}% | {secondary.get('used_percent', 0)}%",
                          font=fonts['20'], fill=0)
                plan = str(openai.get('plan_type', 'unknown')).upper()
                draw.text((x, y + 109), f"Plan {plan} | Credits {openai.get('credits', {}).get('available_count', 0)}",
                          font=fonts['20'], fill=0)
            elif openai.get('mode') == 'codex_api_key':
                draw.text((x, y + 86), "Codex API key mode active", font=fonts['20'], fill=0)
                draw.text((x, y + 109), "Add admin key or ChatGPT sign-in for usage", font=fonts['20'], fill=0)
            else:
                openai_day = openai.get('window_24h', {})
                top_model = next(iter(openai.get('models', [])), {})
                total_tokens = openai_day.get('input_tokens', 0) + openai_day.get('output_tokens', 0)
                draw.text((x, y + 86),
                          f"{openai_label} 24h {openai_day.get('requests', 0)} req | {compact_number(total_tokens)} tok",
                          font=fonts['20'], fill=0)
                top_label = format_model_label(top_model.get('model'))
                draw.text((x, y + 109), f"Top model: {top_label} {top_model.get('requests_7d', 0)} req / 7d",
                          font=fonts['20'], fill=0)
        return

    if ENABLE_CLAUDE:
        draw.text((x, y), "CLAUDE AI USAGE", font=fonts['28'], fill=0)

        if claude.get('error'):
            draw.text((x, y + 50), "Claude Usage Error", font=fonts['24'], fill=0)
        else:
            pct_5h = claude.get('five_hour', {}).get('utilization', 0)
            rem_5h = time_until(claude.get('five_hour', {}).get('resets_at'))
            draw.text((x, y + 40), f"5-Hour Limit: {pct_5h}% (Resets in {rem_5h})", font=fonts['20'], fill=0)
            draw_progress_bar(draw, x, y + 65, 400, 15, pct_5h)

            pct_7d = claude.get('seven_day', {}).get('utilization', 0)
            rem_7d = time_until(claude.get('seven_day', {}).get('resets_at'))
            draw.text((x, y + 90), f"7-Day Limit: {pct_7d}% (Resets in {rem_7d})", font=fonts['20'], fill=0)
            draw_progress_bar(draw, x, y + 115, 400, 15, pct_7d)
        return

    openai_label = openai.get('label', OPENAI_CONF.get('LABEL', 'OPENAI / CODEX'))
    draw.text((x, y), openai_label, font=fonts['28'], fill=0)

    if openai.get('error'):
        draw.text((x, y + 50), "OpenAI / Codex Usage Error", font=fonts['24'], fill=0)
    elif openai.get('mode') == 'codex_chatgpt':
        primary = openai.get('primary_window', {})
        secondary = openai.get('secondary_window', {})

        draw.text((x, y + 35), f"Plan: {str(openai.get('plan_type', 'unknown')).upper()}",
                  font=fonts['20'], fill=0)

        primary_label = format_window_label(primary.get('limit_window_seconds'))
        primary_pct = primary.get('used_percent', 0)
        draw.text((x, y + 58), f"{primary_label}: {primary_pct}% (Resets in {time_until(primary.get('reset_at'))})",
                  font=fonts['20'], fill=0)
        draw_progress_bar(draw, x, y + 82, 400, 15, primary_pct)

        secondary_label = format_window_label(secondary.get('limit_window_seconds'))
        secondary_pct = secondary.get('used_percent', 0)
        draw.text((x, y + 100),
                  f"{secondary_label}: {secondary_pct}% (Resets in {time_until(secondary.get('reset_at'))})",
                  font=fonts['20'], fill=0)
        draw_progress_bar(draw, x, y + 124, 400, 15, secondary_pct)
    elif openai.get('mode') == 'codex_api_key':
        draw.text((x, y + 35), "Codex is using API key mode.", font=fonts['20'], fill=0)
        draw.text((x, y + 60), "Plan/rate-limit data is only", font=fonts['20'], fill=0)
        draw.text((x, y + 85), "available with ChatGPT sign-in", font=fonts['20'], fill=0)
        draw.text((x, y + 108), "or an OpenAI Admin API key.", font=fonts['20'], fill=0)
    else:
        usage_24h = openai.get('window_24h', {})
        usage_7d = openai.get('window_7d', {})
        models = openai.get('models', [])

        total_24h_tokens = usage_24h.get('input_tokens', 0) + usage_24h.get('output_tokens', 0)
        total_7d_tokens = usage_7d.get('input_tokens', 0) + usage_7d.get('output_tokens', 0)

        draw.text((x, y + 35),
                  f"24h: {usage_24h.get('requests', 0)} req | {compact_number(total_24h_tokens)} tok",
                  font=fonts['20'], fill=0)
        draw.text((x, y + 60),
                  f"7d: {usage_7d.get('requests', 0)} req | {compact_number(total_7d_tokens)} tok",
                  font=fonts['20'], fill=0)

        for idx, m_data in enumerate(models[:2]):
            label = format_model_label(m_data.get('model'))
            y_off = y + 85 + (idx * 23)
            draw.text((x, y_off), f"{label}: {m_data.get('requests_7d', 0)} req / 7d", font=fonts['20'], fill=0)


def draw_spotify_widget(Himage, draw, fonts, state, x, y):
    spotify = state['spotify']
    if spotify['cover']:
        Himage.paste(spotify['cover'], (x, y))
    else:
        draw_icon(draw, x, y, "icon_spotify", (120, 120))

    status_ico = "icon_play" if spotify['status'] == 'PLAYING' else "icon_pause"
    draw_icon(draw, x + 140, y + 10, status_ico, (30, 30))

    if spotify['status'] == 'PLAYING':
        words = spotify['text'].split(' - ')
        artist = words[0] if len(words) > 0 else "Unknown"
        track = words[1] if len(words) > 1 else ""
        draw.text((x + 180, y + 10), artist[:20], font=fonts['28'], fill=0)
        draw.text((x + 140, y + 50), track[:25], font=fonts['24'], fill=0)


def draw_time_progress_widget(draw, fonts, state, x, y):
    dt = state['now']
    draw.text((x, y), "TIME PROGRESS", font=fonts['28'], fill=0)

    day_pct = (dt.hour * 3600 + dt.minute * 60 + dt.second) / 86400.0
    days_in_m = calendar.monthrange(dt.year, dt.month)[1]
    month_pct = (dt.day - 1 + (dt.hour / 24.0)) / days_in_m
    days_in_y = 366 if calendar.isleap(dt.year) else 365
    year_pct = (dt.timetuple().tm_yday - 1 + (dt.hour / 24.0)) / days_in_y

    def draw_prog(y_offset, label, pct):
        draw.text((x, y + y_offset), label, font=fonts['24'], fill=0)
        bx = x + 110
        bw = 200
        bh = 20
        draw.rectangle((bx, y + y_offset + 2, bx + bw, y + y_offset + bh + 2), outline=0, width=2)
        if pct > 0:
            fill_w = int((bw - 4) * min(pct, 1.0))
            if fill_w > 0:
                draw.rectangle((bx + 2, y + y_offset + 4, bx + 2 + fill_w, y + y_offset + bh), fill=0)
        draw.text((bx + bw + 15, y + y_offset), f"{int(pct * 100)}%", font=fonts['24'], fill=0)

    draw_prog(40, "DAY", day_pct)
    draw_prog(75, "MONTH", month_pct)
    draw_prog(110, "YEAR", year_pct)


def draw_gmail_widget(draw, fonts, state, x, y):
    draw_icon(draw, x, y, "icon_mail", (60, 60))
    draw.text((x + 80, y + 10), f"Unread Inbox: {state['gmail_unread']}", font=fonts['35'], fill=0)


def draw_slot(widget_id, Himage, draw, fonts, state, x, y, clear_rect=None):
    if clear_rect:
        draw.rectangle(clear_rect, fill=255)

    if widget_id == 'strava':
        draw_strava_widget(draw, fonts, state, x, y)
    elif widget_id == 'sysload':
        draw_sysload_widget(draw, fonts, state, x, y)
    elif widget_id == 'bambu':
        draw_bambu_widget(draw, fonts, state, x, y)
    elif widget_id == 'crypto':
        draw_crypto_widget(draw, fonts, state, x, y)
    elif widget_id == 'roborock':
        draw_roborock_widget(draw, fonts, state, x, y)
    elif widget_id == 'antigravity':
        draw_antigravity_widget(draw, fonts, state, x, y)
    elif widget_id == 'ping':
        draw_ping_widget(draw, fonts, state, x, y)
    elif widget_id == 'ai_usage':
        draw_ai_usage_widget(draw, fonts, state, x, y)
    elif widget_id == 'spotify':
        draw_spotify_widget(Himage, draw, fonts, state, x, y)
    elif widget_id == 'time_progress':
        draw_time_progress_widget(draw, fonts, state, x, y)


