#!/usr/bin/env python3
"""OpenRouter 生图（正确端点版）· 角色一致性优先

关键：图像生成走 POST /api/v1/images，不是 /api/v1/chat/completions。
图像模型也不在 /api/v1/models 里，在 /api/v1/images/models。

用法：
  export OPENROUTER_API_KEY=sk-or-v1-xxx
  python3 gen_openrouter.py out.png "提示词" [--ref 参考图.png] [--seed 12345]

角色一致性做法：
  1. 先生成一张满意的主图，记下它用的 --seed
  2. 之后每张都带 --ref 主图 + 同一个 --seed，只改动作/表情/场景的措辞
  3. input_references 最多 14 张，可以把多角度参考一起传进去
"""
import argparse, base64, json, mimetypes, os, sys, time, urllib.request, urllib.error

API = "https://openrouter.ai/api/v1/images"
MODEL = "bytedance-seed/seedream-5-0-lite"   # 也可 seedream-5-0-pro / seedream-4.5


def data_url(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("prompt")
    ap.add_argument("--ref", action="append", default=[],
                    help="参考图路径，可重复，最多 14 张")
    ap.add_argument("--seed", type=int, help="固定种子，角色一致性靠它")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--aspect", default="3:4", help="立绘用 3:4 或 9:16")
    ap.add_argument("--resolution", default="2K", choices=["2K", "4K"])
    ap.add_argument("--n", type=int, default=1, help="1-4")
    ap.add_argument("--transparent", action="store_true",
                    help="请求透明背景（省掉 rembg 抠图）")
    a = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("请先设置 OPENROUTER_API_KEY", file=sys.stderr)
        return 2

    body = {
        "model": a.model,
        "prompt": a.prompt,
        "aspect_ratio": a.aspect,
        "resolution": a.resolution,
        "n": a.n,
    }
    if a.seed is not None:
        body["seed"] = a.seed
    if a.transparent:
        body["background"] = "transparent"
        body["output_format"] = "png"
    if a.ref:
        body["input_references"] = [
            {"type": "image_url", "image_url": {"url": data_url(p)}} for p in a.ref[:14]
        ]

    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                res = json.load(r)
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:600]
            print(f"[retry {attempt}] HTTP {e.code}: {detail}", file=sys.stderr)
            if attempt == 3:
                return 1
            time.sleep(2 * attempt)
        except Exception as e:
            print(f"[retry {attempt}] {e}", file=sys.stderr)
            if attempt == 3:
                return 1
            time.sleep(2 * attempt)

    items = res.get("data") or []
    if not items:
        print("无图片返回：" + json.dumps(res)[:600], file=sys.stderr)
        return 1

    stem, ext = os.path.splitext(a.out)
    for i, item in enumerate(items):
        path = a.out if len(items) == 1 else f"{stem}_{i+1}{ext or '.png'}"
        with open(path, "wb") as f:
            f.write(base64.b64decode(item["b64_json"]))
        print(f"已保存 {path}  ({item.get('media_type', '?')})")

    u = res.get("usage") or {}
    if "cost" in u:
        print(f"本次花费 ${u['cost']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
