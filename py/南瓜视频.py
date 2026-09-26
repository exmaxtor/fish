#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南瓜影院 · TVBox 爬虫（探嗅版）
境界：轮海秘境 · 彼岸境（探嗅模式）
"""
import sys
import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup

sys.path.append("..")
from base.spider import Spider


class Spider(Spider):
    def __init__(self):
        self.siteUrl = "https://74214.tv333.homes"
        # 备用域名，以防主站失效
        self.fallbackUrl = "https://74214.kk881.xyz"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.siteUrl,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        self.session = requests.Session()
        self.class_cache = None

    def init(self, extend=""):
        return True

    # ═════════ 硬编码分类（完整列表请自行补全，此处仅示例） ═════════
    def _builtin_classes(self):
        # 请将之前的完整分类列表复制到这里，为节省篇幅此处只留3个示例
        return [
            {"type_id": "6ab222795552b5f2a80d08e054eb6eb2", "type_name": "主播网红"},
            {"type_id": "05e63492cd2898bd6fa1c7cf36d5cd8a", "type_name": "国产厂牌"},
            {"type_id": "efc9a244d59a9d510b84644f2fa79b88", "type_name": "日本无码"},
        ]

    # ═════════ 临字秘 · 分类 ═════════
    def homeContent(self, filter):
        if self.class_cache:
            return {"class": self.class_cache}
        try:
            url = self.siteUrl + "/more/"
            resp = self.session.get(url, headers=self.headers, timeout=10)
            resp.encoding = "utf-8"
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")
            panel = soup.select_one(".panel-body")
            if panel:
                classes = []
                for a in panel.find_all("a", class_="btn"):
                    href = a.get("href")
                    if href and href.startswith("/type/"):
                        tid = href.replace("/type/", "").replace(".html", "")
                        name = a.get_text(strip=True)
                        if tid and name:
                            classes.append({"type_id": tid, "type_name": name})
                if classes:
                    self.class_cache = classes
                    return {"class": classes}
        except Exception as e:
            print("[南瓜] 动态分类失败:", e)
        self.class_cache = self._builtin_classes()
        return {"class": self.class_cache}

    # ═════════ 斗字秘 · 列表 ═════════
    def categoryContent(self, tid, pg, filter, extend):
        if pg == "1":
            url = f"{self.siteUrl}/type/{tid}.html"
        else:
            url = f"{self.siteUrl}/type/{tid}.html?page={pg}"
        try:
            resp = self.session.get(url, headers=self.headers, timeout=15)
            resp.encoding = "utf-8"
            html = resp.text
        except Exception as e:
            print("[南瓜] 列表请求失败:", e)
            return {"list": [], "page": pg, "pagecount": 999}

        videos = []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("a.card")
        for card in cards:
            try:
                href = card.get("href", "")
                if not href or not href.startswith("/video/"):
                    continue
                vid = href.replace("/video/", "").replace(".html", "")
                heading = card.select_one(".card-heading strong")
                title = heading.get_text(strip=True) if heading else ""
                img = card.select_one("img.lazy")
                pic = img.get("data-original") or img.get("src") if img else ""
                if pic and not pic.startswith("http"):
                    pic = urllib.parse.urljoin(self.siteUrl, pic)
                remark = ""
                content_div = card.select_one(".card-content")
                if content_div:
                    pull_right = content_div.select_one(".pull-right")
                    if pull_right:
                        remark = pull_right.get_text(strip=True)
                if "AD" in title or "AD" in remark:
                    continue
                videos.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
            except Exception:
                continue

        pagecount = 999
        try:
            pager = soup.select_one("ul.pager")
            if pager:
                total = int(pager.get("data-rec-total", 0))
                per_page = int(pager.get("data-rec-per-page", 55))
                if total > 0 and per_page > 0:
                    pagecount = (total + per_page - 1) // per_page
        except:
            pass
        if pagecount == 999:
            try:
                nums = re.findall(r'<a[^>]*>\s*(\d+)\s*</a>', html)
                if nums:
                    pagecount = max(int(x) for x in nums)
            except:
                pass
        return {"list": videos, "page": int(pg), "pagecount": pagecount}

    # ═════════ 者字秘 · 详情（探嗅模式） ═════════
    def detailContent(self, ids):
        vid = ids[0]
        # 构建详情页完整 URL
        url = self.siteUrl + "/video/" + vid + ".html"

        # 尝试获取页面标题（可选）
        title = "南瓜视频"
        try:
            resp = self.session.get(url, headers=self.headers, timeout=10)
            resp.encoding = "utf-8"
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)
            else:
                m = re.search(r'<title>([^<]+)</title>', html)
                if m:
                    title = m.group(1).split("_")[0].split("-")[0].strip()
        except:
            pass

        # ── 策略1：直接返回详情页 URL，让 TVBox 探嗅 ──
        # 如果 TVBox 支持 parse:1，它会尝试加载该页面并自动提取视频
        # 注意：有些 TVBox 版本可能不支持，但大多数现代版本都支持
        return {
            "list": [{
                "vod_id": vid,
                "vod_name": title,
                "vod_play_from": "南瓜(探嗅)",
                "vod_play_url": url
            }],
            "parse": 1  # 关键：告诉 TVBox 需要二次解析
        }

        # ── 策略2（备选）：如果页面中有 iframe 或 m3u8，优先返回（可提高成功率） ──
        # 下面代码默认注释，如果希望优先使用 iframe 或直链，可取消注释并调整
        """
        # 尝试提取 iframe
        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
        if iframe_match:
            iframe_src = iframe_match.group(1)
            if iframe_src.startswith("//"):
                iframe_src = "https:" + iframe_src
            elif not iframe_src.startswith("http"):
                iframe_src = urllib.parse.urljoin(self.siteUrl, iframe_src)
            return {
                "list": [{
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_play_from": "南瓜(iframe)",
                    "vod_play_url": iframe_src
                }],
                "parse": 1
            }
        # 尝试提取 m3u8 直链
        m = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
        if m:
            return {
                "list": [{
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_play_from": "南瓜(m3u8)",
                    "vod_play_url": m.group(1)
                }]
            }
        # 否则，返回详情页 URL 探嗅
        return {
            "list": [{
                "vod_id": vid,
                "vod_name": title,
                "vod_play_from": "南瓜(探嗅)",
                "vod_play_url": url
            }],
            "parse": 1
        }
        """

    # ═════════ 兵字秘 · 播放 ═════════
    def playerContent(self, flag, id, vipFlags):
        # 如果传入的是网页地址，让 TVBox 再次解析
        if id.startswith("http") and not self.isVideoFormat(id):
            return {
                "parse": 1,
                "url": id,
                "header": json.dumps({
                    "User-Agent": self.headers["User-Agent"],
                    "Referer": self.siteUrl
                })
            }
        # 如果已经是视频地址，直接播放
        return {
            "parse": 0,
            "url": id,
            "header": json.dumps({
                "User-Agent": self.headers["User-Agent"],
                "Referer": self.siteUrl
            })
        }

    # ═════════ 搜索 ═════════
    def searchContent(self, key, quick, pg="1"):
        search_url = f"{self.siteUrl}/search/?wd={urllib.parse.quote(key)}"
        if pg != "1":
            search_url += f"&page={pg}"
        try:
            resp = self.session.get(search_url, headers=self.headers, timeout=15)
            resp.encoding = "utf-8"
            html = resp.text
        except Exception:
            return {"list": []}
        videos = []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("a.card")
        for card in cards:
            try:
                href = card.get("href", "")
                if not href or not href.startswith("/video/"):
                    continue
                vid = href.replace("/video/", "").replace(".html", "")
                heading = card.select_one(".card-heading strong")
                title = heading.get_text(strip=True) if heading else ""
                img = card.select_one("img.lazy")
                pic = img.get("data-original") or img.get("src") if img else ""
                if pic and not pic.startswith("http"):
                    pic = urllib.parse.urljoin(self.siteUrl, pic)
                videos.append({"vod_id": vid, "vod_name": title, "vod_pic": pic, "vod_remarks": "搜索"})
            except:
                continue
        return {"list": videos}

    def isVideoFormat(self, url):
        return any(url.lower().endswith(ext) for ext in [".m3u8", ".mp4", ".flv", ".mkv"])

    def manualVideoCheck(self):
        return False