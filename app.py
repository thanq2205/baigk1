"""
ESCAPE – Trò chơi giải đố kinh dị 5 cửa, góc nhìn thứ nhất (lấy cảm hứng từ Doors trong Roblox)
Chạy:  streamlit run app.py
Đặt file nhạc "doors-roblox-ost-elevator-jam-made-with-Voicemod.mp3" cùng thư mục với app.py.
Game 3D chạy bằng Three.js, nhúng vào Streamlit qua components.html.
"""
import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ESCAPE", layout="wide")


# ---------------------------------------------------------------------------
# DỮ LIỆU CÂU ĐỐ TRẮC NGHIỆM (sửa tại đây)
# Mỗi cửa có 3 câu. Chọn đúng -> nhận 1 chữ số. Ghép theo "order" để ra mật mã.
#   q: câu hỏi | a: đáp án ĐÚNG | w: 3 đáp án SAI | digit: chữ số | hint: gợi ý
# Vị trí A/B/C/D được xáo ngẫu nhiên mỗi lần mở câu hỏi.
# ---------------------------------------------------------------------------
DOORS = [
    {
        "name": "Sảnh đón tiếp",
        "intro": "Ánh đèn chập chờn. Hãy tìm 3 manh mối trong phòng.",
        "order": [0, 1, 2],
        "order_text": "Ghép chìa 1 → chìa 2 → chìa 3.",
        "questions": [
            {"q": "Cái gì càng lấy đi càng lớn?",
             "a": "Cái hố", "w": ["Cái bóng", "Cái cây", "Tuổi tác"],
             "digit": 4, "hint": "Bạn thường thấy nó khi đào đất."},
            {"q": "Có 3 quả táo, bạn lấy đi 2 quả. Vậy bạn đang có mấy quả táo?",
             "a": "2 quả", "w": ["1 quả", "3 quả", "5 quả"],
             "digit": 7, "hint": "Hỏi 'bạn có' chứ không hỏi 'còn lại'."},
            {"q": "Cái gì có chìa nhưng không mở được ổ khóa nào?",
             "a": "Đàn piano", "w": ["Cái tủ", "Con dao", "Quyển sách"],
             "digit": 1, "hint": "Nhạc cụ có phím đen phím trắng."},
        ],
    },
    {
        "name": "Thư viện bỏ hoang",
        "intro": "Bụi phủ kín mọi thứ. Có tiếng thì thầm: 'Hãy suy nghĩ...'",
        "order": [2, 1, 0],
        "order_text": "Ghép NGƯỢC: chìa 3 → chìa 2 → chìa 1.",
        "questions": [
            {"q": "Điền số tiếp theo: 2, 6, 12, 20, 30, ?",
             "a": "42", "w": ["36", "40", "44"],
             "digit": 3, "hint": "Hiệu giữa các số liên tiếp: 4, 6, 8, 10..."},
            {"q": "Có một từ trong từ điển luôn được 'viết sai'. Từ đó là gì?",
             "a": "Sai", "w": ["Đúng", "Chính tả", "Từ điển"],
             "digit": 8, "hint": "Chính câu hỏi đã chứa đáp án."},
            {"q": "Giải mã (mỗi chữ cái lùi 1 vị trí trong bảng chữ cái): EPPS",
             "a": "DOOR", "w": ["DOOM", "FOOT", "DEER"],
             "digit": 5, "hint": "E lùi 1 vị trí là D."},
        ],
    },
    {
        "name": "Phòng thí nghiệm",
        "intro": "Mùi hóa chất nồng nặc. Mọi thứ đều có vẻ không ổn...",
        "order": [1, 0, 2],
        "order_text": "Ghép chìa 2 → chìa 1 → chìa 3.",
        "questions": [
            {"q": "Một người đi bộ 3 km/giờ. Sau 2 giờ 30 phút đi được bao nhiêu km?",
             "a": "7,5 km", "w": ["6 km", "7 km", "8 km"],
             "digit": 9, "hint": "3 × 2,5"},
            {"q": "Điền số tiếp theo: 1, 1, 2, 3, 5, 8, ?",
             "a": "13", "w": ["11", "12", "14"],
             "digit": 6, "hint": "Mỗi số bằng tổng hai số đứng trước."},
            {"q": "Ký hiệu hóa học của vàng là gì?",
             "a": "Au", "w": ["Ag", "Fe", "Go"],
             "digit": 0, "hint": "Từ tiếng Latin 'Aurum'."},
        ],
    },
    {
        "name": "Hầm tối",
        "intro": "Có thứ gì đó đang di chuyển trong bóng tối...",
        "order": [1, 2, 0],
        "order_text": "Ghép chìa 2 → chìa 3 → chìa 1.",
        "questions": [
            {"q": "Mình có thành phố nhưng không có nhà, có núi nhưng không có cây, có sông nhưng không có nước. Mình là gì?",
             "a": "Bản đồ", "w": ["Giấc mơ", "Bức ảnh", "Cuốn sách"],
             "digit": 2, "hint": "Bạn dùng nó để tìm đường."},
            {"q": "Số nhị phân 1011 bằng số thập phân nào?",
             "a": "11", "w": ["9", "10", "13"],
             "digit": 7, "hint": "8 + 0 + 2 + 1"},
            {"q": "Tôi nói mà không có miệng, nghe mà không có tai, chỉ sống nhờ không khí. Tôi là gì?",
             "a": "Tiếng vang", "w": ["Cơn gió", "Cái loa", "Bóng ma"],
             "digit": 3, "hint": "Hét vào hang núi sẽ nghe thấy tôi."},
        ],
    },
    {
        "name": "Phòng cuối cùng",
        "intro": "Cánh cửa cuối cùng, to lớn và lạnh lẽo. Chỉ còn một bước nữa...",
        "order": [2, 0, 1],
        "order_text": "Ghép chìa 3 → chìa 1 → chìa 2.",
        "questions": [
            {"q": "Tôi bay mà không có cánh, khóc mà không có mắt. Tôi là gì?",
             "a": "Đám mây", "w": ["Con chim", "Máy bay", "Cái bóng"],
             "digit": 1, "hint": "Nhìn lên trời khi sắp mưa."},
            {"q": "Trong cuộc đua, bạn vượt qua người đang đứng thứ 2. Giờ bạn thứ mấy?",
             "a": "Thứ 2", "w": ["Thứ 1", "Thứ 3", "Thứ 4"],
             "digit": 9, "hint": "Bạn thế chỗ người đó."},
            {"q": "Trong game Doors, thực thể nháy đèn rồi lao qua cực nhanh tên là gì?",
             "a": "Rush", "w": ["Seek", "Figure", "Screech"],
             "digit": 4, "hint": "Nó bắt đầu bằng chữ R."},
        ],
    },
]

MUSIC_FILE = "doors-roblox-ost-elevator-jam-made-with-Voicemod.mp3"
PLAY_MUSIC_FILE = "05. In The House.mp3"   # nhạc nền khi đang chơi

# Âm thanh bão: sấm cắt từ file "tiengsamset.mp3" (đã xử lý) + tiếng mưa lặp liền mạch.
# Đặt 2 file này cùng thư mục với app.py. Thiếu file thì game tự dùng âm thanh tổng hợp như cũ.
# Tiếng bước chân: file "tiengchan.mp3" (đặt cùng thư mục với app.py). Game cắt từng bước chân theo bảng STEP_CLIPS
# [giây bắt đầu, độ to] rồi phát lần lượt; chạy thì phát nhanh hơn + cao hơn một chút. Thiếu file -> dùng tiếng tổng hợp cũ.
CATCH_FILE = "faaahhhh.mp3"     # tiếng khi ma bắt được người chơi (đặt cùng thư mục với app.py; thiếu file -> dùng tiếng gào tổng hợp)
GHOST_FILE = "tiengma.mp3"      # tiếng ma: phát khi ma xuất hiện (đặt cùng thư mục với app.py; thiếu file -> dùng tiếng tổng hợp)
STEP_FILE = "tiengchan.mp3"
STEP_CLIPS = [[0.357, 0.126], [1.009, 0.144], [1.609, 0.085], [2.236, 0.152], [2.852, 0.159], [3.477, 0.216], [4.102, 0.09], [4.775, 0.137], [5.373, 0.078], [6.027, 0.132], [6.624, 0.088], [7.266, 0.21], [7.871, 0.219], [8.504, 0.177], [9.101, 0.236], [9.732, 0.196], [10.365, 0.212], [11.021, 0.115], [11.64, 0.086], [12.267, 0.153], [12.883, 0.157], [13.508, 0.215], [14.133, 0.089], [14.806, 0.137], [15.404, 0.078], [16.058, 0.132], [16.655, 0.142], [17.322, 0.126], [17.959, 0.136], [18.628, 0.115], [19.278, 0.116], [19.922, 0.21], [20.53, 0.253], [21.179, 0.152], [21.823, 0.087], [22.482, 0.154], [23.096, 0.083], [23.784, 0.121], [25.072, 0.092], [25.708, 0.107], [26.407, 0.112]]
THUNDER_FILE = "thunder_fx.mp3"
RAIN_FILE = "rain_loop.wav"
# Bảng cắt của THUNDER_FILE: s = giây bắt đầu clip trong file, d = độ dài, c = thời điểm TIẾNG NỔ trong clip
# (game căn c đúng vào lúc tia chớp + độ trễ), k = 'crack' (nổ gắt, dùng cho sét gần) / 'roll' (sấm cuộn, sét xa).
THUNDER_CLIPS = [
    {"n": "A", "k": "crack", "s": 0.0, "d": 3.07, "c": 0.08},
    {"n": "B", "k": "crack", "s": 3.47, "d": 1.866, "c": 0.08},
    {"n": "C", "k": "crack", "s": 5.736, "d": 1.81, "c": 0.08},
    {"n": "D", "k": "crack", "s": 7.946, "d": 7.108, "c": 0.08},
    {"n": "E", "k": "crack", "s": 15.454, "d": 8.08, "c": 0.08},
    {"n": "F", "k": "crack", "s": 23.934, "d": 3.082, "c": 0.08},
    {"n": "G", "k": "crack", "s": 27.416, "d": 2.428, "c": 0.08},
    {"n": "I", "k": "crack", "s": 30.244, "d": 5.47, "c": 0.08},
    {"n": "L1", "k": "crack", "s": 36.114, "d": 1.766, "c": 0.08},
    {"n": "M", "k": "crack", "s": 38.28, "d": 4.31, "c": 0.08},
    {"n": "N", "k": "crack", "s": 42.99, "d": 2.514, "c": 0.08},
    {"n": "O", "k": "crack", "s": 45.904, "d": 3.952, "c": 0.08},
    {"n": "J", "k": "roll", "s": 50.256, "d": 6.35, "c": 0.3},
    {"n": "L2", "k": "roll", "s": 57.006, "d": 5.15, "c": 0.3},
    {"n": "intro", "k": "roll", "s": 62.556, "d": 2.85, "c": 0.3}
]


def _norm(s: str) -> str:
    """So khớp tên file không phân biệt hoa/thường, dấu cách, gạch dưới, dấu chấm."""
    return "".join(ch for ch in s.lower() if ch.isalnum())


@st.cache_data(show_spinner=False)
def load_mp3(name: str, skip: str = "", fallback: bool = False) -> str:
    """Đọc file mp3 (cùng thư mục với app.py) và nhúng vào game dạng data-URI."""
    base = Path(__file__).resolve().parent
    p = base / name
    if not p.exists():
        want = _norm(Path(name).stem)
        files = sorted(base.glob("*.mp3"))
        same = [f for f in files if _norm(f.stem) == want]
        if same:
            p = same[0]
        elif fallback:
            other = [f for f in files if _norm(f.stem) != _norm(Path(skip).stem)]
            if not other:
                return ""
            p = other[0]
        else:
            return ""
    return "data:audio/mpeg;base64," + base64.b64encode(p.read_bytes()).decode()


@st.cache_data(show_spinner=False)
def load_asset(name: str, mime: str) -> str:
    """Đọc file âm thanh cùng thư mục với app.py -> data-URI (rỗng nếu không có)."""
    p = Path(__file__).resolve().parent / name
    if not p.exists():
        return ""
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def build_data() -> str:
    out = []
    for d in DOORS:
        out.append({
            "name": d["name"], "intro": d["intro"], "order": d["order"], "order_text": d["order_text"],
            # o[0] luôn là đáp án đúng; phía JS sẽ xáo thứ tự A/B/C/D
            "questions": [
                {"q": q["q"], "o": [q["a"]] + q["w"], "digit": q["digit"], "hint": q["hint"]}
                for q in d["questions"]
            ],
        })
    return json.dumps(out, ensure_ascii=False)


# ---------------------------------------------------------------------------
# GAME 3D (HTML + Three.js)
# ---------------------------------------------------------------------------
GAME_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>
  html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000;font-family:'Times New Roman','Noto Serif',Georgia,serif;color:#eee;user-select:none}
  /* Khung 16:9: #stage luôn giữ tỉ lệ 16:9 (letterbox), #ui là lớp giao diện thiết kế ở 1280x720 rồi scale theo khung */
  #stage{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);overflow:hidden;background:#000}
  #c{position:absolute;inset:0}
  #c canvas{display:block}
  #ui{position:absolute;left:0;top:0;width:1280px;height:720px;transform-origin:0 0;overflow:hidden;pointer-events:none}
  .ov,#modal,#sl,#fs,button,input{pointer-events:auto}
  #fs{position:absolute;top:8px;right:10px;z-index:30;padding:5px 10px;font-size:13px;margin:0;opacity:.75}
  #fs:hover,#mu:hover{opacity:1}
  #mu{position:absolute;top:8px;right:74px;z-index:30;padding:5px 9px;font-size:13px;margin:0;opacity:.75}
  #lockbtn{position:absolute;right:16px;bottom:16px;z-index:7;width:56px;height:56px;padding:0;margin:0;border-radius:50%;
           font-size:18px;font-weight:bold;background:rgba(0,0,0,.55);border:2px solid #9a2a2a;display:none}
  #lockbtn.on{background:rgba(120,90,10,.75);border-color:#ffd86b;box-shadow:0 0 14px #a80}
  #cross.lk{box-sizing:border-box;width:22px;height:22px;margin:-11px;background:transparent;border:2px solid rgba(255,255,255,.85);box-shadow:0 0 6px #000}
  #cross.lk:after{content:'';position:absolute;left:50%;top:50%;width:4px;height:4px;margin:-2px;border-radius:50%;background:#fff}
  #musichint{display:none;margin-top:14px;font-size:14px;color:#8a8070;animation:mh 1.6s infinite}
  @keyframes mh{0%,100%{opacity:.35}50%{opacity:1}}
  .row{display:flex;align-items:center;justify-content:center;gap:10px;margin:8px 0}
  .row input[type=range]{width:320px;accent-color:#b3141a}
  .sq{width:42px;padding:6px 0;font-size:20px}
  #settings .hw{text-align:center;width:600px}
  #ql{color:#ffd86b;font-size:19px;margin:4px 0}
  #qd{font-size:13px;color:#9a9080;margin:4px auto;max-width:520px}
  #opts{display:none;flex-direction:column;gap:8px;margin-bottom:8px}
  .opt{display:flex;align-items:center;gap:12px;width:100%;text-align:left;font-size:17px;padding:10px 14px;margin:0;letter-spacing:0;box-sizing:border-box}
  .opt b{display:inline-block;flex:none;min-width:28px;height:28px;line-height:28px;text-align:center;border-radius:50%;background:#7a2a2a;color:#ffd86b}
  .opt.bad{opacity:.38;text-decoration:line-through;cursor:not-allowed;background:#1c0808;border-color:#4a2a2a;box-shadow:none}
  .ov{position:absolute;inset:0;display:none;flex-direction:column;align-items:center;justify-content:center;
      background:radial-gradient(ellipse at center,rgba(30,8,8,.88),rgba(0,0,0,.97));text-align:center;padding:20px;z-index:20;overflow:auto}
  #mbg{position:absolute;inset:0;display:none;overflow:hidden;background:#000}
  #mimg{position:absolute;inset:-2%;background:#000 url(__MENUBG__) center/cover no-repeat;animation:mzoom 40s ease-in-out infinite alternate}
  @keyframes mzoom{from{transform:scale(1) translateX(-.6%)}to{transform:scale(1.07) translateX(.6%)}}
  #msky{position:absolute;left:0;right:0;top:0;height:58%;background:linear-gradient(#010103 0%,rgba(1,1,4,.96) 45%,rgba(2,3,8,.7) 75%,rgba(0,0,0,0) 100%)}   /* bầu trời đen, chỉ lộ ra khi sét */
  #mfx{position:absolute;inset:0;width:100%;height:100%}
  #mfl{position:absolute;inset:0;opacity:0;background:radial-gradient(ellipse at 45% 30%,rgba(200,220,255,.9),rgba(120,150,220,.35) 60%,rgba(60,80,140,.1))}
  #menu{background:radial-gradient(ellipse at center,rgba(0,0,0,.22) 0%,rgba(0,0,0,.05) 50%,rgba(0,0,0,.3) 100%)}   /* menu trong suốt để thấy khu rừng phía sau */
  #menu h1{text-shadow:0 0 22px #000,0 0 8px #000,0 0 18px #600}
  .ov h1{font-size:64px;letter-spacing:14px;margin:0 0 18px;color:#b3141a;text-shadow:0 0 18px #600,0 0 4px #000}
  .ov p{max-width:580px;line-height:1.55;color:#c9c0b0}
  button{background:#3a0d0d;color:#eee;border:1px solid #9a2a2a;padding:10px 22px;font-size:16px;
         border-radius:4px;cursor:pointer;margin:4px;font-family:inherit;letter-spacing:1px}
  button:hover{background:#6a1414;box-shadow:0 0 12px #a00}
  .mb{display:flex;flex-direction:column;align-items:center;gap:6px}
  .mb button{width:260px;font-size:19px;padding:12px 22px}
  #story{background:radial-gradient(ellipse at center,rgba(0,0,0,.62),rgba(0,0,0,.85));animation:sopen 1.2s ease}
  @keyframes sopen{0%{opacity:0;filter:brightness(3.2) blur(8px)}35%{opacity:.8;filter:brightness(1.8) blur(3px)}55%{opacity:.35}100%{opacity:1;filter:none}}
  #sttl{letter-spacing:8px;animation:stitle 1.6s ease both}
  @keyframes stitle{from{letter-spacing:34px;opacity:0;filter:blur(6px)}to{letter-spacing:8px;opacity:1;filter:none}}
  .sty{max-width:620px;padding:0 10px;margin-bottom:22px;text-align:center;line-height:1.7;color:#cfc6b6;font-size:19px}
  .sty p{margin:0 auto 14px;max-width:none;opacity:0;animation:sfade 1.5s ease forwards}
  .sty p:nth-child(1){animation-delay:.5s}.sty p:nth-child(2){animation-delay:2.4s}
  .sty b{color:#fff}
  .sty .cl{color:#ffd86b;letter-spacing:1px;text-shadow:0 0 10px #c8861a,0 0 22px #6a4a10}
  .sty kbd{background:#2a1010;border:1px solid #7a2a2a;border-radius:3px;padding:0 6px;font-family:inherit;color:#ffd86b}
  #story .mb button{opacity:0;animation:sfade 1.2s ease 3.4s forwards}
  @keyframes sfade{0%{opacity:0;filter:blur(9px);transform:translateY(12px) scale(1.04)}45%{opacity:.85}58%{opacity:.25}72%{opacity:.95}100%{opacity:1;filter:none;transform:none}}
  .hw{max-width:700px;text-align:left;line-height:1.5;color:#c9c0b0;font-size:15px}
  .hw h3{margin:14px 0 4px;color:#d9b45a;font-size:17px;letter-spacing:1px}
  .hw ul{margin:0;padding-left:20px}
  .hw b{color:#fff}
  .hw kbd{background:#2a1010;border:1px solid #7a2a2a;border-radius:3px;padding:0 6px;font-family:inherit;color:#ffd86b}
  #hud{position:absolute;top:10px;left:12px;font-size:17px;text-shadow:0 0 4px #000;z-index:5;line-height:1.5}
  #ks{color:#ffd86b;font-size:20px}
  #ot{font-size:13px;color:#bbb}
  #sl{font-size:13px;color:#999;cursor:pointer;display:inline-block;margin-top:2px}
  #sl.on{color:#7dff9a}
  #help{position:absolute;bottom:8px;left:12px;font-size:12px;color:#8a8a8a;z-index:5;text-shadow:0 0 3px #000}
  #cross{position:absolute;left:50%;top:50%;width:4px;height:4px;margin:-2px;border-radius:50%;
         background:rgba(255,255,255,.45);z-index:5;pointer-events:none}
  #prompt{position:absolute;left:50%;top:58%;transform:translateX(-50%);background:rgba(0,0,0,.65);
          padding:6px 14px;border-radius:4px;font-size:18px;display:none;z-index:6;border:1px solid #9a2a2a}
  #banner{position:absolute;left:50%;top:14%;transform:translateX(-50%);text-align:center;white-space:pre-line;
          font-size:22px;text-shadow:0 0 8px #000;opacity:0;transition:opacity .5s;z-index:6;max-width:80%;pointer-events:none}
  #whisper{position:absolute;font-size:30px;font-style:italic;color:#8a0c0c;opacity:0;transition:opacity 1s;
           z-index:4;pointer-events:none;text-shadow:0 0 10px #000;letter-spacing:3px}
  #flash{position:absolute;inset:0;background:#a00;opacity:0;pointer-events:none;transition:opacity .45s;z-index:11}
  #bars{position:absolute;inset:0;pointer-events:none;z-index:9;opacity:0;transition:opacity .6s;
        background:linear-gradient(#000 0 12%,transparent 12% 88%,#000 88%)}
  #bars.on{opacity:1}
  #warn{z-index:25}
  .chk{display:flex;align-items:center;gap:10px;justify-content:center;margin:14px 0;color:#e0d6c0;font-size:16px;cursor:pointer}
  .chk input{width:20px;height:20px;accent-color:#b3141a;cursor:pointer}
  #fade{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none;transition:opacity .8s;z-index:12}
  #scare{position:absolute;inset:0;width:100%;height:100%;display:none;pointer-events:none;z-index:10;image-rendering:pixelated}
  #hide{position:absolute;inset:0;display:none;pointer-events:none;z-index:4}
  /* Tủ: hai cánh cửa khép lại, chỉ chừa 1 kẽ hở DỌC ở giữa để nhìn ra ngoài (mép cửa có viền gỗ mờ) */
  #hide.ward{background:linear-gradient(90deg,#000 0 46.6%,#24170e 46.6% 47.6%,transparent 47.6% 52.4%,#24170e 52.4% 53.4%,#000 53.4% 100%)}
  #hide.bed{background:linear-gradient(#000 0 42%,transparent 60%),radial-gradient(ellipse at center,transparent 45%,rgba(0,0,0,.85) 100%)}
  #vig{position:absolute;inset:0;pointer-events:none;z-index:3;
       background:radial-gradient(ellipse at center,transparent 38%,rgba(0,0,0,.55) 75%,rgba(0,0,0,.95) 100%)}
  #grain{position:absolute;inset:0;width:100%;height:100%;image-rendering:pixelated;opacity:.2;
         mix-blend-mode:overlay;pointer-events:none;z-index:3}
  #lowhp{position:absolute;inset:0;pointer-events:none;z-index:3;opacity:0;
         background:radial-gradient(ellipse at center,transparent 35%,rgba(150,0,0,.75) 100%)}
  #lowhp.pulse{animation:pl 1.1s infinite}
  @keyframes pl{0%,100%{opacity:.25}50%{opacity:1}}
  #modal{position:absolute;inset:0;display:none;align-items:center;justify-content:center;
         background:rgba(0,0,0,.65);z-index:15}
  /* Bảng câu hỏi = một tờ giấy cũ */
  /* Bảng câu hỏi = tờ giấy nhàu, rách mép, chữ viết tay bằng bút chì (kiểu mấy tờ giấy trong Doors) */
  #box{position:relative;color:#16130f;border:0;padding:36px 48px 34px;width:min(760px,90%);
       text-align:center;transform:rotate(-1deg);
       font-family:'Segoe Print','Bradley Hand','Chalkboard SE','Comic Sans MS','Marker Felt',cursive;
       background:#b3a78c;background-size:100% 100%;
       clip-path:polygon(1% 3%,12% 0,27% 2.5%,44% .5%,63% 2%,82% 0,99% 2%,100% 20%,98.5% 38%,100% 57%,98% 76%,100% 98%,84% 100%,66% 98%,48% 100%,30% 98.5%,12% 100%,0 97%,1.5% 78%,0 58%,2% 38%,0 18%)}
  #mt{color:#8a0f0f;font-size:30px;margin-bottom:12px;font-weight:900;letter-spacing:2px;text-transform:uppercase;text-shadow:none}
  #mq{font-size:27px;line-height:1.4;margin-bottom:18px;color:#16130f;font-weight:900;text-transform:uppercase;letter-spacing:.5px;
      text-shadow:none;-webkit-font-smoothing:antialiased}
  #mi{width:80%;padding:9px;font-size:22px;border:0;border-bottom:3px solid #2b2722;border-radius:0;
      background:rgba(255,255,255,.14);color:#2b2722;text-align:center;outline:none;font-family:inherit;letter-spacing:4px}
  #fb{min-height:28px;margin:10px 0;color:#8a0f0f;font-size:21px;font-weight:900;text-transform:uppercase;letter-spacing:1px}
  #box button{background:rgba(40,32,20,.06);color:#16130f;border:3px solid #16130f;border-radius:3px 8px 4px 7px;
      box-shadow:none;font-family:inherit;text-transform:uppercase;text-shadow:none;font-weight:900;font-size:19px;padding:10px 22px}
  #box button:hover{background:#16130f;color:#d8ccb0;box-shadow:none;text-shadow:none}
  #box .opt{font-size:25px;font-weight:900;padding:11px 18px;gap:16px;letter-spacing:.5px}
  #box .opt b{background:transparent;color:#8a0f0f;border:3px solid #8a0f0f;text-shadow:none;font-size:22px;min-width:40px;height:40px;line-height:36px}
  #box .opt.bad{opacity:.5;text-decoration:line-through;text-decoration-thickness:3px;cursor:not-allowed;background:rgba(0,0,0,.06);border-color:#7a6e55;color:#5e5543}
  #box .opt.bad:hover{background:rgba(0,0,0,.06);color:#5e5543}
  html,body,#stage,#c canvas{touch-action:none;overscroll-behavior:none;-webkit-touch-callout:none;-webkit-tap-highlight-color:transparent;-webkit-user-select:none}
  #tui{display:none}
  .tb{position:absolute;z-index:8;border-radius:50%;border:2px solid #9a2a2a;background:rgba(0,0,0,.45);color:#eee;font-weight:bold;
      display:flex;align-items:center;justify-content:center;pointer-events:auto;touch-action:none;user-select:none;-webkit-user-select:none}
  .tb.on{background:rgba(120,90,10,.75);border-color:#ffd86b}
  #tE{right:40px;bottom:70px;width:110px;height:110px;font-size:40px}
  #tRun{right:182px;bottom:34px;width:84px;height:84px;font-size:17px;letter-spacing:1px}
  #joyB,#joyK{position:absolute;border-radius:50%;display:none;pointer-events:none;z-index:7}
  #joyB{width:150px;height:150px;margin:-75px;border:2px solid rgba(255,255,255,.35);background:rgba(255,255,255,.06)}
  #joyK{width:64px;height:64px;margin:-32px;background:rgba(255,255,255,.3);border:2px solid rgba(255,255,255,.55)}
  .touch #fs{padding:10px 16px;font-size:18px}
  .touch #mu{padding:10px 14px;font-size:18px;right:104px}
  #rot{position:fixed;inset:0;z-index:99;background:#000;color:#d9b45a;display:none;align-items:center;justify-content:center;
       text-align:center;padding:20px;font-size:22px;letter-spacing:2px}
</style>
</head>
<body>
<div id="stage"><div id="c"></div><div id="mbg"><div id="mimg"></div><div id="msky"></div><canvas id="mfx"></canvas><div id="mfl"></div></div><div id="ui">
<div id="vig"></div><canvas id="grain"></canvas><div id="lowhp"></div>
<div id="cross"></div>
<div id="hud"><div id="dn"></div><div id="hp"></div><div id="hn"></div><div id="ks"></div><div id="ot"></div></div>
<div id="help">WASD / ←→: di chuyển · Kéo chuột: nhìn · Shift: Shift Lock · Giữ Space: chạy · E: tương tác · A/B/C/D: chọn đáp án · Esc: đóng</div>
<button id="fs" title="Toàn màn hình">FULL</button><button id="mu" title="Bật / tắt âm thanh">🔊</button>
<button id="lockbtn" title="Shift Lock (phím Shift)">SL</button>
<div id="tui"><div id="joyB"></div><div id="joyK"></div><div id="tE" class="tb">E</div><div id="tRun" class="tb">CHẠY</div></div>
<div id="prompt"></div>
<div id="banner"></div>
<div id="whisper"></div>
<div id="hide"></div>
<canvas id="scare" width="640" height="360"></canvas>
<div id="flash"></div>
<div id="bars"></div>
<div id="fade"></div>

<div id="modal"><div id="box">
  <div id="mt"></div><div id="mq"></div>
  <div id="opts"></div>
  <input id="mi" autocomplete="off" spellcheck="false" inputmode="numeric">
  <div id="fb"></div>
  <button id="b1">Trả lời</button><button id="b2">Gợi ý</button><button id="b3">Đóng (Esc)</button>
</div></div>

<div id="menu" class="ov" style="display:flex">
  <h1>ESCAPE</h1>
  <div class="mb">
    <button id="start">CHƠI</button>
    <button id="how">HƯỚNG DẪN</button>
    <button id="settingsBtn">CÀI ĐẶT</button>
  </div>
  <p id="musichint">Bấm vào bất kỳ đâu để bật nhạc</p>
</div>

<div id="settings" class="ov">
  <h1 style="font-size:40px;letter-spacing:8px">CÀI ĐẶT</h1>
  <div class="hw">
    <h3>Đồ họa</h3>
    <div class="row"><button id="gLow">THẤP</button><button id="gHigh">CAO</button></div>
    <div class="row"><button id="qm" class="sq">−</button><input id="qr" type="range" min="1" max="10" step="1" value="8"><button id="qp" class="sq">+</button></div>
    <div id="ql"></div>
    <p id="qd"></p>
    <h3>Hiệu ứng</h3>
    <label class="chk" style="justify-content:flex-start"><input type="checkbox" id="rfchk2"> Giảm hiệu ứng chớp sáng (an toàn hơn cho người nhạy cảm ánh sáng)</label>
    <h3>Âm lượng nhạc</h3>
    <div class="row"><input id="vr" type="range" min="0" max="100" step="5" value="60"><span id="vv">60%</span></div>
  </div>
  <button id="sback">Quay lại</button>
</div>

<div id="story" class="ov">
  <div class="sty">
    <p>Tìm đủ <b class="cl">3 MANH MỐI PHÁT SÁNG</b> trong mỗi phòng và <b>trả lời các câu hỏi</b> để mở cửa.</p>
    <p>Khi có ma xuất hiện, hãy <b>trốn dưới gầm giường</b> hoặc <b>trong tủ quần áo</b> (bấm <kbd>E</kbd>).</p>
  </div>
  <div class="mb"><button id="sgo">BẮT ĐẦU</button></div>
</div>

<div id="howto" class="ov">
  <h1 style="font-size:40px;letter-spacing:8px">HƯỚNG DẪN</h1>
  <div class="hw">
    <h3>Điều khiển</h3>
    <ul>
      <li><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> hoặc phím mũi tên: di chuyển / xoay</li>
      <li><b>Kéo chuột</b>: nhìn xung quanh</li>
      <li><kbd>Shift</kbd> hoặc nút SL góc phải dưới: bật / tắt <b>Shift Lock</b> giống Roblox — chuột bị khóa ở giữa màn hình, hiện tâm ngắm, xoay camera mà không cần bấm chuột. Lỡ nhả chuột (Esc) thì bấm vào màn hình để khóa lại</li>
      <li>Khi tắt Shift Lock: giữ chuột trái hoặc phải rồi kéo để nhìn</li>
      <li><kbd>A</kbd><kbd>B</kbd><kbd>C</kbd><kbd>D</kbd> hoặc bấm chuột: chọn đáp án khi trả lời câu hỏi</li>
      <li>Giữ <kbd>Space</kbd>: chạy</li>
      <li><b>Điện thoại</b> (nên xoay ngang): cần gạt bên trái màn hình để đi, vuốt bên phải để nhìn, nút <kbd>E</kbd> để tương tác, giữ nút <kbd>CHẠY</kbd> để chạy</li>
      <li><kbd>E</kbd>: tương tác (xem manh mối, mở cửa, trốn vào tủ / gầm giường)</li>
      <li><kbd>Esc</kbd>: đóng bảng câu hỏi</li>
    </ul>
    <h3>Mục tiêu</h3>
    <ul>
      <li>Mỗi phòng có <b>3 manh mối</b> phát sáng nhấp nháy 3 giây một lần. Trả lời <b>câu hỏi trắc nghiệm A/B/C/D</b> để lấy 3 chữ số (chìa khóa).</li>
      <li>Ghép các chữ số theo đúng thứ tự gợi ý rồi nhập mật mã vào <b>cánh cửa</b> để sang phòng tiếp theo.</li>
      <li>Có 5 cánh cửa. Chọn sai đáp án hoặc nhập sai mật mã sẽ mất 1 (có 3 ).</li>
    </ul>
    <h3>Con ma</h3>
    <ul>
      <li>Thỉnh thoảng <b>đèn sẽ chớp liên tục</b>. Đó là dấu hiệu một con ma sắp xuất hiện.</li>
      <li>Hãy <b>trốn ngay</b> vào <b>tủ quần áo</b> hoặc <b>gầm giường</b> (nhìn vào rồi bấm <kbd>E</kbd>).</li>
      <li>Khi đã trốn, đừng cử động. Ma sẽ đến lục soát rồi bỏ đi. Chỉ ra ngoài khi nó đã đi hẳn.</li>
      <li>Nếu bị ma bắt, bạn <b>chết</b> và phải <b>chơi lại từ cửa số 1</b>.</li>
      <li>Những đôi mắt đỏ trong bóng tối sẽ biến mất khi bạn nhìn thẳng vào chúng.</li>
    </ul>
    <p style="text-align:center;color:#8a8a8a;margin-top:14px"><i>Nên đeo tai nghe và tắt đèn phòng.</i></p>
  </div>
  <button id="hback">Quay lại</button>
</div>

<div id="warn" class="ov" style="display:flex">
  <h1 style="color:#d9b45a;font-size:46px;letter-spacing:8px;text-shadow:0 0 14px #6a4a10">CẢNH BÁO</h1>
  <div class="hw" style="width:620px">
    <p style="margin:0 0 6px;max-width:none">Trò chơi này là game <b>kinh dị</b> và có chứa:</p>
    <ul>
      <li><b>Âm thanh lớn, đột ngột</b> (tiếng hét, tiếng động mạnh). Hãy hạ âm lượng trước khi chơi, nhất là khi đeo tai nghe.</li>
      <li><b>Ánh sáng chớp nhanh, màn hình nhấp nháy</b>. Có thể gây khó chịu hoặc kích phát cơn co giật ở người nhạy cảm với ánh sáng / mắc chứng động kinh.</li>
      <li><b>Cảnh hù dọa bất ngờ</b> (jumpscare) và hình ảnh rùng rợn.</li>
      <li><b>Không phù hợp</b> với trẻ nhỏ, người có bệnh tim hoặc dễ hoảng sợ.</li>
    </ul>
    <p style="margin:10px 0 0;max-width:none">Nếu cảm thấy chóng mặt, buồn nôn, đau đầu hoặc khó chịu, hãy <b>dừng chơi ngay</b> và nghỉ ngơi.</p>
  </div>
  <button id="warnok" style="font-size:19px;padding:12px 30px">Tôi hiểu, tiếp tục</button>
</div>

<div id="over" class="ov"><h1>BẠN ĐÃ CHẾT</h1><p id="overmsg"></p>
  <div><button id="retry">Chơi lại từ đầu</button><button id="tomenu">Menu</button></div></div>
<div id="win" class="ov"><h1 style="color:#d9b45a">THOÁT ĐƯỢC!</h1><p>Bạn đã vượt qua cả 5 cánh cửa... lần này.</p>
  <div><button id="again">Chơi lại</button><button id="tomenu2">Menu</button></div></div>

</div></div>
<div id="rot">XOAY NGANG ĐIỆN THOẠI ĐỂ CHƠI</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){
const DOORS = __DATA__;
const MUSIC_SRC = "__MUSIC__";
const PLAY_SRC = "__MUSIC2__";
const MAX_HP=3, HINTS0=5, RH=4;
const SIZES=[[18,26],[20,28],[22,30],[22,32],[24,34]];
let RW=18, RD=26;
const $=id=>document.getElementById(id);
const SRC='<!DOCTYPE html>\n'+document.documentElement.outerHTML;   // bản sao trang để mở ở tab mới
function loadNum(k,d,lo,hi){try{const v=parseInt(localStorage.getItem(k));return(v>=lo&&v<=hi)?v:d;}catch(e){return d;}}
function saveNum(k,v){try{localStorage.setItem(k,v);}catch(e){}}
// Nút tắt/bật âm thanh: mọi nút phát ra loa đều được dẫn qua 1 gain tổng (master) để tắt tiếng một lần là im hết
let MUTED=loadNum('doors_mute',0,0,1)===1;
const _mc=AudioNode.prototype.connect, masters=new WeakMap();
function masterOf(ctx){let m=masters.get(ctx); if(!m){m=ctx.createGain(); m.gain.value=MUTED?0:1; _mc.call(m,ctx.destination); masters.set(ctx,m);} return m;}
AudioNode.prototype.connect=function(d,...r){
  try{ if(typeof AudioDestinationNode!=='undefined'&&d instanceof AudioDestinationNode) d=masterOf(d.context); }catch(e){}
  return _mc.call(this,d,...r);
};
const COARSE=!!(window.matchMedia&&matchMedia('(pointer:coarse)').matches);   // điện thoại / máy tính bảng
let Q=loadNum('doors_q',COARSE?4:8,1,10), HQ=Q>=6;       // mức đồ họa 1-10 (<=5: Thấp, >=6: Cao)
let STW=1280, STH=720, mouseX=0, mouseY=0, mouseIn=false, optOrder=[], wrongSet={}, lockFailShown=false, lockBlocked=false, lockEver=false, lockMsgT=0, touchMode=COARSE;
// Cao: độ phân giải gần đầy đủ. Thấp: render độ phân giải rất nhỏ rồi phóng to kiểu pixel (low-poly retro)
const pr=()=>HQ?Math.max(.8,Math.min(window.devicePixelRatio||1,.55+Q*.15)):(0.28+Q*0.05);
let RF=loadNum('doors_rf',0,0,1)===1;   // giảm hiệu ứng chớp sáng
let hp=MAX_HP, hints=HINTS0, door=0, solved=[false,false,false], hintShown={};
let state='menu', modalOpen=false, modalMode='q', modalIdx=0, hidden=false, doorOpen=false, transitioning=false;
let yaw=0, pitch=0, dragging=false, shake=0, bob=0, bannerT=null, cur=null, curSpot=null, spots=[];
let keys={}, tt=0, stepT=0, hbT=0, evT=14, flickT=0, nextFlick=12, lampF=1, dark=0;
let shiftLock=false, expectUnlock=false, scareT=0, scareYaw=0, ghostTimer=40, scareFlashT=0;
let room=null, doorPivot=null, obstacles=[], inter=[], watchers=[], flameMat=null, fireMat=null;
const gh={phase:'idle',t:0,t0:1,x:0,z:0,alpha:0,peek:0,face:0,step:0,ux:0,uz:1};

// ---------- Renderer / Scene ----------
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(pr());
renderer.setSize(1280,720);
renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.3;
renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
$('c').appendChild(renderer.domElement);
const canvas=renderer.domElement;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x030101);
scene.fog=new THREE.FogExp2(0x050202,0.045);
const camera=new THREE.PerspectiveCamera(72,16/9,0.1,70);
camera.rotation.order='YXZ';
scene.add(camera);
// Khung 16:9 luôn nằm gọn trong màn hình (letterbox), giao diện scale theo khung
const stage=$('stage'), ui=$('ui');
function fit(){
  const W=innerWidth,H=innerHeight; let w=W,h=Math.round(W*9/16);
  if(h>H){h=H;w=Math.round(H*16/9);}
  STW=w;STH=h; stage.style.width=w+'px'; stage.style.height=h+'px';
  ui.style.transform='scale('+(w/1280)+')';
  renderer.setSize(w,h); camera.aspect=16/9; camera.updateProjectionMatrix();
  $('rot').style.display=(touchMode&&H>W)?'flex':'none';
}
fit();

// Đèn pin
const spot=new THREE.SpotLight(0xfff0cc,2.1,24,Math.PI/5.2,0.5,1.1);
spot.position.set(0.2,-0.1,0);   // đèn pin đã bỏ: spot không gắn vào camera/scene nên không chiếu sáng
 camera.add(spot.target); spot.target.position.set(0,0,-3);
spot.shadow.mapSize.set(1024,1024); spot.shadow.camera.near=0.2; spot.shadow.camera.far=24; spot.shadow.bias=-0.0006;
const ambL=new THREE.AmbientLight(0x4a3a34,0.85); scene.add(ambL);
// Các đèn cố định (tạo một lần để tránh biên dịch lại shader)
const lamp=new THREE.PointLight(0xffb066,1.1,24); scene.add(lamp);
lamp.shadow.mapSize.set(512,512); lamp.shadow.camera.near=0.3; lamp.shadow.camera.far=24; lamp.shadow.bias=-0.003;
const lampB=new THREE.PointLight(0xffb066,0.9,22); scene.add(lampB);
const doorLight=new THREE.PointLight(0xfff1c9,0,10); scene.add(doorLight);
const sconceL=[0,1].map(()=>{const l=new THREE.PointLight(0xff9a40,1.0,9);scene.add(l);return l;});
const clueL=[0,1,2].map(()=>{const l=new THREE.PointLight(0xffaa44,.9,5.5);scene.add(l);return l;});

// Bụi bay
const DUST=320, dustPos=new Float32Array(DUST*3);
const dustGeo=new THREE.BufferGeometry(); dustGeo.setAttribute('position',new THREE.BufferAttribute(dustPos,3));
const dust=new THREE.Points(dustGeo,new THREE.PointsMaterial({color:0xffddaa,size:0.035,transparent:true,opacity:.45,depthWrite:false}));
dust.frustumCulled=false; scene.add(dust);
function resetDust(){for(let i=0;i<DUST;i++){dustPos[i*3]=(Math.random()-.5)*RW;dustPos[i*3+1]=Math.random()*RH;dustPos[i*3+2]=(Math.random()-.5)*RD;}
  dustGeo.attributes.position.needsUpdate=true;}

// ---------- Texture thủ tục ----------
const CAN={};
function T(key,w,h,draw,rx,ry){
  if(!CAN[key]){const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);CAN[key]=c;}
  const t=new THREE.CanvasTexture(CAN[key]); t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(rx||1,ry||1); t.anisotropy=4;
  if(!HQ){t.magFilter=THREE.NearestFilter;t.minFilter=THREE.NearestMipmapNearestFilter;t.anisotropy=1;}   // texture vuông pixel
  return t;
}
const rnd=(a,b)=>a+Math.random()*(b-a);
function mulberry(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function noiseFx(g,w,h,a){const id=g.getImageData(0,0,w,h),d=id.data;for(let i=0;i<d.length;i+=4){const n=(Math.random()-.5)*a;d[i]+=n;d[i+1]+=n;d[i+2]+=n;}g.putImageData(id,0,0);}
function stains(g,w,h,n,a){for(let i=0;i<n;i++){const x=rnd(0,w),y=rnd(0,h),r=rnd(6,46),gr=g.createRadialGradient(x,y,0,x,y,r);
  gr.addColorStop(0,'rgba(0,0,0,'+a+')');gr.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=gr;g.fillRect(x-r,y-r,r*2,r*2);}}
const WALLC=['#6b4a35','#4a5a4a','#4a5568','#5a3a4a','#3d3d3d'];
const wallTex=(i,rx,ry)=>T('wall'+i,256,256,(g,w,h)=>{
  g.fillStyle=WALLC[i];g.fillRect(0,0,w,h);
  for(let x=0;x<w;x+=32){g.fillStyle='rgba(255,255,255,.05)';g.fillRect(x,0,16,h);}
  g.strokeStyle='rgba(0,0,0,.28)';g.lineWidth=2;
  for(let y=0;y<h;y+=64)for(let x=0;x<w;x+=64){const cx=x+32,cy=y+32;
    g.beginPath();g.moveTo(cx,cy-18);g.lineTo(cx+12,cy);g.lineTo(cx,cy+18);g.lineTo(cx-12,cy);g.closePath();g.stroke();
    g.beginPath();g.arc(cx,cy,3,0,6.3);g.stroke();}
  stains(g,w,h,26,.16);noiseFx(g,w,h,22);},rx,ry);
const carpetTex=(rx,ry)=>T('carpet',256,256,(g,w,h)=>{
  g.fillStyle='#3d0d10';g.fillRect(0,0,w,h);g.strokeStyle='rgba(200,150,60,.22)';g.lineWidth=2;
  for(let i=-h;i<w+h;i+=32){g.beginPath();g.moveTo(i,0);g.lineTo(i+h,h);g.stroke();g.beginPath();g.moveTo(i+h,0);g.lineTo(i,h);g.stroke();}
  g.fillStyle='rgba(0,0,0,.25)';for(let y=16;y<h;y+=32)for(let x=16;x<w;x+=32){g.fillRect(x-3,y-3,6,6);}
  stains(g,w,h,22,.22);noiseFx(g,w,h,34);},rx,ry);
const woodTex=(rx,ry)=>T('wood',128,128,(g,w,h)=>{
  g.fillStyle='#2e1b10';g.fillRect(0,0,w,h);
  for(let x=0;x<w;x+=16){g.fillStyle='rgba(0,0,0,.35)';g.fillRect(x,0,2,h);}
  for(let i=0;i<60;i++){g.strokeStyle='rgba(0,0,0,'+rnd(.05,.2)+')';g.beginPath();const x=rnd(0,w);g.moveTo(x,0);g.bezierCurveTo(x+6,h/3,x-6,h*2/3,x+rnd(-3,3),h);g.stroke();}
  noiseFx(g,w,h,26);},rx,ry);
const ceilTex=(rx,ry)=>T('ceil',256,256,(g,w,h)=>{g.fillStyle='#2b1f16';g.fillRect(0,0,w,h);stains(g,w,h,30,.4);noiseFx(g,w,h,24);},rx,ry);
const doorTex=()=>T('door',256,512,(g,w,h)=>{
  g.fillStyle='#6f4322';g.fillRect(0,0,w,h);
  for(let x=0;x<w;x+=32){g.fillStyle='rgba(0,0,0,.18)';g.fillRect(x,0,2,h);}
  [[24,24],[134,24],[24,270],[134,270]].forEach(p=>{const pw=98,ph=p[1]<200?230:210;
    g.fillStyle='rgba(0,0,0,.35)';g.fillRect(p[0],p[1],pw,ph);g.fillStyle='#7c4c28';g.fillRect(p[0]+6,p[1]+6,pw-12,ph-12);
    g.strokeStyle='rgba(0,0,0,.4)';g.strokeRect(p[0]+14,p[1]+14,pw-28,ph-28);});
  stains(g,w,h,10,.25);noiseFx(g,w,h,28);});
const bookTex=()=>T('books',256,128,(g,w,h)=>{
  g.fillStyle='#1b110a';g.fillRect(0,0,w,h);
  for(let r=0;r<4;r++){let x=4;const y=r*32;while(x<w-8){const bw=rnd(6,14),bh=rnd(18,28);
    g.fillStyle='hsl('+Math.floor(rnd(0,40))+','+Math.floor(rnd(20,50))+'%,'+Math.floor(rnd(14,30))+'%)';g.fillRect(x,y+30-bh,bw,bh);x+=bw+1;}
    g.fillStyle='#000';g.fillRect(0,y+30,w,3);}
  noiseFx(g,w,h,22);});
const paintTex=v=>T('paint'+v,256,320,(g,w,h)=>{
  const gr=g.createLinearGradient(0,0,0,h);gr.addColorStop(0,['#1d2a2a','#2a1d2a','#2a2a1d','#241a1a'][v%4]);gr.addColorStop(1,'#050505');
  g.fillStyle=gr;g.fillRect(0,0,w,h);
  g.fillStyle='#0b0b0b';g.beginPath();g.ellipse(w/2,h+10,95,120,0,0,7);g.fill();
  const ox=(v%3-1)*6;
  g.fillStyle='#b8a98a';g.beginPath();g.ellipse(w/2+ox,125,52,68,0,0,7);g.fill();
  g.fillStyle='#000';[-20,20].forEach(dx=>{g.beginPath();g.ellipse(w/2+dx+ox,112,11,15+(v%3)*2,0,0,7);g.fill();});
  g.fillStyle='#ff2a2a';[-20,20].forEach(dx=>{g.beginPath();g.arc(w/2+dx+ox,114,2.4,0,7);g.fill();});
  g.strokeStyle='#000';g.lineWidth=3;g.beginPath();g.moveTo(w/2-28+ox,158);g.quadraticCurveTo(w/2+ox,180+(v%3)*8,w/2+28+ox,158);g.stroke();
  g.strokeStyle='rgba(0,0,0,.5)';g.lineWidth=1;for(let i=0;i<8;i++){g.beginPath();g.moveTo(rnd(0,w),rnd(0,h));g.lineTo(rnd(0,w),rnd(0,h));g.stroke();}
  stains(g,w,h,14,.35);noiseFx(g,w,h,26);});
const bloodTex=()=>T('blood',128,128,(g,w,h)=>{
  for(let i=0;i<26;i++){const x=64+rnd(-40,40),y=64+rnd(-40,40),r=rnd(2,16),gr=g.createRadialGradient(x,y,0,x,y,r);
    gr.addColorStop(0,'rgba(110,5,5,.95)');gr.addColorStop(1,'rgba(90,0,0,0)');g.fillStyle=gr;g.beginPath();g.arc(x,y,r,0,7);g.fill();}});
const handTex=()=>T('hand',128,128,(g,w,h)=>{
  g.fillStyle='rgba(115,8,8,.92)';g.strokeStyle='rgba(115,8,8,.92)';g.lineCap='round';
  g.beginPath();g.ellipse(64,88,28,32,0,0,7);g.fill();g.lineWidth=11;
  for(let i=0;i<5;i++){const a=-2.45+i*.37;g.beginPath();g.moveTo(64+Math.cos(a)*16,88+Math.sin(a)*16);g.lineTo(64+Math.cos(a)*(i==2?58:52),88+Math.sin(a)*(i==2?58:52));g.stroke();}
  g.lineWidth=3;for(let i=0;i<5;i++){const x=rnd(40,88);g.beginPath();g.moveTo(x,110);g.lineTo(x,110+rnd(6,18));g.stroke();}});
const MSG=['ĐỪNG NHÌN','TRỐN ĐI','NÓ Ở ĐÂY','ĐỪNG CHẠY','KHÔNG CÓ LỐI RA'];
const msgTex=t=>T('msg'+t,512,128,(g,w,h)=>{
  g.font='bold 60px serif';g.textAlign='center';g.fillStyle='#7d0a0a';g.shadowColor='#400';g.shadowBlur=8;g.fillText(t,w/2,66);
  g.shadowBlur=0;for(let i=0;i<22;i++){g.fillRect(rnd(60,w-60),68,rnd(2,4),rnd(8,46));}});
const rugTex=()=>T('rug',256,512,(g,w,h)=>{
  g.fillStyle='#3b0c10';g.fillRect(0,0,w,h);
  g.strokeStyle='#b8893a';g.lineWidth=6;g.strokeRect(10,10,w-20,h-20);g.lineWidth=2;g.strokeRect(24,24,w-48,h-48);
  g.fillStyle='rgba(184,137,58,.35)';
  for(let i=0;i<5;i++){const cy=90+i*85;g.beginPath();g.moveTo(w/2,cy-34);g.lineTo(w/2+44,cy);g.lineTo(w/2,cy+34);g.lineTo(w/2-44,cy);g.closePath();g.fill();}
  stains(g,w,h,18,.3);noiseFx(g,w,h,30);});
const clockTex=()=>T('clock',128,128,(g,w,h)=>{
  g.fillStyle='#c9b98c';g.beginPath();g.arc(64,64,60,0,7);g.fill();g.strokeStyle='#2a1a08';g.lineWidth=4;g.stroke();
  g.lineWidth=3;for(let i=0;i<12;i++){const a=i/12*6.283;g.beginPath();g.moveTo(64+Math.sin(a)*48,64-Math.cos(a)*48);g.lineTo(64+Math.sin(a)*56,64-Math.cos(a)*56);g.stroke();}
  g.lineWidth=5;g.beginPath();g.moveTo(64,64);g.lineTo(64+Math.sin(.4)*30,64-Math.cos(.4)*30);g.stroke();
  g.lineWidth=3;g.beginPath();g.moveTo(64,64);g.lineTo(64+Math.sin(4.1)*44,64-Math.cos(4.1)*44);g.stroke();noiseFx(g,w,h,18);});
const webTex=()=>T('web',128,128,(g,w,h)=>{
  g.clearRect(0,0,w,h);g.strokeStyle='rgba(220,220,220,.55)';g.lineWidth=1;
  for(let i=0;i<=6;i++){const a=i/6*Math.PI/2;g.beginPath();g.moveTo(0,0);g.lineTo(Math.cos(a)*128,Math.sin(a)*128);g.stroke();}
  for(let r=18;r<130;r+=18){g.beginPath();for(let i=0;i<=6;i++){const a=i/6*Math.PI/2,rr=r*(0.9+Math.random()*.2),x=Math.cos(a)*rr,y=Math.sin(a)*rr;if(i)g.lineTo(x,y);else g.moveTo(x,y);}g.stroke();}});
const faceTex=()=>T('face',512,640,(g,w,h)=>{
  const gr=g.createRadialGradient(w/2,h*.45,30,w/2,h*.5,w*.75);gr.addColorStop(0,'#dcd6c6');gr.addColorStop(1,'#625b50');
  g.fillStyle=gr;g.fillRect(0,0,w,h);
  g.strokeStyle='rgba(40,40,40,.55)';g.lineWidth=1.4;
  for(let i=0;i<46;i++){let x=rnd(0,w),y=rnd(0,h);g.beginPath();g.moveTo(x,y);for(let k=0;k<5;k++){x+=rnd(-26,26);y+=rnd(6,28);g.lineTo(x,y);}g.stroke();}
  [-1,1].forEach(s=>{g.save();g.translate(w/2+s*102,h*.36);g.rotate(s*.28);
    const eg=g.createRadialGradient(0,0,4,0,0,76);eg.addColorStop(0,'#000');eg.addColorStop(.7,'#050505');eg.addColorStop(1,'rgba(20,20,20,0)');
    g.fillStyle=eg;g.beginPath();g.ellipse(0,0,64,98,0,0,7);g.fill();
    g.fillStyle='#e8e8f0';g.beginPath();g.arc(0,8,5,0,7);g.fill();g.restore();
    g.strokeStyle='rgba(20,20,20,.7)';g.lineWidth=5;g.beginPath();g.moveTo(w/2+s*92,h*.36+90);g.lineTo(w/2+s*88,h*.36+200);g.stroke();});
  g.fillStyle='#101010';[-1,1].forEach(s=>{g.beginPath();g.ellipse(w/2+s*14,h*.55,6,15,s*.3,0,7);g.fill();});
  g.save();g.translate(w/2,h*.77);
  g.fillStyle='#000';g.beginPath();g.ellipse(0,0,150,128,0,0,7);g.fill();
  const ey=x=>Math.sqrt(Math.max(0,1-(x/150)*(x/150)))*128;
  g.fillStyle='#e8e2d0';
  for(let i=-6;i<=6;i++){const x=i*21,hh=26+Math.abs(Math.sin(i*2.1))*22;
    g.beginPath();g.moveTo(x-9,-ey(x-9)+3);g.lineTo(x,-ey(x)+hh);g.lineTo(x+9,-ey(x+9)+3);g.fill();
    g.beginPath();g.moveTo(x-9,ey(x-9)-3);g.lineTo(x,ey(x)-hh*.8);g.lineTo(x+9,ey(x+9)-3);g.fill();}
  g.restore();
  stains(g,w,h,10,.25);noiseFx(g,w,h,16);});

// ---------- Cơn bão bên ngoài cửa sổ (mưa, sét, sấm) ----------
const haloTex=()=>T('halo',64,64,(g,w,h)=>{
  const gr=g.createRadialGradient(32,32,0,32,32,32);
  gr.addColorStop(0,'rgba(255,255,255,1)');gr.addColorStop(.35,'rgba(255,255,255,.4)');gr.addColorStop(1,'rgba(255,255,255,0)');
  g.fillStyle=gr;g.fillRect(0,0,w,h);});
const stC=document.createElement('canvas'); stC.width=256; stC.height=192;
const stG=stC.getContext('2d');
const stTex=new THREE.CanvasTexture(stC); stTex.wrapS=THREE.RepeatWrapping;
const stormMat=new THREE.MeshBasicMaterial({map:stTex,fog:false}); stormMat.userData.keep=true;
const stormL=new THREE.PointLight(0x9db8ff,0,45); scene.add(stormL);
const drops=[]; for(let i=0;i<150;i++) drops.push({x:Math.random()*256,y:Math.random()*192,v:260+Math.random()*260,l:7+Math.random()*12});
const trees=[]; for(let i=0;i<15;i++) trees.push({x:i*18+Math.random()*8,h:28+Math.random()*34,w:12+Math.random()*10});
let flashV=0, boltT=0, nextBolt=3.5, thunderIn=-999, thunderNear=false, boltX=60, boltPts=[], stAcc=0;
const cl255=v=>Math.max(0,Math.min(255,Math.round(v)));
function drawStorm(dt){
  const g=stG,w=256,h=192,f=flashV;
  const gr=g.createLinearGradient(0,0,0,h);
  gr.addColorStop(0,'rgb('+cl255(10+f*190)+','+cl255(14+f*200)+','+cl255(26+f*225)+')');
  gr.addColorStop(1,'rgb('+cl255(22+f*170)+','+cl255(30+f*180)+','+cl255(46+f*200)+')');
  g.fillStyle=gr; g.fillRect(0,0,w,h);
  // mây đen trôi
  for(let i=0;i<6;i++){
    const x=((i*58+tt*5)%330)-35, y=14+(i%3)*15;
    g.fillStyle='rgba('+cl255(30+f*170)+','+cl255(36+f*170)+','+cl255(56+f*170)+',.6)';
    g.beginPath(); g.ellipse(x,y,55,15,0,0,7); g.fill();
  }
  // bóng cây, đồi phía xa
  const tc='rgb('+cl255(4+f*50)+','+cl255(6+f*55)+','+cl255(12+f*70)+')';
  g.fillStyle=tc; g.fillRect(0,h-14,w,14);
  trees.forEach(t=>{g.beginPath(); g.moveTo(t.x,h-12); g.lineTo(t.x+t.w/2,h-12-t.h); g.lineTo(t.x+t.w,h-12); g.fill();});
  // tia sét
  if(boltT>.7&&boltPts.length>1){
    g.lineJoin='round';
    g.strokeStyle='rgba(150,170,255,.28)'; g.lineWidth=7;
    g.beginPath(); boltPts.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])); g.stroke();
    g.strokeStyle='rgba(245,248,255,'+Math.min(1,.5+f)+')'; g.lineWidth=2.4;
    g.beginPath(); boltPts.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])); g.stroke();
    const b=boltPts[Math.floor(boltPts.length/2)];
    g.lineWidth=1.4; g.beginPath(); g.moveTo(b[0],b[1]); g.lineTo(b[0]+22,b[1]+26); g.lineTo(b[0]+14,b[1]+50); g.stroke();
  }
  // mưa
  g.strokeStyle='rgba(180,200,235,'+(.38+f*.4)+')'; g.lineWidth=1; g.beginPath();
  for(let i=0;i<drops.length;i++){
    const d=drops[i]; d.y+=d.v*dt; d.x-=d.v*dt*.18;
    if(d.y>h){d.y=-d.l;d.x=Math.random()*(w+40);} if(d.x<-10) d.x+=w+10;
    g.moveTo(d.x,d.y); g.lineTo(d.x-d.l*.18,d.y+d.l);
  }
  g.stroke();
  // lớp hơi nước mờ trên kính
  g.fillStyle='rgba(120,140,180,.07)'; g.fillRect(0,0,w,h);
}
function thunder(near){
  if(!amb||!(state==='play'||state==='scare')) return;
  try{
    const a=ac(), t0=a.currentTime, n=Math.floor(a.sampleRate*4.2), b=a.createBuffer(1,n,a.sampleRate), x=b.getChannelData(0);
    for(let i=0;i<n;i++){const t=i/n; x[i]=(Math.random()*2-1)*Math.pow(1-t,1.25)*(.6+.4*Math.sin(t*30)+.25*Math.sin(t*71));}
    const s=a.createBufferSource(), lp=a.createBiquadFilter(), g=a.createGain(), cp=a.createDynamicsCompressor();
    lp.type='lowpass'; lp.frequency.setValueAtTime(1100,t0); lp.frequency.exponentialRampToValueAtTime(45,t0+3.8);
    g.gain.value=near?9:6.5;
    cp.threshold.value=-12; cp.knee.value=8; cp.ratio.value=14; cp.attack.value=.002; cp.release.value=.25;
    s.buffer=b; s.connect(lp); lp.connect(g); g.connect(cp); cp.connect(a.destination); s.start(t0);
    noise(.35,near?1:.7);                       // tiếng nổ chát lúc sét đánh
    if(near){ noise(.6,.8); tone(70,.7,'sawtooth',.5,30); }
    tone(near?58:44,3.2,'sine',1,18);           // tiếng ầm trầm
    tone(near?95:70,1.4,'square',.28,28);
  }catch(e){}
}
function stormUpdate(dt){
  nextBolt-=dt;
  if(nextBolt<=0){
    nextBolt=state==='menu'?3.5+Math.random()*5.5:6+Math.random()*10; boltT=1; boltX=20+Math.random()*216;
    boltPts=[[boltX,0]]; let bx=boltX,by=0;
    while(by<130){bx+=(Math.random()-.5)*28; by+=10+Math.random()*14; boltPts.push([bx,by]);}
    const near=Math.random()<.6, dly=near?.06+Math.random()*.1:1.0+Math.random()*1.6;   // gần: nổ gần như cùng lúc chớp; xa: trễ 1-2,6 giây
    if(thunderPlay(dly,near)) thunderIn=-999; else{thunderIn=dly; thunderNear=near;}      // chưa có file -> tiếng tổng hợp cũ
    rainSwell(near);
  }
  if(boltT>0){
    boltT=Math.max(0,boltT-dt); const e=1-boltT;
    flashV=RF?.4*Math.max(0,1-e*1.3)
      :(e<.07?1:e<.13?.12:e<.24?.95:e<.34?.25:e<.46?.6:Math.max(0,.55*(1-(e-.46)/.54)));
  } else flashV=0;
  if(thunderIn>-100){thunderIn-=dt; if(thunderIn<=0){thunderIn=-999; thunder(thunderNear);}}
  stormL.intensity=flashV*3;
  stAcc+=dt;
  if(stAcc>(flashV>0?.016:.05)){drawStorm(stAcc); stAcc=0; stTex.needsUpdate=true;}
}
// Manh mối: cứ 3 giây phát sáng một lần
function pulseClues(){
  const ph=(tt%3)/3, p=ph<.05?ph/.05:Math.exp(-(ph-.05)*4.2);
  for(const o of inter){
    if(o.kind!=='clue') continue;
    if(solved[o.idx]){o.mat.emissiveIntensity=.7;o.L.intensity=.45;o.halo.material.opacity=0;}
    else{o.mat.emissiveIntensity=.12+2.6*p;o.L.intensity=.05+2.4*p;o.halo.material.opacity=.95*p;}
  }
}

// ---------- Ma (thực thể) ----------
const ghostRoot=new THREE.Group(); ghostRoot.rotation.order='YXZ'; ghostRoot.position.set(0,-80,0); scene.add(ghostRoot);
const gBody=new THREE.Group(); ghostRoot.add(gBody);
const gArms=[], gHair=[], gMats=[]; let gHeadG, gMouth, gLight;
(function(){
  const skin=new THREE.MeshStandardMaterial({color:0xb4aea0,roughness:.7,emissive:0x2c2822});
  const dk=new THREE.MeshStandardMaterial({color:0x060505,roughness:1,side:THREE.DoubleSide,emissive:0x060606});
  const prof=[[0,.74],[.2,.68],[.7,.5],[1.2,.33],[1.5,.27],[1.78,.4],[2.0,.44],[2.12,.22],[2.24,.1]];
  const lg=new THREE.LatheGeometry(prof.map(p=>new THREE.Vector2(p[1],p[0])),28), pa=lg.attributes.position;
  for(let i=0;i<pa.count;i++){const y=pa.getY(i);if(y<.32){const a=Math.atan2(pa.getZ(i),pa.getX(i));
    pa.setY(i,y+Math.abs(Math.sin(a*5)+Math.sin(a*11+1.3))*.3*(1-y/.32));}}
  lg.computeVertexNormals(); gBody.add(new THREE.Mesh(lg,dk));
  gHeadG=new THREE.Group(); gHeadG.position.set(0,2.4,0.05); gBody.add(gHeadG);
  const hs=new THREE.Mesh(new THREE.SphereGeometry(1,28,24),skin); hs.scale.set(.27,.44,.25); gHeadG.add(hs);
  const ft=faceTex();
  const fm=new THREE.MeshStandardMaterial({map:ft,emissiveMap:ft,emissive:0xffffff,emissiveIntensity:.6,roughness:.8});
  const fs=new THREE.Mesh(new THREE.SphereGeometry(1.012,28,24,Math.PI/2-.95,1.9,Math.PI*.12,Math.PI*.72),fm); fs.scale.set(.27,.44,.25); gHeadG.add(fs);
  const gm=new THREE.MeshBasicMaterial({color:0xe8e8ff});
  [-1,1].forEach(s=>{const e=new THREE.Mesh(new THREE.SphereGeometry(.024,8,6),gm);e.position.set(s*.1,.15,.232);gHeadG.add(e);});
  gMouth=new THREE.Mesh(new THREE.CircleGeometry(.1,20),new THREE.MeshBasicMaterial({color:0x000000}));
  gMouth.position.set(0,-.2,.23); gMouth.scale.set(1.1,.4,1); gHeadG.add(gMouth);
  for(let i=0;i<20;i++){const a=.9+i/19*(Math.PI*2-1.8),len=1.2+Math.random()*.9;
    const g2=new THREE.Group(); g2.position.set(Math.sin(a)*.2,.2,Math.cos(a)*.18-.02);
    const m2=new THREE.Mesh(new THREE.BoxGeometry(.014,len,.014),dk); m2.position.y=-len/2; g2.add(m2);
    g2.rotation.z=Math.sin(a)*.12; gHeadG.add(g2); gHair.push(g2);}
  [-1,1].forEach(s=>{const sh=new THREE.Group(); sh.position.set(s*.42,2.02,.03); gBody.add(sh);
    const up=new THREE.Mesh(new THREE.CylinderGeometry(.045,.035,.95,6),skin); up.position.y=-.475; sh.add(up);
    const el=new THREE.Group(); el.position.y=-.95; sh.add(el);
    const fo=new THREE.Mesh(new THREE.CylinderGeometry(.035,.028,.95,6),skin); fo.position.y=-.475; el.add(fo);
    const hand=new THREE.Group(); hand.position.y=-.95; el.add(hand);
    for(let k=0;k<5;k++){const f=new THREE.Group(); f.rotation.z=(k-2)*.26; hand.add(f);
      const fm2=new THREE.Mesh(new THREE.CylinderGeometry(.012,.004,.36,5),skin); fm2.position.y=-.18; f.add(fm2);}
    gArms.push({sh,el,s});});
  gLight=new THREE.PointLight(0xcfd8ff,0,11); gLight.position.set(0,2.2,.9); gBody.add(gLight);
  const seen=new Set();
  ghostRoot.traverse(o=>{if(o.material&&!seen.has(o.material)){seen.add(o.material);o.material.transparent=true;o.material.opacity=0;gMats.push(o.material);}});
  ghostRoot.scale.set(1.05,1.05,1.05);
})();
function parkGhost(){ ghostSoundStop();$('bars').className='';if(camera.fov!==72){camera.fov=72;camera.updateProjectionMatrix();}gh.phase='idle';gh.alpha=0;gh.peek=0;ghostRoot.position.set(0,-80,0);ghostRoot.rotation.x=0;gLight.intensity=0;}

// ---------- Dựng phòng ----------
const M=(c,e)=>new THREE.MeshStandardMaterial({color:c,roughness:.9,emissive:e||0x000000,side:THREE.DoubleSide});

function disposeRoom(){
  if(!room) return; scene.remove(room); const seen=new Set();
  room.traverse(o=>{ if(o.geometry) o.geometry.dispose();
    const ms=o.material?(Array.isArray(o.material)?o.material:[o.material]):[];
    ms.forEach(mt=>{ if(seen.has(mt)||(mt.userData&&mt.userData.keep))return; seen.add(mt); if(mt.map)mt.map.dispose(); if(mt.emissiveMap)mt.emissiveMap.dispose(); mt.dispose(); }); });
  room=null;
}

function buildRoom(){
  disposeRoom();
  room=new THREE.Group(); scene.add(room);
  obstacles=[]; inter=[]; watchers=[]; spots=[]; doorOpen=false; curSpot=null; fireMat=null;
  const sz=SIZES[door%SIZES.length]; RW=sz[0]; RD=sz[1];
  const hw=RW/2, hd=RD/2, m=(door%2)?-1:1, S1=-m, S2=m;
  scene.fog=new THREE.FogExp2(0x050202,0.04+door*0.004);
  renderer.shadowMap.enabled=HQ; spot.castShadow=HQ; lamp.castShadow=HQ;
  const R=mulberry(door*7919+17);
  const pick=a=>a[Math.floor(R()*a.length)];
  const ryOf=s=>s<0?Math.PI/2:-Math.PI/2;
  const lit=tx=>new THREE.MeshStandardMaterial({map:tx,roughness:.9,side:THREE.DoubleSide});
  const woodM=new THREE.MeshStandardMaterial({map:woodTex(1,1),roughness:.75});
  const woodDark=M(0x1b0f08), woodMid=M(0x3a2415), stone=M(0x3a3836);
  const brass=new THREE.MeshStandardMaterial({color:0xd4af37,metalness:.8,roughness:.3});
  const black=new THREE.MeshBasicMaterial({color:0x000000});
  const fab=c=>new THREE.MeshStandardMaterial({color:c,roughness:1});
  const plane=(w,h,mat,x,y,z,ry,rx)=>{const p=new THREE.Mesh(new THREE.PlaneGeometry(w,h),mat);
    p.position.set(x,y,z);p.rotation.set(rx||0,ry||0,0);p.receiveShadow=true;room.add(p);return p;};
  const box=(sx,sy,sz2,mat,x,y,z,parent,cast)=>{const b=new THREE.Mesh(new THREE.BoxGeometry(sx,sy,sz2),mat);
    b.position.set(x,y,z);b.castShadow=cast!==false;b.receiveShadow=true;(parent||room).add(b);return b;};
  const cyl=(r1,r2,h,seg,mat,x,y,z,parent,cast)=>{const c=new THREE.Mesh(new THREE.CylinderGeometry(r1,r2,h,seg),mat);
    c.position.set(x,y,z);c.castShadow=cast!==false;c.receiveShadow=true;(parent||room).add(c);return c;};
  const addObs=(cx,cz,sx,sz2)=>obstacles.push({x1:cx-sx/2,x2:cx+sx/2,z1:cz-sz2/2,z2:cz+sz2/2});
  const dims=(fx,fz,len,dep)=>Math.abs(fz)>.5?[len,dep]:[dep,len];
  const grp=(x,z,fx,fz)=>{const g=new THREE.Group();g.position.set(x,0,z);g.rotation.y=Math.atan2(fx,fz);room.add(g);return g;};
  const wi=door%5;

  // sàn, trần, tường
  plane(RW,RD,new THREE.MeshStandardMaterial({map:carpetTex(RW/2,RD/2),roughness:1}),0,0,0,0,-Math.PI/2);
  plane(RW,RD,lit(ceilTex(4,5)),0,RH,0,0,Math.PI/2);
  plane(RW,RH,lit(wallTex(wi,RW/2,RH/2)),0,RH/2,-hd);
  plane(RW,RH,lit(wallTex(wi,RW/2,RH/2)),0,RH/2,hd,Math.PI);
  plane(RD,RH,lit(wallTex(wi,RD/2,RH/2)),-hw,RH/2,0,Math.PI/2);
  plane(RD,RH,lit(wallTex(wi,RD/2,RH/2)),hw,RH/2,0,-Math.PI/2);
  // ốp tường gỗ
  const wains=(len,x,z,ry)=>{const gp=new THREE.Group();gp.position.set(x,0,z);gp.rotation.y=ry;room.add(gp);
    box(len,1.1,0.08,woodM,0,0.55,0,gp,false);box(len+0.04,0.07,0.13,woodDark,0,1.13,0.02,gp,false);box(len+0.04,0.16,0.12,woodDark,0,0.08,0.02,gp,false);};
  const seg=hw-1.4;
  wains(seg,-(hw+1.4)/2,-hd+0.04,0); wains(seg,(hw+1.4)/2,-hd+0.04,0); wains(RW,0,hd-0.04,Math.PI);
  wains(RD,-hw+0.04,0,Math.PI/2); wains(RD,hw-0.04,0,-Math.PI/2);
  // dầm trần
  for(let z=-hd+3;z<hd-1;z+=4.5) box(RW,0.22,0.3,woodDark,0,RH-0.11,z,null,false);
  for(let x=-hw+3;x<hw-1;x+=6) box(0.3,0.22,RD,woodDark,x,RH-0.2,0,null,false);

  // đèn chùm
  flameMat=new THREE.MeshBasicMaterial({color:0xffd9a0});
  const iron=M(0x111111);
  const chand=(x,z)=>{const c=new THREE.Group();c.position.set(x,RH,z);room.add(c);
    const chain=new THREE.Mesh(new THREE.CylinderGeometry(.015,.015,.7,6),iron);chain.position.y=-.35;c.add(chain);
    const ring=new THREE.Mesh(new THREE.TorusGeometry(.45,.025,6,18),iron);ring.rotation.x=Math.PI/2;ring.position.y=-.7;c.add(ring);
    for(let i=0;i<6;i++){const a=i/6*6.283,f=new THREE.Mesh(new THREE.SphereGeometry(.05,8,6),flameMat);f.position.set(Math.cos(a)*.45,-.62,Math.sin(a)*.45);c.add(f);}};
  chand(0,RD*0.12); chand(0,-RD*0.28);
  lamp.position.set(0,RH-0.85,RD*0.12); lampB.position.set(0,RH-0.85,-RD*0.28);

  // cửa ra
  const dz=-hd, fm=M(0x1a1008);
  box(0.3,3.3,0.25,fm,-1.1,1.65,dz+0.12,null,false); box(0.3,3.3,0.25,fm,1.1,1.65,dz+0.12,null,false); box(2.5,0.3,0.25,fm,0,3.15,dz+0.12,null,false);
  const glow=new THREE.Mesh(new THREE.PlaneGeometry(1.9,3.0),new THREE.MeshBasicMaterial({color:0xfff1c9}));
  glow.position.set(0,1.5,dz+0.03); room.add(glow);
  doorPivot=new THREE.Group(); doorPivot.position.set(-0.9,0,dz+0.14); room.add(doorPivot);
  box(1.8,2.95,0.1,new THREE.MeshStandardMaterial({map:doorTex(),roughness:.7}),0.9,1.475,0,doorPivot,false);
  [0.5,2.4].forEach(y=>box(0.12,0.22,0.14,M(0x222222),0.03,y,0,doorPivot,false));
  const knob=new THREE.Mesh(new THREE.SphereGeometry(0.07,12,10),brass); knob.position.set(1.6,1.4,0.1); doorPivot.add(knob);
  const cv=document.createElement('canvas'); cv.width=128; cv.height=64; const g=cv.getContext('2d');
  g.fillStyle='#caa24a'; g.fillRect(0,0,128,64); g.strokeStyle='#5a4010'; g.lineWidth=4; g.strokeRect(3,3,122,58);
  g.fillStyle='#2a1a08'; g.font='bold 42px serif'; g.textAlign='center'; g.textBaseline='middle'; g.fillText(String(door+1).padStart(3,'0'),64,34);
  const pm=new THREE.Mesh(new THREE.PlaneGeometry(0.6,0.3),new THREE.MeshStandardMaterial({map:new THREE.CanvasTexture(cv),metalness:.6,roughness:.4}));
  pm.position.set(0.9,2.45,0.06); doorPivot.add(pm);
  doorLight.position.set(0,1.8,dz+1.3); doorLight.intensity=0;
  inter.push({kind:'door',x:0,z:dz,r:2.7});

  // ---- đồ nội thất (các hàm dựng) ----
  const pillar=(x,z)=>{cyl(.38,.38,RH,14,M(0x4a4038),x,RH/2,z);box(1,.25,1,stone,x,.12,z);box(1,.25,1,stone,x,RH-.12,z,null,false);addObs(x,z,.8,.8);};
  const table=(x,z,sx,sz2,h)=>{box(sx,.08,sz2,woodM,x,h,z);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>box(.1,h,.1,woodDark,x+p[0]*(sx/2-.1),h/2,z+p[1]*(sz2/2-.1)));addObs(x,z,sx,sz2);};
  const chair=(x,z,ry)=>{const c=new THREE.Group();c.position.set(x,0,z);c.rotation.y=ry;room.add(c);
    box(.5,.05,.5,woodDark,0,.5,0,c,false);box(.5,.7,.05,woodDark,0,.85,-.22,c,false);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>box(.05,.5,.05,woodDark,p[0]*.22,.25,p[1]*.22,c,false));};
  const shelf=(x,z,fx,fz,len)=>{const gp=grp(x,z,fx,fz);box(len,2.4,.5,woodDark,0,1.2,0,gp);
    const p=new THREE.Mesh(new THREE.PlaneGeometry(len-.1,2.3),lit(bookTex()));p.position.set(0,1.2,.26);gp.add(p);
    const d=dims(fx,fz,len,.5);addObs(x,z,d[0],d[1]);};
  const clock=(x,z,fx,fz)=>{const gp=grp(x,z,fx,fz);box(.65,2.3,.42,woodDark,0,1.15,0,gp);
    box(.5,.5,.02,new THREE.MeshStandardMaterial({map:clockTex()}),0,1.75,.22,gp,false);box(.4,1.0,.02,M(0x0d0805),0,.75,.22,gp,false);
    cyl(.07,.07,.02,12,brass,0,.55,.23,gp,false).rotation.x=Math.PI/2;
    const d=dims(fx,fz,.65,.42);addObs(x,z,d[0],d[1]);};
  const fireplace=(x,z,fx,fz)=>{const gp=grp(x,z,fx,fz);
    box(.35,1.9,.8,stone,-.95,.95,0,gp);box(.35,1.9,.8,stone,.95,.95,0,gp);box(2.5,.4,.9,stone,0,1.95,0,gp);
    box(2,1.6,.5,M(0x050303),0,.8,-.2,gp,false);box(2.6,.12,1.0,woodDark,0,2.2,.05,gp,false);
    const fl=new THREE.Mesh(new THREE.PlaneGeometry(1.1,.8),new THREE.MeshBasicMaterial({color:0xff6a1a,transparent:true,opacity:.85}));
    fl.position.set(0,.55,.1);gp.add(fl);fireMat=fl.material;
    [[-.3,0.25],[.3,-.2]].forEach(p=>{const lg2=cyl(.07,.07,.9,7,woodDark,p[0],.12,.05,gp,false);lg2.rotation.z=Math.PI/2;lg2.rotation.y=p[1];});
    sconceL[0].position.set(x+fx*1.2,1.0,z+fz*1.2);
    const d=dims(fx,fz,2.5,.9);addObs(x,z,d[0],d[1]);};
  const sofa=(x,z,fx,fz,col)=>{const gp=grp(x,z,fx,fz),f=fab(col);
    box(2.4,.4,1,f,0,.3,0,gp);box(2.4,.75,.25,f,0,.78,-.4,gp);box(.25,.6,1,f,-1.08,.55,0,gp);box(.25,.6,1,f,1.08,.55,0,gp);
    box(.95,.18,.8,f,-.5,.55,.05,gp,false);box(.95,.18,.8,f,.5,.55,.05,gp,false);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>box(.08,.12,.08,woodDark,p[0]*1.1,.05,p[1]*.45,gp,false));
    const d=dims(fx,fz,2.4,1);addObs(x,z,d[0],d[1]);};
  const dresser=(x,z,fx,fz)=>{const gp=grp(x,z,fx,fz);box(2.2,1.2,1,woodM,0,.6,0,gp);box(2.3,.07,1.1,woodDark,0,1.23,0,gp,false);
    for(let i=0;i<3;i++){box(.65,.4,.03,woodMid,-.72+i*.72,.8,.51,gp,false);box(.08,.04,.04,brass,-.72+i*.72,.8,.55,gp,false);}
    const d=dims(fx,fz,2.2,1);addObs(x,z,d[0],d[1]);};
  const barrel=(x,z)=>{cyl(.36,.4,.95,12,woodMid,x,.475,z);[.2,.75].forEach(y=>cyl(.41,.41,.05,12,iron,x,y,z,null,false));addObs(x,z,.8,.8);};
  const crate=(x,z,s,ry)=>{const b=box(s,s,s,woodMid,x,s/2,z);b.rotation.y=ry||0;addObs(x,z,s*1.2,s*1.2);};
  const wardrobe=(x,z,fx,fz)=>{const gp=grp(x,z,fx,fz);
    box(1.5,2.8,.95,woodM,0,1.4,0,gp);box(1.64,.14,1.08,woodDark,0,2.86,0,gp,false);box(1.6,.1,1.04,woodDark,0,.05,0,gp,false);
    const dL=box(.72,2.55,.03,woodMid,-.37,1.4,.49,gp,false), dR=box(.72,2.55,.03,woodMid,.37,1.4,.49,gp,false), dS=box(.03,2.55,.04,black,0,1.4,.49,gp,false);
    [-.1,.1].forEach(dx=>box(.04,.2,.04,brass,dx,1.3,.53,gp,false));
    const d=dims(fx,fz,1.5,.95);addObs(x,z,d[0],d[1]);
    const sp={kind:'hide',type:'ward',x,z,r:2.6,fx,fz,hx:x,hz:z,hy:1.5,yaw:Math.atan2(-fx,-fz),ex:x+fx*1.5,ez:z+fz*1.5,gd:2.4,bend:.85,sink:0,doors:[dL,dR,dS]};
    inter.push(sp);spots.push(sp);};
  const bed=(x,z,wallSide,fx,fz,col)=>{const gp=new THREE.Group();gp.position.set(x,0,z);gp.rotation.y=wallSide<0?0:Math.PI;room.add(gp);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>box(.08,.5,.08,woodDark,p[0]*1.1,.25,p[1]*.7,gp,false));
    box(2.3,.12,1.5,woodDark,0,.56,0,gp);box(2.2,.22,1.4,fab(0x6b6358),0,.73,0,gp);
    box(.45,.12,.9,fab(0xcfc6b0),-.85,.9,0,gp,false);box(1.35,.07,1.46,fab(col),.35,.87,0,gp,false);
    box(.1,1.3,1.6,woodDark,-1.2,.95,0,gp);box(.08,.55,1.5,woodDark,1.15,.75,0,gp,false);
    addObs(x,z,2.3,1.5);
    const sp={kind:'hide',type:'bed',x,z,r:2.6,fx,fz,hx:x,hz:z,hy:.32,yaw:Math.atan2(-fx,-fz),ex:x+fx*1.5,ez:z+fz*1.5,gd:2.7,bend:.72,sink:1.3};
    inter.push(sp);spots.push(sp);};
  const painting=(v,x,y,z,ry,pw,ph)=>{const gp=new THREE.Group();gp.position.set(x,y,z);gp.rotation.y=ry;room.add(gp);
    box(pw+.16,ph+.16,.06,M(0x6b5320),0,0,0,gp,false);
    const t=paintTex(v),p=new THREE.Mesh(new THREE.PlaneGeometry(pw,ph),new THREE.MeshStandardMaterial({map:t,emissiveMap:t,emissive:0xffffff,emissiveIntensity:.2,roughness:.8}));
    p.position.z=.04;gp.add(p);};
  const windowAt=(x,y,z,ry,ww,hh)=>{ww=ww||2.0;hh=hh||1.8;const gp=new THREE.Group();gp.position.set(x,y,z);gp.rotation.y=ry;room.add(gp);
    const geo=new THREE.PlaneGeometry(ww,hh),uv=geo.attributes.uv,o=Math.random(),uvW=Math.min(1,(ww/hh)*(192/256));
    for(let i=0;i<uv.count;i++)uv.setX(i,o+uv.getX(i)*uvW);
    const gl=new THREE.Mesh(geo,stormMat);gl.position.z=.02;gp.add(gl);
    box(ww+.24,.1,.14,woodDark,0,hh/2+.05,.04,gp,false);box(ww+.36,.1,.24,woodDark,0,-hh/2-.05,.08,gp,false);
    box(.1,hh+.2,.14,woodDark,-ww/2-.05,0,.04,gp,false);box(.1,hh+.2,.14,woodDark,ww/2+.05,0,.04,gp,false);
    box(.05,hh,.07,woodDark,0,0,.05,gp,false);box(ww,.05,.07,woodDark,0,hh*.12,.05,gp,false);
    const cu=fab(0x3a0c0c);box(.26,hh+.3,.1,cu,-ww/2-.28,0,.09,gp,false);box(.26,hh+.3,.1,cu,ww/2+.28,0,.09,gp,false);};
  const sconceMesh=(x,z,ry)=>{const gp=new THREE.Group();gp.position.set(x,2.3,z);gp.rotation.y=ry;room.add(gp);
    box(.12,.4,.12,M(0x2a1a0a),0,0,.08,gp,false);
    const fl=new THREE.Mesh(new THREE.SphereGeometry(.07,8,6),new THREE.MeshBasicMaterial({color:0xffbb55}));fl.position.set(0,.28,.1);gp.add(fl);};
  const decal=(tx,w2,h2,x,y,z,ry,rx)=>{const p=new THREE.Mesh(new THREE.PlaneGeometry(w2,h2),
    new THREE.MeshStandardMaterial({map:tx,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2,roughness:.4}));
    p.position.set(x,y,z);p.rotation.set(rx||0,ry||0,0);p.receiveShadow=true;room.add(p);};
  const clue=(idx,x,y,z,sx,sy,sz2,lz)=>{
    const mat=new THREE.MeshStandardMaterial({color:0xffcc55,emissive:0xffaa22,emissiveIntensity:1.4});
    box(sx,sy,sz2,mat,x,y,z,null,false);
    const L=clueL[idx];L.color.set(0xffaa44);L.position.set(x,y+0.4,z+lz);
    const halo=new THREE.Sprite(new THREE.SpriteMaterial({map:haloTex(),color:0xffcc66,transparent:true,opacity:0,blending:THREE.AdditiveBlending,depthWrite:false,fog:false}));
    halo.position.set(x,y+.05,z+lz*.4);halo.scale.set(1.6,1.6,1);room.add(halo);
    inter.push({kind:'clue',idx,x,z,r:2.6,mat,L,halo});};

  // ---- bày trí: mỗi phòng một bố cục riêng ----
  sconceL.forEach(l=>l.color.set(0xff9a40));
  sconceL[0].position.set(-hw+1.2,2.4,-hd+5); sconceL[1].position.set(hw-1.2,2.6,hd-6);
  stormL.position.set(0,RH-.7,0);
  const wx=(s,o)=>s*(hw-o);
  const candle=(x,z,h)=>{cyl(.04,.04,.22,8,M(0xddd5c0),x,h+.11,z,null,false);
    const f1=new THREE.Mesh(new THREE.SphereGeometry(.045,8,6),new THREE.MeshBasicMaterial({color:0xffc060}));f1.position.set(x,h+.27,z);room.add(f1);};
  const paintClue=(idx,cx)=>{box(1.7,1.4,.06,M(0x6b5320),cx,2.0,hd-.06,null,false);
    clue(idx,cx,2.0,hd-.1,1.5,1.2,.04,-.7);plane(1.3,1.0,lit(paintTex(3)),cx,2.0,hd-.16,Math.PI);};
  // thảm: mỗi phòng một kích thước
  const rs=[[7,12],[4.5,18],[2.4,26],[3.6,22],[6,24]][door%5];
  const rug=new THREE.Mesh(new THREE.PlaneGeometry(rs[0],rs[1]),new THREE.MeshStandardMaterial({map:rugTex(),roughness:1}));
  rug.rotation.x=-Math.PI/2; rug.position.set(0,.012,0); rug.receiveShadow=true; room.add(rug);

  switch(door%5){

  // ===== PHÒNG 1: SẢNH ĐÓN TIẾP — đại sảnh có bàn ăn dài ở giữa, lò sưởi, cột đá =====
  case 0:{
    [-1,1].forEach(sx=>[-1,1].forEach(sz2=>pillar(sx*(hw-4),sz2*RD*0.2)));
    table(0,-RD*0.04,2.2,4,.8);
    [-1.2,0,1.2].forEach(d=>{chair(-1.6,-RD*0.04+d,Math.PI/2);chair(1.6,-RD*0.04+d,-Math.PI/2);});
    [-1,1].forEach(d=>candle(0,-RD*0.04+d*1.2,.8));
    clock(wx(-1,.4),-RD*0.40,1,0);
    const tx0=wx(-1,1.7),tz0=-RD*0.25;
    table(tx0,tz0,1.3,2.4,.8);chair(tx0,tz0+1.7,-Math.PI/2);
    clue(0,tx0,.88,tz0+.3,.5,.08,.35,0);candle(tx0,tz0-.8,.8);
    sconceMesh(wx(-1,.1),-RD*0.15,ryOf(-1));
    wardrobe(wx(-1,.55),-RD*0.05,1,0);
    shelf(wx(-1,.3),RD*0.15,1,0,3);
    bed(wx(-1,1.4),RD*0.36,-1,0,-1,pick([0x5a1a1a,0x1a3a5a,0x3a5a2a]));
    fireplace(wx(1,.45),-RD*0.40,-1,0);
    shelf(wx(1,.3),-RD*0.20,-1,0,3);
    dresser(wx(1,.8),RD*0.05,-1,0);
    clue(1,wx(1,.8),1.28,RD*0.05,.5,.05,.4,0);
    bed(wx(1,1.4),RD*0.26,1,0,-1,pick([0x4a1a4a,0x5a3a1a,0x1a4a4a]));
    sofa(wx(1,.9),RD*0.37,-1,0,pick([0x5a1212,0x1a3a2a,0x2a2a4a]));
    wardrobe(wx(1,.55),RD*0.47,-1,0);
    wardrobe(4.5,hd-.55,0,-1);
    paintClue(2,-4.5);
    box(1.0,1,1,woodMid,-7.6,.5,hd-.8); addObs(-7.6,hd-.8,1.0,1.0);
    barrel(-(hw-.7),-hd+.8); barrel(-(hw-1.5),-hd+.7); crate(hw-.8,-hd+.8,.9,.4); crate(hw-1.8,-hd+.7,.7,.9);
    painting(0,wx(-1,.05),2.5,RD*0.36,ryOf(-1),1,1.25);
    painting(1,wx(1,.05),3.1,-RD*0.20,ryOf(1),1,1.25);
    painting(2,wx(1,.05),2.3,RD*0.26,ryOf(1),1,1.25);
    painting(0,wx(1,.05),2.3,RD*0.37,ryOf(1),1,1.25);
    painting(2,3.6,2.2,-hd+.05,0,1,1.25);
    painting(0,-2.5,2.2,hd-.05,Math.PI,1,1.25);
    windowAt(wx(-1,.06),2.4,-RD*0.25,ryOf(-1));
    windowAt(wx(1,.06),2.4,4.2,ryOf(1));
    windowAt(-6.5,2.4,-hd+.06,0); windowAt(6.5,2.4,-hd+.06,0);
    windowAt(1.5,2.4,hd-.06,Math.PI);
    sconceMesh(wx(1,.1),RD*0.05,ryOf(1));
    sconceL[1].position.set(wx(-1,.9),2.6,-RD*0.15);
    break;}

  // ===== PHÒNG 2: THƯ VIỆN BỎ HOANG — kệ sách chạy dọc tường, các bàn đọc sách =====
  case 1:{
    sconceL[0].position.set(-hw+1.5,2.4,-1); sconceL[1].position.set(hw-1.5,2.6,6);
    [-9,-5.8,-2.6].forEach(z=>shelf(wx(-1,.3),z,1,0,3));
    [-10.4,-7.2].forEach(z=>shelf(wx(1,.3),z,-1,0,3));
    shelf(wx(1,.3),4.5,-1,0,3);
    shelf(-3.8,-hd+.3,0,1,3); shelf(3.8,-hd+.3,0,1,3);
    table(-3.6,-3,2.6,1.3,.8); chair(-3.6,-4.1,0); chair(-3.6,-1.9,Math.PI);
    clue(0,-3.0,.88,-3,.5,.08,.35,0); candle(-4.6,-3,.8);
    table(3.6,2.5,2.6,1.3,.8); chair(3.6,1.4,0); chair(3.6,3.6,Math.PI);
    clue(1,3.6,.88,2.5,.5,.08,.35,0); candle(4.6,2.5,.8);
    table(-3.6,8,2.6,1.3,.8); chair(-3.6,6.9,0); chair(-3.6,9.1,Math.PI); candle(-3.6,8,.8);
    wardrobe(wx(-1,.55),8.5,1,0);
    bed(wx(-1,1.4),11.5,-1,0,-1,pick([0x3a2a4a,0x1a3a3a,0x4a2a1a]));
    clock(wx(1,.4),8,-1,0);
    wardrobe(wx(1,.55),11.5,-1,0);
    dresser(-4.5,hd-.8,0,-1); clue(2,-4.5,1.28,hd-.8,.5,.05,.4,0);
    wardrobe(5.5,hd-.55,0,-1);
    crate(wx(-1,.8),-hd+.8,.8,.3); crate(wx(1,.9),-hd+.8,.7,.8);
    painting(1,wx(-1,.05),3.1,-5.8,ryOf(-1),1,1.25);
    painting(2,wx(1,.05),3.1,-7.2,ryOf(1),1,1.25);
    painting(0,-4.5,2.3,hd-.05,Math.PI,1,1.25);
    windowAt(wx(-1,.06),2.4,1.5,ryOf(-1)); windowAt(wx(-1,.06),2.4,5.5,ryOf(-1));
    windowAt(wx(1,.06),2.4,-3.5,ryOf(1)); windowAt(wx(1,.06),2.4,.5,ryOf(1));
    windowAt(-7.5,2.4,-hd+.06,0); windowAt(7.5,2.4,-hd+.06,0);
    windowAt(1.5,2.4,hd-.06,Math.PI); windowAt(8.5,2.4,hd-.06,Math.PI);
    sconceMesh(wx(-1,.1),3.5,ryOf(-1)); sconceMesh(wx(1,.1),-1.5,ryOf(1));
    break;}

  // ===== PHÒNG 3: PHÒNG THÍ NGHIỆM — hai dãy bàn thí nghiệm dài, bình chứa phát sáng xanh =====
  case 2:{
    sconceL[1].color.set(0x66ffaa);
    sconceL[0].position.set(-hw+1.5,2.2,-4); sconceL[1].position.set(hw-1.5,2.2,6);
    const gm2=c=>new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:.9});
    const flask=(x,y,z,c)=>cyl(.07,.1,.24,8,gm2(c),x,y+.12,z,null,false);
    table(-4,-4,1.5,7,.95); table(4,-4,1.5,7,.95);
    const fc=[0x66ff99,0x66aaff,0xff6688,0xffe066,0x99ff66,0xcc88ff];
    for(let i=0;i<6;i++){flask(-4.5,.99,-6.8+i*1.2,fc[i]);flask(3.5,.99,-6.8+i*1.2,fc[(i+2)%6]);}
    clue(0,-4,1.03,-3.5,.5,.08,.35,0);
    clue(1,4,1.03,-5,.5,.08,.35,0);
    const tank=(x,z)=>{cyl(.62,.62,.12,16,woodDark,x,.06,z);cyl(.62,.62,.12,16,woodDark,x,2.5,z,null,false);
      cyl(.52,.52,2.4,16,gm2(0x33ff88),x,1.3,z,null,false);addObs(x,z,1.3,1.3);};
    tank(wx(-1,1.4),-hd+1.4); tank(wx(1,1.4),-hd+1.4); tank(wx(-1,1.4),-hd+3);
    barrel(-8,-11); barrel(-7.2,-11.6);
    dresser(wx(-1,.8),3,1,0); clue(2,wx(-1,.8),1.28,3,.5,.05,.4,0);
    shelf(wx(-1,.3),-9,1,0,3); shelf(wx(1,.3),-10,-1,0,3);
    shelf(-4.5,-hd+.3,0,1,3); shelf(4.5,-hd+.3,0,1,3);
    wardrobe(wx(1,.55),-1.5,-1,0); wardrobe(wx(1,.55),5.5,-1,0);
    bed(wx(-1,1.4),8,-1,0,-1,0x2a4a5a);
    wardrobe(wx(-1,.55),12,1,0);
    wardrobe(5,hd-.55,0,-1);
    windowAt(wx(1,.06),2.4,-6,ryOf(1)); windowAt(wx(1,.06),2.4,2,ryOf(1)); windowAt(wx(1,.06),2.4,9,ryOf(1));
    windowAt(wx(-1,.06),2.4,-4.5,ryOf(-1)); windowAt(wx(-1,.06),2.4,-1,ryOf(-1));
    windowAt(-7.5,2.4,-hd+.06,0); windowAt(7.5,2.4,-hd+.06,0);
    windowAt(-4.5,2.4,hd-.06,Math.PI); windowAt(9,2.4,hd-.06,Math.PI);
    sconceMesh(wx(-1,.1),-6.5,ryOf(-1)); sconceMesh(wx(1,.1),-4,ryOf(1));
    break;}

  // ===== PHÒNG 4: HẦM TỐI — hầm rượu: hàng cột, thùng gỗ, cửa sổ thông gió nhỏ trên cao =====
  case 3:{
    sconceL[0].position.set(-6,2.4,-7); sconceL[1].position.set(6,2.4,5);
    [-10,-3.5,3,9.5].forEach(z=>[-4.5,4.5].forEach(x=>pillar(x,z)));
    wardrobe(wx(-1,.55),-6,1,0);
    bed(wx(-1,1.4),.5,-1,0,-1,0x3a2a1a);
    table(-9.6,6.5,1.2,1.2,.9); clue(2,-9.6,.98,6.5,.5,.08,.35,0); candle(-9.2,6,.94);
    shelf(wx(-1,.3),-11.5,1,0,3); shelf(wx(1,.3),-12,-1,0,3);
    wardrobe(wx(1,.55),9,-1,0);
    crate(8.5,-6.5,.9,.2); clue(0,8.5,.95,-6.5,.5,.08,.35,0);
    table(-8,-9,1.4,1.4,.9); clue(1,-8,.98,-9,.5,.08,.35,0);
    [[-9.8,-14.6],[-8.8,-14.8],[9.8,-14.4],[8.8,-14.7],[-9.6,13.6],[-8.5,14.4],[9.6,14.2],[-7.5,10.5],[7.8,1.5],[7.2,-2.5]].forEach(p=>barrel(p[0],p[1]));
    crate(-8,12.3,.9,.5); crate(8.5,12,.9,.2); crate(7.6,-9.5,.8,.7); crate(-7.5,3.5,.8,.1);
    [-11,-4,3,10].forEach(z=>{windowAt(wx(-1,.06),3.3,z,ryOf(-1),2,.6);windowAt(wx(1,.06),3.3,z,ryOf(1),2,.6);});
    windowAt(-6.5,3.2,-hd+.06,0,2,.6); windowAt(6.5,3.2,-hd+.06,0,2,.6);
    sconceMesh(wx(-1,.1),-3,ryOf(-1)); sconceMesh(wx(1,.1),4,ryOf(1));
    painting(1,3.6,2.2,-hd+.05,0,1,1.25);
    break;}

  // ===== PHÒNG 5: PHÒNG CUỐI CÙNG — đại điện lộng lẫy, hai hàng cột, tượng đá, cửa sổ cao sát trần =====
  case 4:{
    [-11,-4,3,10].forEach(z=>[-5.5,5.5].forEach(x=>pillar(x,z)));
    const statue=(x,z)=>{box(1,.6,1,stone,x,.3,z);cyl(.28,.4,1.9,10,M(0x2a2a2e),x,1.55,z);
      const h2=new THREE.Mesh(new THREE.SphereGeometry(.24,12,10),M(0x2a2a2e));h2.position.set(x,2.65,z);h2.castShadow=true;room.add(h2);addObs(x,z,1,1);};
    statue(-3.6,-hd+1.3); statue(3.6,-hd+1.3);
    wardrobe(wx(-1,.55),-8,1,0);
    table(wx(-1,1.6),0,1.2,2.4,.8); clue(0,wx(-1,1.6),.88,0,.5,.08,.35,0); candle(wx(-1,1.6),-.9,.8);
    bed(wx(-1,1.4),6,-1,0,-1,0x4a1a1a);
    sofa(wx(-1,.9),12.5,1,0,0x3a1a2a);
    fireplace(wx(1,.45),-hd+2.4,-1,0);
    dresser(wx(1,.8),-1,-1,0); clue(1,wx(1,.8),1.28,-1,.5,.05,.4,0);
    wardrobe(wx(1,.55),6,-1,0);
    bed(wx(1,1.4),13,1,0,-1,0x1a3a4a);
    wardrobe(6,hd-.55,0,-1); paintClue(2,-3);
    [-12,-4,3,9].forEach(z=>windowAt(wx(-1,.06),2.1,z,ryOf(-1),2.4,2.6));
    [-9,-4,3,9].forEach(z=>windowAt(wx(1,.06),2.1,z,ryOf(1),2.4,2.6));
    windowAt(-8.5,2.1,-hd+.06,0,2.4,2.6); windowAt(8.5,2.1,-hd+.06,0,2.4,2.6);
    windowAt(-8,2.1,hd-.06,Math.PI,2.4,2.6); windowAt(9.5,2.1,hd-.06,Math.PI,2.4,2.6);
    sconceMesh(wx(-1,.1),-6,ryOf(-1)); sconceMesh(wx(1,.1),-6.5,ryOf(1));
    break;}
  }
  sconceMesh(-1.9,-hd+.1,0); sconceMesh(1.9,-hd+.1,0);

  // mạng nhện
  [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>{const w2=new THREE.Mesh(new THREE.PlaneGeometry(1.5,1.5),
    new THREE.MeshBasicMaterial({map:webTex(),transparent:true,depthWrite:false,side:THREE.DoubleSide}));
    w2.position.set(p[0]*(hw-.6),RH-.8,p[1]*(hd-.6));w2.rotation.y=Math.atan2(-p[0],-p[1]);room.add(w2);});

  // vết máu, dấu tay, chữ viết bằng máu, giấy rơi
  for(let i=0;i<4;i++) decal(bloodTex(),rnd(1.2,2.2),rnd(1.2,2.2),rnd(-hw+3,hw-3),.014+i*.001,rnd(-hd+4,hd-4),0,-Math.PI/2);
  decal(handTex(),.9,.9,-5.3,1.4,-hd+.02,0);
  decal(handTex(),.9,.9,5.3,1.4,-hd+.02,0);
  decal(msgTex(MSG[door%5]),3.0,.6,0,3.65,-hd+.02,0);
  const paperM=new THREE.MeshStandardMaterial({color:0xcfc6a8,roughness:1});
  for(let i=0;i<14;i++){const p=new THREE.Mesh(new THREE.PlaneGeometry(.28,.38),paperM);
    p.rotation.set(-Math.PI/2,0,rnd(0,6.3));p.position.set(rnd(-hw+2,hw-2),.02+i*.0005,rnd(-hd+3,hd-3));room.add(p);}
  // ghế đổ
  const tc=new THREE.Group();tc.position.set(-2*m,0.2,RD*0.22);tc.rotation.set(0.1,rnd(0,3),1.45);room.add(tc);
  box(.5,.05,.5,woodDark,0,0,0,tc,false);box(.5,.6,.05,woodDark,0,.3,-.22,tc,false);

  // đôi mắt trong bóng tối
  const eyeMat=new THREE.MeshBasicMaterial({color:0xff2020});
  const spotsE=[[-hw+.6,3.5,-hd+3],[hw-.6,3.5,-hd+3],[-hw+.6,3.6,hd-3],[hw-.6,3.6,hd-3],[0,3.7,-hd+.6],[-hw+.6,3.3,0],[hw-.6,3.3,-2],[0,3.7,hd-.6]];
  const nW=Math.min(2+door,spotsE.length);
  for(let i=0;i<nW;i++){const s=spotsE[(i*3+door)%spotsE.length];const gp=new THREE.Group();gp.position.set(s[0],s[1],s[2]);
    [-0.2,0.2].forEach(dx=>{const e=new THREE.Mesh(new THREE.SphereGeometry(.07,8,6),eyeMat);e.scale.set(1.4,.8,.5);e.position.x=dx;gp.add(e);});
    room.add(gp);watchers.push({g:gp,t:rnd(0,20),off:rnd(0,6)});}
  resetDust();
}
function refreshClues(){
  inter.forEach(o=>{ if(o.kind==='clue' && solved[o.idx]){
    o.mat.color.set(0x55ff88); o.mat.emissive.set(0x22aa55); o.L.color.set(0x55ff88); }});
}

// ---------- Âm thanh ----------
let AC, droneG; const ac=()=>AC||(AC=new (window.AudioContext||window.webkitAudioContext)());
function tone(f,d,type,v,f2){try{const a=ac(),o=a.createOscillator(),g=a.createGain();o.type=type||'sine';
  o.frequency.setValueAtTime(f,a.currentTime);if(f2)o.frequency.exponentialRampToValueAtTime(f2,a.currentTime+d);
  g.gain.setValueAtTime(v||.15,a.currentTime);g.gain.exponentialRampToValueAtTime(.001,a.currentTime+d);
  o.connect(g).connect(a.destination);o.start();o.stop(a.currentTime+d);}catch(e){}}
function noise(d,v){try{const a=ac(),n=Math.floor(a.sampleRate*d),b=a.createBuffer(1,n,a.sampleRate),x=b.getChannelData(0);
  for(let i=0;i<n;i++)x[i]=(Math.random()*2-1)*(1-i/n);const s=a.createBufferSource(),g=a.createGain();
  g.gain.value=v;s.buffer=b;s.connect(g).connect(a.destination);s.start();}catch(e){}}
const sGood=()=>{tone(660,.15,'sine',.15);setTimeout(()=>tone(990,.3,'sine',.15),120);};
const sBad=()=>{tone(160,.4,'sawtooth',.2,60);noise(.3,.25);};
function scream(){
  try{const a=ac(),t0=a.currentTime;
    const mk=(type,f0,f1,vol,dur)=>{const o=a.createOscillator(),g=a.createGain();o.type=type;
      o.frequency.setValueAtTime(f0,t0);o.frequency.exponentialRampToValueAtTime(f1,t0+.35);
      const lfo=a.createOscillator(),lg=a.createGain();lfo.frequency.value=11;lg.gain.value=f1*.08;lfo.connect(lg);lg.connect(o.frequency);lfo.start(t0);lfo.stop(t0+dur);
      g.gain.setValueAtTime(.0001,t0);g.gain.exponentialRampToValueAtTime(vol,t0+.04);g.gain.setValueAtTime(vol,t0+dur*.6);g.gain.exponentialRampToValueAtTime(.001,t0+dur);
      const ws=a.createWaveShaper(),c=new Float32Array(256);for(let i=0;i<256;i++){c[i]=Math.tanh((i/128-1)*4);}ws.curve=c;
      o.connect(ws);ws.connect(g);g.connect(a.destination);o.start(t0);o.stop(t0+dur);};
    mk('sawtooth',300,1250,.35,2.3); mk('square',450,1800,.16,2.1); mk('sawtooth',90,240,.3,2.0);
    noise(1.8,.5); tone(40,1.2,'sine',.6,25);
  }catch(e){}
}
let amb=false;
function ambience(){
  try{const a=ac(); if(a.resume)a.resume(); if(amb)return; amb=true;
    const mk=(f,type,vol)=>{const o=a.createOscillator(),g=a.createGain(),lp=a.createBiquadFilter();o.type=type;o.frequency.value=f;
      lp.type='lowpass';lp.frequency.value=170;g.gain.value=vol;o.connect(lp);lp.connect(g);g.connect(a.destination);o.start();return g;};
    const g1=mk(46,'sawtooth',.05); mk(49.3,'sawtooth',.04);
    const lfo=a.createOscillator(),lg=a.createGain();lfo.frequency.value=.13;lg.gain.value=.03;lfo.connect(lg);lg.connect(g1.gain);lfo.start();
    const n=a.sampleRate*3,b=a.createBuffer(1,n,a.sampleRate),x=b.getChannelData(0);for(let i=0;i<n;i++)x[i]=Math.random()*2-1;
    const s=a.createBufferSource();s.buffer=b;s.loop=true;const bp=a.createBiquadFilter();bp.type='bandpass';bp.frequency.value=400;bp.Q.value=.6;
    const wg=a.createGain();wg.gain.value=.022;s.connect(bp);bp.connect(wg);wg.connect(a.destination);s.start();
    const od=a.createOscillator(),dl=a.createBiquadFilter();droneG=a.createGain();droneG.gain.value=0;od.type='sawtooth';od.frequency.value=62;
    dl.type='lowpass';dl.frequency.value=260;od.connect(dl);dl.connect(droneG);droneG.connect(a.destination);od.start();
    stormAudioLoad(a); stepAudioLoad(a); ghostAudioLoad(a); catchAudioLoad(a);
  }catch(e){}
}
// ---------- Tiếng khi ma bắt được (faaahhhh.mp3, ~1,7 giây; file rất to nên giảm còn CATCH_VOL) ----------
const CATCH_SRC="__CATCH__", CATCH_VOL=.6;
let catchBuf=null, catchLoading=false;
function catchAudioLoad(a){ if(!CATCH_SRC||catchBuf||catchLoading) return; catchLoading=true; decodeBuf(a,CATCH_SRC).then(b=>{catchBuf=b;}).catch(()=>{}); }
function catchSound(){
  if(!catchBuf) return false;
  try{ const a=ac(); if(a.state==='suspended'&&a.resume) a.resume();
    const g=a.createGain(), s=a.createBufferSource(); s.buffer=catchBuf; g.gain.value=CATCH_VOL;
    s.connect(g).connect(a.destination); s.start(); return true; }catch(e){ return false; }
}
// ---------- Tiếng ma (tiengma.mp3): phát 1 lần ~6 giây lúc ma xuất hiện, vào nhỏ dần rồi tắt ----------
const GHOST_SRC="__GHOST__", GH_DUR=6.2, GH_VOL=.8;
let ghBuf=null, ghLoading=false, ghSrc=null, ghGain=null;
function ghostAudioLoad(a){ if(!GHOST_SRC||ghBuf||ghLoading) return; ghLoading=true; decodeBuf(a,GHOST_SRC).then(b=>{ghBuf=b;}).catch(()=>{}); }
function ghostSoundStop(){
  try{ if(ghSrc&&ghGain){ const a=ac(),t=a.currentTime; ghGain.gain.cancelScheduledValues(t); ghGain.gain.setValueAtTime(ghGain.gain.value,t); ghGain.gain.linearRampToValueAtTime(0,t+.5); ghSrc.stop(t+.55); } }catch(e){}
  ghSrc=null; ghGain=null;
}
function ghostSound(){
  if(!ghBuf) return false;
  try{
    ghostSoundStop();
    const a=ac(); if(a.state==='suspended'&&a.resume) a.resume();
    const t=a.currentTime, g=a.createGain(), s=a.createBufferSource(); s.buffer=ghBuf;
    g.gain.setValueAtTime(0,t); g.gain.linearRampToValueAtTime(GH_VOL,t+.2);
    g.gain.setValueAtTime(GH_VOL,t+GH_DUR-1); g.gain.linearRampToValueAtTime(0,t+GH_DUR);
    s.connect(g).connect(a.destination); s.start(t,0,GH_DUR); ghSrc=s; ghGain=g; return true;
  }catch(e){ return false; }
}
// ---------- Bước chân thật (cắt từ tiengchan.mp3); chạy -> nhanh hơn + cao giọng hơn ----------
const STEP_SRC="__STEP__", SCLIPS=__SCLIPS__, STEP_REF=.3, STEP_VOL=1.0;   // SCLIPS: [giây bắt đầu, độ to]
let stBuf=null, stepLoading=false, lastStep=-1;
function stepAudioLoad(a){ if(!STEP_SRC||stBuf||stepLoading) return; stepLoading=true; decodeBuf(a,STEP_SRC).then(b=>{stBuf=b;}).catch(()=>{}); }
function footstep(run){
  if(!stBuf){ noise(.07,.08); tone(70,.09,'sine',.1,40); return; }   // chưa có file -> tiếng tổng hợp cũ
  try{
    const a=ac(); let i; do{ i=Math.floor(Math.random()*SCLIPS.length); }while(i===lastStep&&SCLIPS.length>1); lastStep=i;
    const c=SCLIPS[i], iv=run?.32:.5, rate=(run?1.18:1)*(1+(Math.random()-.5)*.06);
    const dur=Math.min(.5,iv*1.4*rate), wall=dur/rate, t=a.currentTime;
    const v=Math.max(.5,Math.min(2.5,STEP_REF/c[1]))*STEP_VOL*(run?1.1:1);   // cân lại độ to cho các bước đều nhau
    const g=a.createGain(), s=a.createBufferSource(); s.buffer=stBuf; s.playbackRate.value=rate;
    g.gain.setValueAtTime(0,t); g.gain.linearRampToValueAtTime(v,t+.004);
    g.gain.setValueAtTime(v,t+Math.max(.01,wall-.08)); g.gain.linearRampToValueAtTime(0,t+wall);
    s.connect(g).connect(a.destination); s.start(t,Math.max(0,c[0]-.01),dur);
  }catch(e){}
}
/*STORM-AUDIO-BEGIN*/
// ---------- Bão: mưa + sấm thật (cắt từ tiengsamset.mp3, tiếng nổ căn khớp tia chớp) ----------
const THUNDER_SRC="__THUNDER__", RAIN_SRC="__RAIN__";
const TCLIPS=__TCLIPS__;            // {n,k:'crack'|'roll',s:bắt đầu trong file,d:độ dài,c:thời điểm tiếng nổ trong clip}
const RAIN_VOL=.45;
let thBuf=null, rainBuf=null, thBus=null, rainG=null, swellG=null, rainWant=false, rainTgt=0, lastClip=-1, stormLoading=false;
function b64buf(u){const s=atob(u.slice(u.indexOf(',')+1)),b=new Uint8Array(s.length);for(let i=0;i<s.length;i++)b[i]=s.charCodeAt(i);return b.buffer;}
function decodeBuf(a,uri){return new Promise((ok,no)=>{try{const p=a.decodeAudioData(b64buf(uri),ok,no);if(p&&p.catch)p.catch(no);}catch(e){no(e);}});}
function stormAudioLoad(a){
  if(stormLoading) return; stormLoading=true;
  if(THUNDER_SRC&&TCLIPS.length) decodeBuf(a,THUNDER_SRC).then(b=>{thBuf=b;}).catch(()=>{});
  if(RAIN_SRC) decodeBuf(a,RAIN_SRC).then(b=>{rainBuf=b;rainStart(a);}).catch(()=>{});
}
function rainStart(a){
  if(rainG||!rainBuf) return;
  rainG=a.createGain(); rainG.gain.value=rainTgt; swellG=a.createGain();
  const lp=a.createBiquadFilter(); lp.type='lowpass'; lp.frequency.value=7000; lp.Q.value=.4;      // nghe qua cửa sổ: bớt chói
  lp.connect(swellG); swellG.connect(rainG); rainG.connect(a.destination);
  [[0,-.55],[rainBuf.duration*.43,.55]].forEach(p=>{                      // 2 lớp lệch pha chia trái/phải cho có độ rộng
    const s=a.createBufferSource(); s.buffer=rainBuf; s.loop=true;
    if(a.createStereoPanner){const pn=a.createStereoPanner(); pn.pan.value=p[1]; s.connect(pn); pn.connect(lp);} else s.connect(lp);
    s.start(0,p[0]);
  });
}
function rainUpdate(){                // gọi mỗi khung hình: mưa chỉ nghe khi đang chơi, nhỏ lại khi ma xuất hiện
  const want=(state==='play'||state==='scare'||state==='menu'), tgt=want?(gh.phase!=='idle'&&state!=='menu'?RAIN_VOL*.55:RAIN_VOL*(state==='menu'?.85:1)):0;
  rainWant=want;
  if(tgt!==rainTgt){rainTgt=tgt; if(rainG&&AC) rainG.gain.setTargetAtTime(tgt,AC.currentTime,.7);}
}
function rainSwell(near){             // mưa/gió dâng nhẹ ngay lúc chớp, rồi dịu lại
  if(!swellG||!AC||!rainWant) return;
  const t=AC.currentTime; swellG.gain.setTargetAtTime(near?1.35:1.15,t,.12); swellG.gain.setTargetAtTime(1,t+1.4,.9);
}
function thunderBus(a){
  if(thBus) return thBus;
  const c=a.createDynamicsCompressor(); c.threshold.value=-10; c.knee.value=10; c.ratio.value=6; c.attack.value=.003; c.release.value=.3;
  c.connect(a.destination); return thBus=c;
}
// delay = số giây từ lúc tia chớp tới lúc tiếng NỔ vang lên. Lên lịch bằng đồng hồ âm thanh nên tiếng nổ rơi đúng mốc.
// Trả về false nếu chưa có file (khi đó dùng tiếng tổng hợp cũ).
function thunderPlay(delay,near){
  if(!thBuf||!(state==='play'||state==='scare'||state==='menu')) return false;
  try{
    const a=ac(); if(a.state==='suspended'&&a.resume) a.resume();
    // gần: clip nổ gắt. xa: ưu tiên clip sấm cuộn, thỉnh thoảng dùng clip nổ nhưng làm mờ
    let pool=[]; TCLIPS.forEach((c,i)=>{ if(i===lastClip) return; if(near?c.k==='crack':(c.k==='roll'||Math.random()<.35)) pool.push(i); });
    if(!pool.length) pool=TCLIPS.map((c,i)=>i);
    const i=pool[Math.floor(Math.random()*pool.length)]; lastClip=i; const c=TCLIPS[i];
    const now=a.currentTime; let when=now+delay-c.c, off=c.s, dur=c.d;
    if(when<now){const sk=now-when; off+=sk; dur-=sk; when=now;}          // delay quá ngắn: bỏ bớt đoạn lót đầu clip
    const src=a.createBufferSource(); src.buffer=thBuf;
    const lp=a.createBiquadFilter(); lp.type='lowpass'; lp.frequency.value=near?14000:Math.max(1400,3600-delay*900);   // càng xa càng trầm
    const g=a.createGain(); g.gain.value=near?.95:Math.max(.38,.8-delay*.16);
    src.connect(lp); lp.connect(g); g.connect(thunderBus(a)); src.start(when,off,dur);
    return true;
  }catch(e){return false;}
}
/*STORM-AUDIO-END*/
const WH=['đừng quay lại...','nó đang nhìn bạn','phía sau bạn','đừng nhìn vào bóng tối','chạy đi...','bạn không một mình','nó biết bạn ở đây'];
function whisper(txt){const w=$('whisper');w.textContent=txt||WH[Math.floor(Math.random()*WH.length)];
  w.style.left=(8+Math.random()*60)+'%';w.style.top=(15+Math.random()*60)+'%';w.style.opacity=.8;setTimeout(()=>w.style.opacity=0,2400);noise(1.2,.05);}

// ---------- Tiện ích UI ----------
function banner(t,ms){const b=$('banner');b.textContent=t;b.style.opacity=1;clearTimeout(bannerT);
  bannerT=setTimeout(()=>b.style.opacity=0,ms||2500);}
function updateHud(){
  $('lockbtn').style.display=(state==='play'&&!touchMode)?'block':'none';
  $('tui').style.display=(touchMode&&state==='play')?'block':'none';
  $('lowhp').className=(hp===1&&state==='play')?'pulse':'';
  if(door>=DOORS.length) return;
  const D=DOORS[door];
  $('dn').textContent='Cửa '+(door+1)+'/5';
  $('hp').innerHTML='MẠNG '+'<span style="color:#d01a1a">&#9829;</span>'.repeat(Math.max(hp,0))+'<span style="color:#4a4a4a">&#9829;</span>'.repeat(MAX_HP-Math.max(hp,0));
  $('hn').textContent='Gợi ý: '+hints;
  $('ks').textContent='Chìa khóa: '+D.questions.map((q,i)=>solved[i]?q.digit:'_').join(' · ');
  $('ot').textContent=solved.every(Boolean)?D.order_text:'';
  $('lockbtn').className=shiftLock?'on':''; $('lockbtn').textContent='SL';
  $('lockbtn').style.display=(state==='play'&&!touchMode)?'block':'none';
  $('lowhp').className=(hp===1&&state==='play')?'pulse':'';
}
// Shift Lock kiểu Roblox: chuột bị khóa ở GIỮA màn hình (con trỏ ẩn, hiện tâm ngắm), xoay camera không cần bấm chuột.
// Bấm Shift (hoặc nút ) để bật/tắt. Nếu trình duyệt chặn khóa chuột trong khung nhúng -> dùng nút TAB MỚI mở game ở tab mới.
const inFrame=(function(){try{return window.top!==window;}catch(e){return true;}})();
const isLocked=()=>document.pointerLockElement===canvas;
function lockFail(){
  if(!lockEver) lockBlocked=true;        // chưa từng khóa được -> khung nhúng bị chặn
  setCursor();
  if(!shiftLock||state!=='play'||modalOpen||gh.phase!=='idle') return;   // không đè lên cảnh báo của ma
  const now=performance.now(); if(now-lockMsgT<3500) return; lockMsgT=now;  // promise reject + pointerlockerror -> chỉ báo 1 lần
}
function lockPtr(){try{const p=canvas.requestPointerLock();if(p&&p.catch)p.catch(lockFail);}catch(e){lockFail();}}
function unlockPtr(){expectUnlock=true;try{document.exitPointerLock();}catch(e){}setTimeout(()=>{expectUnlock=false;},250);}
const fakeLock=()=>shiftLock&&!isLocked()&&lockBlocked;
function setCursor(){
  const want=shiftLock&&state==='play'&&!modalOpen;
  const hide=want&&(isLocked()||lockBlocked);
  canvas.style.cursor=hide?'none':'default';
  $('cross').className=hide?'lk':'';
}
function syncLock(){
  const want=shiftLock&&state==='play'&&!modalOpen;
  if(want&&!isLocked()) lockPtr();
  else if(!want&&isLocked()) unlockPtr();
  setCursor();
  if(state!=='menu') updateHud();
}
function toggleSL(){
  shiftLock=!shiftLock; lockFailShown=false; lockMsgT=0; dragging=false;
  banner(shiftLock?'Shift Lock: BẬT — chuột khóa ở giữa màn hình':'Shift Lock: TẮT — giữ chuột trái/phải và kéo để nhìn',1800);
  syncLock(); updateHud();
}
document.addEventListener('pointerlockchange',()=>{
  if(isLocked()){lockEver=true;lockBlocked=false;}
  else if(shiftLock&&!expectUnlock&&state==='play'&&!modalOpen){   // lỡ nhả chuột (Esc): giữ Shift Lock BẬT như Roblox
    banner('Chuột đã nhả. Bấm vào màn hình để khóa lại (Shift để tắt Shift Lock).',2600);}
  setCursor();
});
document.addEventListener('pointerlockerror',lockFail);

// grain
(function(){const gc=$('grain');gc.width=160;gc.height=90;const x=gc.getContext('2d');
  setInterval(()=>{const id=x.createImageData(160,90),d=id.data;for(let i=0;i<d.length;i+=4){const v=Math.random()*255;d[i]=d[i+1]=d[i+2]=v;d[i+3]=70;}x.putImageData(id,0,0);},70);})();

function damage(msg){
  hp--; shake=0.3; sBad();
  const f=$('flash'); f.style.background='#a00'; f.style.opacity=.75; setTimeout(()=>f.style.opacity=0,350);
  banner(msg+'  -1 mạng',2500); updateHud();
  if(hp<=0) gameOver('Bạn gục ngã ở cửa số '+(door+1)+'...\nBạn phải bắt đầu lại từ cửa số 1.');
}
function gameOver(msg){
  state='over'; closeModal(true); syncLock(); updateHud(); parkGhost();
  camera.fov=72; camera.updateProjectionMatrix(); $('scare').style.display='none'; $('flash').style.opacity=0;
  $('overmsg').style.whiteSpace='pre-line'; $('overmsg').textContent=msg;
  $('over').style.display='flex';
}

// ---------- Modal ----------
// Texture giấy nhàu cho bảng câu hỏi (nếp gấp, mảng sáng/tối, vết ố, hạt)
(function(){
  const w=640,h=560,c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');
  const gr=g.createLinearGradient(0,0,w,h);gr.addColorStop(0,'#c6bba1');gr.addColorStop(.5,'#b5a98e');gr.addColorStop(1,'#a69a7d');
  g.fillStyle=gr;g.fillRect(0,0,w,h);
  for(let i=0;i<90;i++){const x=rnd(0,w),y=rnd(0,h);
    g.fillStyle=Math.random()<.5?'rgba(255,250,235,'+rnd(.03,.12)+')':'rgba(40,30,15,'+rnd(.03,.12)+')';
    g.beginPath();g.moveTo(x,y);for(let k=0;k<4;k++)g.lineTo(x+rnd(-100,100),y+rnd(-100,100));g.closePath();g.fill();}
  for(let i=0;i<26;i++){let x=rnd(0,w),y=rnd(0,h),a=rnd(0,6.3);const pts=[[x,y]];
    for(let k=0;k<5;k++){a+=rnd(-.6,.6);x+=Math.cos(a)*rnd(30,70);y+=Math.sin(a)*rnd(30,70);pts.push([x,y]);}
    [[0,0,'rgba(35,25,10,.30)'],[1.5,1.5,'rgba(255,250,235,.28)']].forEach(s=>{
      g.save();g.translate(s[0],s[1]);g.strokeStyle=s[2];g.lineWidth=1.3;g.beginPath();
      pts.forEach((p,k)=>k?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.stroke();g.restore();});}
  stains(g,w,h,10,.13); noiseFx(g,w,h,22);
  const vg=g.createRadialGradient(w/2,h/2,h*.25,w/2,h/2,w*.75);vg.addColorStop(0,'rgba(0,0,0,0)');vg.addColorStop(1,'rgba(50,35,10,.4)');
  g.fillStyle=vg;g.fillRect(0,0,w,h);
  $('box').style.backgroundImage='url('+c.toDataURL('image/jpeg',.88)+')';
})();
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function openModal(){modalOpen=true;syncLock();$('modal').style.display='flex';$('fb').textContent='';
  if(modalMode==='code') setTimeout(()=>$('mi').focus(),30);}
function closeModal(silent){modalOpen=false;$('modal').style.display='none';$('mi').value='';keys={};
  if(!silent) syncLock();}
function openQ(i){
  const q=DOORS[door].questions[i]; modalMode='q'; modalIdx=i;
  $('mt').textContent='Manh mối '+(i+1); $('mq').textContent=q.q; $('b2').style.display='inline-block';
  $('mi').style.display='none'; $('b1').style.display='none';
  optOrder=shuffle([0,1,2,3]); wrongSet={};            // q.o[0] là đáp án đúng
  const box=$('opts'); box.innerHTML=''; box.style.display='flex';
  optOrder.forEach((oi,k)=>{
    const b=document.createElement('button'); b.className='opt';
    const l=document.createElement('b'); l.textContent='ABCD'[k];
    const t=document.createElement('span'); t.textContent=q.o[oi];
    b.appendChild(l); b.appendChild(t); b.onclick=()=>choose(k); box.appendChild(b);
  });
  openModal(); if(hintShown[door+'-'+i]) $('fb').textContent=''+q.hint;
}
function choose(k){
  if(!modalOpen||modalMode!=='q'||wrongSet[k]) return;
  const q=DOORS[door].questions[modalIdx];
  if(optOrder[k]===0){
    solved[modalIdx]=true; sGood(); closeModal(); refreshClues(); updateHud();
    banner('Đúng! Chìa khóa '+(modalIdx+1)+' = '+q.digit+(solved.every(Boolean)?'\nĐã đủ chìa! Hãy ra mở cửa.':''),3000);
  } else {
    wrongSet[k]=true; $('opts').children[k].classList.add('bad'); $('fb').textContent='Sai rồi!';
    damage('Một thực thể tấn công bạn!');
  }
}
function openCode(){
  const D=DOORS[door]; modalMode='code';
  $('mt').textContent='Ổ khóa'; $('mq').textContent='Nhập mật mã '+D.questions.length+' chữ số. '+D.order_text;
  $('b2').style.display='none'; $('opts').style.display='none'; $('mi').style.display=''; $('b1').style.display=''; openModal();
}
function submit(){
  if(modalMode!=='code') return;
  const v=$('mi').value; if(!v.trim()) return;
  const D=DOORS[door];
  const code=D.order.map(i=>D.questions[i].digit).join('');
  if(v.trim()===code){ closeModal(); doorOpen=true; sGood(); tone(70,1.2,'sawtooth',.12,40); banner('Cửa đã mở! Hãy bước vào ánh sáng...',3000); }
  else { $('fb').textContent='Mật mã sai!'; $('mi').value=''; damage('Ổ khóa phóng điện vào bạn!'); }
}
$('b1').onclick=submit; $('b3').onclick=()=>closeModal();
$('b2').onclick=()=>{
  const k=door+'-'+modalIdx, q=DOORS[door].questions[modalIdx];
  if(hintShown[k]){$('fb').textContent=''+q.hint;return;}
  if(hints<=0){$('fb').textContent='Hết lượt gợi ý!';return;}
  hints--; hintShown[k]=true; $('fb').textContent=''+q.hint; updateHud();
};
$('mi').addEventListener('keydown',e=>{if(e.key==='Enter')submit();});

// ---------- Luồng game ----------
function startRoom(){
  solved=[false,false,false]; buildRoom(); hidden=false; spot.intensity=2.1; $('hide').style.display='none';
  camera.position.set(0,1.6,RD/2-2); yaw=0; pitch=0; lampF=1; dark=0; parkGhost();
  ghostTimer=(door===0?38:28)+Math.random()*24; updateHud();
  banner('CỬA '+(door+1)+': '+DOORS[door].name+'\n'+DOORS[door].intro,4500);
}
let inStory=false, storyTm=[];
function storyStop(){storyTm.forEach(clearTimeout); storyTm=[];}
function storyIntro(){            // bảng cốt truyện: tắt nhạc, hiệu ứng + âm thanh lúc chữ hiện ra
  storyStop(); try{musicStop();}catch(e){}
  const hit=()=>{try{tone(95,.6,'sine',.13,55); noise(.18,.07);}catch(e){}};
  $('sgo').disabled=true;
  try{noise(1,.1); tone(48,2.4,'sine',.24,28);}catch(e){}      // tiếng ngân trầm lúc bảng hiện
  storyTm.push(setTimeout(()=>{hit(); try{tone(1400,.5,'sine',.025,500);}catch(e){}},550));
  storyTm.push(setTimeout(()=>{hit(); try{tone(1250,.5,'sine',.025,420);}catch(e){}},2450));
  storyTm.push(setTimeout(()=>{$('sgo').disabled=false; $('sgo').focus(); try{tone(520,.5,'sine',.05,300);}catch(e){}},3500));
}
function showOnly(id){['menu','story','howto','settings','over','win'].forEach(i=>$(i).style.display=(i===id?'flex':'none'));
  inStory=(id==='story'); if(inStory) storyIntro(); else storyStop();}
function resetGame(){musicStop();hp=MAX_HP;hints=HINTS0;door=0;hintShown={};state='play';ambience();playMusicStart();
  camera.fov=72;camera.updateProjectionMatrix();$('scare').style.display='none';
  showOnly(''); startRoom(); syncLock();}
function toMenu(){playMusicStop();state='menu';closeModal(true);syncLock();parkGhost();showOnly('menu');buildRoom();camera.position.set(0,1.6,RD/2-2);yaw=0;pitch=0;musicStart();}
// Trong khung Streamlit (chặn khóa chuột): bấm CHƠI -> mở game ở tab mới để Shift Lock chạy chuẩn. Bị chặn popup thì chơi tại chỗ.
$('start').onclick=()=>{
  if(inFrame){
    try{
      const w=window.open(URL.createObjectURL(new Blob([SRC],{type:'text/html'}))+'#fromframe','_blank');
      if(w){return;}
    }catch(e){}
  }
  showOnly('story');            // bảng cốt truyện trước khi vào game
};
// Tab mới do trang Streamlit mở ra: biến luôn tab cũ thành game (không còn tab thừa), rồi tự đóng tab mới này.
// Nếu trình duyệt không cho thì giữ tab mới, tab cũ để nguyên (không làm trống).
if(!inFrame&&location.hash==='#fromframe'&&window.opener){
  try{
    const top0=window.opener.top;
    top0.location.href=URL.createObjectURL(new Blob([SRC],{type:'text/html'}))+'#takeover';
    let n=0; const iv=setInterval(()=>{
      n++; let ok=false;
      try{ ok=top0.location.href.indexOf('#takeover')>0&&top0.document.readyState==='complete'&&!!top0.document.getElementById('start'); }catch(e){}
      if(ok){ clearInterval(iv); setTimeout(()=>{try{window.close();}catch(e){}},400); }
      else if(n>40) clearInterval(iv);    // ~6s không được -> thôi, giữ nguyên cả hai tab
    },150);
  }catch(e){}
}
function setRF(v){RF=!!v; saveNum('doors_rf',RF?1:0); $('rfchk2').checked=RF;}
$('rfchk2').onchange=()=>setRF($('rfchk2').checked); setRF(RF);
$('warnok').onclick=()=>{$('warn').style.display='none';};
$('tomenu').onclick=toMenu; $('tomenu2').onclick=toMenu;
$('sgo').onclick=()=>{storyStop();resetGame();};
$('how').onclick=()=>showOnly('howto'); $('hback').onclick=()=>showOnly('menu');
// ----- Cài đặt đồ họa (kiểu Roblox: thanh trượt 1-10; 1-5 = Thấp, 6-10 = Cao) -----
function updateSettingsUI(){
  $('qr').value=Q;
  $('ql').textContent='Mức đồ họa: '+Q+' / 10 — '+(Q>=6?'CAO':'THẤP');
  $('qd').textContent=Q>=6
    ?'Cao: bóng đổ động, độ phân giải đầy đủ, nhiễu hạt phim và bụi bay. Đẹp hơn nhưng cần máy khỏe.'
    :'Thấp: kiểu pixel low-poly retro — hình ảnh vuông pixel, texture thô, tắt bóng đổ, nhiễu hạt và bụi. Rất mượt trên máy yếu.';
  $('gLow').style.boxShadow=Q<=5?'0 0 10px #a00':'none'; $('gHigh').style.boxShadow=Q>=6?'0 0 10px #a00':'none';
}
function applyQuality(noBuild){
  HQ=Q>=6;
  renderer.setPixelRatio(pr()); renderer.setSize(STW,STH);
  canvas.style.imageRendering=HQ?'auto':'pixelated';
  renderer.toneMappingExposure=HQ?1.3:1.55;
  [[spot,Q>=9?1024:512],[lamp,Q>=9?512:256]].forEach(a=>{
    if(a[0].shadow.map){a[0].shadow.map.dispose();a[0].shadow.map=null;} a[0].shadow.mapSize.set(a[1],a[1]);});
  $('grain').style.display=HQ?'block':'none'; dust.visible=HQ;
  gMats.forEach(m=>{m.needsUpdate=true;});
  saveNum('doors_q',Q); updateSettingsUI();
  if(!noBuild) buildRoom();
}
$('settingsBtn').onclick=()=>{showOnly('settings');updateSettingsUI();};
$('sback').onclick=()=>showOnly('menu');
$('qr').oninput=()=>{Q=+$('qr').value;updateSettingsUI();};
$('qr').onchange=()=>{Q=+$('qr').value;applyQuality();};
$('qm').onclick=()=>{Q=Math.max(1,Q-1);applyQuality();};
$('qp').onclick=()=>{Q=Math.min(10,Q+1);applyQuality();};
$('gLow').onclick=()=>{Q=3;applyQuality();};
$('gHigh').onclick=()=>{Q=10;applyQuality();};

// ----- Nhạc menu -----
const bgm=new Audio(); bgm.loop=true; bgm.preload='auto'; if(MUSIC_SRC) bgm.src=MUSIC_SRC;
let musicVol=loadNum('doors_vol',60,0,100)/100, fadeI=null;
$('vr').value=Math.round(musicVol*100); $('vv').textContent=Math.round(musicVol*100)+'%';
function fadeTo(v,done){
  clearInterval(fadeI);
  fadeI=setInterval(()=>{const d=v-bgm.volume;
    if(Math.abs(d)<.03){bgm.volume=v;clearInterval(fadeI);if(done)done();}
    else bgm.volume=Math.max(0,Math.min(1,bgm.volume+Math.sign(d)*.03));},40);
}
function musicStart(){
  if(!MUSIC_SRC||state!=='menu') return;
  if(bgm.paused) bgm.volume=0;
  const p=bgm.play();
  const ok=()=>{$('musichint').style.display='none'; if(state==='menu') fadeTo(musicVol); else bgm.pause();};
  const blocked=()=>{$('musichint').style.display='block';};     // trình duyệt chặn tự phát -> chờ người chơi bấm
  if(p&&p.then) p.then(ok).catch(blocked); else ok();
}
function musicStop(){ $('musichint').style.display='none'; fadeTo(0,()=>bgm.pause()); }
// Nhạc nền khi đang chơi (nhỏ lại khi ma xuất hiện)
const pbgm=new Audio(); pbgm.loop=true; pbgm.preload='auto'; if(PLAY_SRC) pbgm.src=PLAY_SRC;
let pduck=1;
function playMusicStart(){ if(!PLAY_SRC||!pbgm.paused) return; pbgm.volume=Math.min(1,musicVol*.8); const p=pbgm.play(); if(p&&p.catch)p.catch(()=>{}); }
function playMusicStop(){ pbgm.pause(); try{pbgm.currentTime=0;}catch(e){} }
$('vr').oninput=()=>{musicVol=+$('vr').value/100;$('vv').textContent=$('vr').value+'%';saveNum('doors_vol',$('vr').value);
  if(!bgm.paused){clearInterval(fadeI);bgm.volume=musicVol;}};
['pointerdown','keydown'].forEach(ev=>addEventListener(ev,()=>{if(state==='menu'&&!inStory&&bgm.paused)musicStart();},true));
['pointerdown','keydown'].forEach(ev=>addEventListener(ev,()=>{try{const a=ac(); if(a.resume)a.resume(); stormAudioLoad(a);}catch(e){}},{capture:true,once:true}));   // nạp tiếng sấm cho menu
function nextRoom(){
  transitioning=true; $('fade').style.opacity=1;
  setTimeout(()=>{
    door++;
    if(door>=DOORS.length){playMusicStop();state='win';syncLock();updateHud();parkGhost();showOnly('win');}
    else startRoom();
    $('fade').style.opacity=0; transitioning=false;
  },900);
}
function toggleHide(sp){
  if(!hidden){
    if(gh.phase!=='idle'&&Math.hypot(gh.x-camera.position.x,gh.z-camera.position.z)<3&&gh.phase==='hunt'){banner('Quá muộn! Ma ở quá gần!',1500);return;}
    hidden=true; curSpot=sp; wardDoors(sp,true); camera.position.set(sp.hx,sp.hy,sp.hz); yaw=sp.yaw; pitch=0; spot.intensity=0;
    $('hide').className=sp.type; $('hide').style.display='block'; noise(.25,.08); tone(90,.2,'square',.05,70);
  } else {
    if(gh.phase!=='idle'){banner('Ma vẫn còn ở đây... đừng ra!',1600);return;}
    hidden=false; wardDoors(curSpot,false); let ex=curSpot.ex,ez=curSpot.ez,k=0;
    while(hit(ex,ez)&&k<4){ex+=curSpot.fx*.5;ez+=curSpot.fz*.5;k++;}
    camera.position.set(ex,1.6,ez); spot.intensity=2.1; $('hide').style.display='none'; curSpot=null; noise(.2,.06);
  }
}
function act(){
  if(hidden){toggleHide();return;}
  if(!cur) return;
  if(cur.kind==='hide') toggleHide(cur);
  else if(gh.phase!=='idle'){banner('Không phải lúc này! Hãy trốn đi!',1500);}
  else if(cur.kind==='clue'){ if(!solved[cur.idx]) openQ(cur.idx); }
  else if(cur.kind==='door'){
    if(doorOpen) return;
    if(solved.every(Boolean)) openCode();
    else banner('Cửa bị khóa. Cần đủ 3 chìa khóa ('+solved.filter(Boolean).length+'/3).',2200);
  }
}

// ---------- Ma: logic ----------
function startGhost(){
  gh.phase='warn'; gh.t=5.2; gh.alpha=0;
  if(modalOpen) closeModal(true), syncLock();
  banner('ĐÈN CHỚP… CÓ THỨ GÌ ĐÓ ĐANG TỚI!\nTRỐN NGAY: tủ hoặc gầm giường (E)',4600);
  tone(90,1.6,'sawtooth',.12,45);
}
function ghostSpawn(){
  // Ma hiện ra Ở XA người chơi: chọn điểm xa nhất trong phòng (giữa 4 cạnh + 4 góc). Người chơi vẫn đi lại bình thường.
  const ax=RW/2-2.5, az=RD/2-2.5;
  const c=[[0,-az],[0,az],[-ax,0],[ax,0],[-ax,-az],[ax,-az],[-ax,az],[ax,az]];
  let best=c[0],bd=-1; c.forEach(p=>{const d=Math.hypot(p[0]-camera.position.x,p[1]-camera.position.z);if(d>bd){bd=d;best=p;}});
  gh.x=best[0]; gh.z=best[1]; gh.phase='reveal'; gh.t0=gh.t=2.2; gh.step=0; gh.alpha=0; gh.shr=false;
  gh.face=Math.atan2(camera.position.x-gh.x,camera.position.z-gh.z);
  if(ghostSound()) gh.shr=true;            // có file tiếng ma -> bỏ tiếng gào tổng hợp
  else{ noise(1.4,.3); tone(70,1.6,'sawtooth',.2,160); }
}
function moveGhost(tx,tz,sp,dt){
  const dx=tx-gh.x,dz=tz-gh.z,d=Math.hypot(dx,dz)||1,s=Math.min(d,sp*dt);
  gh.x+=dx/d*s; gh.z+=dz/d*s; if(d>.05) gh.face=Math.atan2(dx,dz); return d;
}
function caught(){
  if(state!=='play') return;
  state='scare'; gh.phase='scare'; scareT=0; closeModal(true); syncLock();
  const dx=gh.x-camera.position.x, dz=gh.z-camera.position.z, d=Math.hypot(dx,dz)||1;
  gh.ux=dx/d; gh.uz=dz/d; scareYaw=Math.atan2(-gh.ux,-gh.uz); gh.alpha=1;
  $('scare').style.display='block'; $('banner').style.opacity=0; $('prompt').style.display='none';
  ghostSoundStop(); if(!catchSound()) scream();   // có file -> phát tiếng của bạn, thiếu file -> tiếng gào tổng hợp cũ
  shake=.5;
}
function updGhost(dt){
  const P=gh.phase;
  if(P==='idle'){
    ghostTimer-=dt;
    if(ghostTimer<=0&&!transitioning&&state==='play') startGhost();
    return;
  }
  if(P==='warn'){ gh.t-=dt; if(gh.t<=0) ghostSpawn(); return; }
  if(P==='reveal'){
    // Ma chập chờn hiện hình ở xa (người chơi vẫn điều khiển bình thường) -> gào một tiếng -> bắt đầu đuổi
    gh.t-=dt; const e=gh.t0-gh.t;
    gh.alpha=e<1.2?Math.min(1,e/1.2)*(Math.random()<.35?.3:1):1;
    gh.face=Math.atan2(camera.position.x-gh.x,camera.position.z-gh.z);
    if(Math.random()<dt*2) noise(.25,.1);
    if(e>1.2&&!gh.shr){gh.shr=true; tone(900,.9,'sawtooth',.14,260); tone(120,1,'square',.14,50); noise(.9,.3);}
    if(gh.t<=0){gh.phase='hunt'; gh.t=0; gh.step=0;
      noise(1.2,.35); tone(60,1.4,'sawtooth',.22,200); whisper('chạy đi...');
      banner('NÓ ĐANG ĐUỔI THEO BẠN!\nTRỐN NGAY (tủ / gầm giường — E)',3200);}
    return;
  }
  if(P==='hunt'||P==='search') gh.alpha=Math.min(1,gh.alpha+dt*1.4);
  const px=camera.position.x, pz=camera.position.z;
  if(P==='hunt'){
    if(!hidden){
      const d=moveGhost(px,pz,3.6,dt);
      if(d<1.15){caught();return;}
    } else {
      const sp=curSpot, d=moveGhost(sp.x+sp.fx*sp.gd,sp.z+sp.fz*sp.gd,3.6,dt);
      if(d<0.12){gh.phase='search'; gh.t0=gh.t=6+Math.random()*1.5; gh.peek=0; whisper('tôi biết bạn ở đây...');}
    }
    gh.step-=dt; if(gh.step<=0){gh.step=.55; const dd=Math.hypot(gh.x-px,gh.z-pz); tone(45,.25,'sine',Math.min(.5,1/(dd*.3+1)),30); noise(.08,Math.min(.2,.6/(dd+1)));}
  } else if(P==='search'){
    gh.t-=dt; const sp=curSpot;
    gh.x=sp.x+sp.fx*sp.gd; gh.z=sp.z+sp.fz*sp.gd; gh.face=Math.atan2(-sp.fx,-sp.fz);
    const tp=gh.t0*.55, goal=gh.t<tp?1-gh.t/tp:0;
    gh.peek+=(goal-gh.peek)*Math.min(1,dt*3);
    if(Math.random()<dt*1.2) noise(.3,.05);
    if(gh.t<=0){gh.phase='leave'; gh.t=3; tone(60,1.8,'sawtooth',.14,35);}
  } else if(P==='leave'){
    gh.t-=dt; gh.peek=Math.max(0,gh.peek-dt*1.2); const sp=curSpot;
    if(sp) moveGhost(gh.x+sp.fx*6,gh.z+sp.fz*6,2.2,dt);
    gh.alpha=Math.max(0,Math.min(1,gh.t/1.6));
    if(gh.t<=0){parkGhost(); ghostTimer=45+Math.random()*35; banner('Ma đã đi rồi... Bạn có thể ra ngoài.',2800);}
  }
}
function animGhost(dt){
  const act2=gh.phase!=='idle';
  if(!act2){return;}
  const t=tt;
  const hunting=(gh.phase==='hunt'||gh.phase==='scare');
  gMats.forEach(m=>m.opacity=gh.alpha);
  gLight.intensity=gh.alpha*2.4*(0.6+0.4*Math.random());
  if(gh.phase!=='scare'){
    const sp=curSpot;
    const sink=(gh.phase==='search'||gh.phase==='leave')&&sp?sp.sink*gh.peek:0;
    const bend=(gh.phase==='search'||gh.phase==='leave')&&sp?sp.bend*gh.peek:(gh.phase==='reveal'?.65*Math.max(0,gh.t/gh.t0):0);
    ghostRoot.position.set(gh.x,-sink+Math.sin(t*2)*.04,gh.z);
    let da=gh.face-ghostRoot.rotation.y; da=Math.atan2(Math.sin(da),Math.cos(da));
    ghostRoot.rotation.y+=da*Math.min(1,dt*8);
    ghostRoot.rotation.x=bend;
  }
  const tgt=hunting?-1.35:(gh.phase==='reveal'?-.8:-.2);
  gArms.forEach((a,i)=>{a.sh.rotation.x+=((tgt+Math.sin(t*3+i)*.1)-a.sh.rotation.x)*Math.min(1,dt*6);a.el.rotation.x=-.25+Math.sin(t*5+i*2)*.08;});
  gHeadG.rotation.set(Math.sin(t*2.1)*.12,Math.sin(t*1.3)*.2,Math.sin(t*7)*.07+(Math.random()<dt*3?(Math.random()-.5)*.8:0));
  const lunge=gh.phase==='reveal'&&gh.t0-gh.t>3.3;
  if(gh.phase==='scare'||lunge){gHeadG.rotation.z+=(Math.random()-.5)*.5;gHeadG.rotation.y+=(Math.random()-.5)*.4;}
  gHair.forEach((h,i)=>{h.rotation.x=Math.sin(t*2+i)*.12;});
  gMouth.scale.y=(gh.phase==='scare'||lunge)?1.1+Math.abs(Math.sin(t*40))*.5:.35+Math.sin(t*3)*.1+(gh.phase==='search'?gh.peek*.5:0);
}
const sc=$('scare'), scx=sc.getContext('2d');
function drawScare(t){
  const w=sc.width,h=sc.height; scx.clearRect(0,0,w,h);
  if(t<.12||t>2.2||(!RF&&Math.random()<.18)||!CAN.face) return;
  const k=1+Math.min(t,.6)*.9+Math.sin(t*50)*.04, fh=h*1.35*k, fw=fh*512/640;
  scx.fillStyle='rgba(0,0,0,.55)'; scx.fillRect(0,0,w,h);
  scx.save(); scx.translate(w/2+(Math.random()-.5)*w*.04,h*.52+(Math.random()-.5)*h*.04); scx.rotate((Math.random()-.5)*.08);
  scx.drawImage(CAN.face,-fw/2,-fh/2,fw,fh); scx.restore();
  scx.fillStyle='rgba(140,150,175,'+(.08+Math.random()*.16)+')'; scx.fillRect(0,0,w,h);
  scx.fillStyle='rgba(0,0,0,.25)'; for(let y=0;y<h;y+=4) scx.fillRect(0,y,w,1);
}
function updScare(dt){
  scareT+=dt;
  let da=scareYaw-yaw; da=Math.atan2(Math.sin(da),Math.cos(da)); yaw+=da*(1-Math.exp(-dt*16));
  pitch+=(0.18-pitch)*(1-Math.exp(-dt*10));
  const e=Math.min(1,scareT/.25), fd=3.0-1.0*(1-Math.pow(1-e,3));
  ghostRoot.position.set(camera.position.x+gh.ux*fd+(Math.random()-.5)*.05,(Math.random()-.5)*.05,camera.position.z+gh.uz*fd+(Math.random()-.5)*.05);
  ghostRoot.rotation.y=Math.atan2(-gh.ux,-gh.uz); ghostRoot.rotation.x=.8*Math.min(1,scareT/.2);
  camera.fov=72+Math.min(scareT,1.2)*18; camera.updateProjectionMatrix();
  shake=Math.max(shake,.3);
  scareFlashT-=dt; if(scareFlashT<=0){scareFlashT=.06;const f=$('flash');
    if(RF){f.style.transition='opacity .3s';f.style.background='#667';f.style.opacity=.22;}
    else{f.style.transition='none';f.style.background=Math.random()<.4?'#fff':'#8890a0';f.style.opacity=Math.random()<.6?(.3+Math.random()*.6):0;}}
  drawScare(scareT);
  if(scareT>2.6){ const f=$('flash'); f.style.transition='opacity .45s'; gameOver('Con ma đã bắt được bạn...\nBạn phải bắt đầu lại từ cửa số 1.'); }
}

// ---------- Điều khiển ----------
addEventListener('keydown',e=>{
  if(modalOpen){
    if(e.code==='Escape') closeModal();
    else if(modalMode==='q'&&!e.repeat&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&(e.key||'').length===1){
      const k='ABCD'.indexOf(e.key.toUpperCase()); if(k>=0) choose(k);
    }
    return;
  }
  if((e.code==='ShiftLeft'||e.code==='ShiftRight')&&!e.repeat){ if(state==='play'&&!transitioning) toggleSL(); return; }
  keys[e.code]=true;
  if(e.code==='KeyE'&&state==='play'&&!transitioning) act();
  if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(e.code)) e.preventDefault();
});
addEventListener('keyup',e=>{keys[e.code]=false;});
canvas.addEventListener('mousedown',()=>{
  dragging=!shiftLock&&state==='play'&&!modalOpen;
  if(shiftLock&&state==='play'&&!modalOpen&&!isLocked()) lockPtr();
});
canvas.addEventListener('contextmenu',e=>e.preventDefault());
addEventListener('mouseup',()=>dragging=false);
document.documentElement.addEventListener('mouseleave',()=>{mouseIn=false;});
document.addEventListener('mouseleave',()=>{mouseIn=false;});
document.addEventListener('mouseout',e=>{if(!e.relatedTarget)mouseIn=false;});   // con trỏ rời khung/iframe -> ngừng xoay
addEventListener('blur',()=>{mouseIn=false;dragging=false;keys={};});                           // mất focus (bấm ra ngoài iframe) -> ngừng xoay
document.addEventListener('visibilitychange',()=>{mouseIn=false;dragging=false;keys={};});
addEventListener('mousemove',e=>{
  const r=stage.getBoundingClientRect();
  mouseX=(e.clientX-r.left)/r.width*2-1; mouseY=(e.clientY-r.top)/r.height*2-1;
  mouseIn=Math.abs(mouseX)<=1&&Math.abs(mouseY)<=1;
  if(state!=='play'||modalOpen) return;
  // Vuốt sang phải -> quay phải, sang trái -> quay trái (cả khi khóa chuột thật lẫn khi bị trình duyệt chặn)
  if(isLocked()||dragging||fakeLock()){
    if(Math.abs(e.movementX)>250||Math.abs(e.movementY)>250) return;   // Chrome đôi khi báo delta khổng lồ lúc vừa khóa chuột
    yaw-=e.movementX*0.0025; pitch=Math.max(-1.3,Math.min(1.3,pitch-e.movementY*0.0025));
  }
});
addEventListener('resize',fit);
document.addEventListener('fullscreenchange',fit);
$('lockbtn').onclick=()=>{if(state==='play'&&!modalOpen&&!transitioning)toggleSL();};
document.querySelectorAll('#ui button').forEach(b=>b.addEventListener('click',()=>b.blur()));   // nhả focus để Space/Enter không bấm lại nút
function setMute(v){
  MUTED=!!v; saveNum('doors_mute',MUTED?1:0); $('mu').textContent=MUTED?'🔇':'🔊';
  try{ const m=AC&&masters.get(AC); if(m) m.gain.setTargetAtTime(MUTED?0:1,AC.currentTime,.04); }catch(e){}
  bgm.muted=MUTED; pbgm.muted=MUTED;
}
$('mu').onclick=()=>setMute(!MUTED); setMute(MUTED);
$('fs').onclick=()=>{try{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen();}catch(e){}};
if(!document.documentElement.requestFullscreen){ $('fs').style.display='none'; $('mu').style.right='10px'; }   // iPhone không hỗ trợ toàn màn hình

// ----- Điều khiển cảm ứng: cần gạt trái = đi, vuốt phải = nhìn, nút E = tương tác, nút CHẠY = chạy -----
const joy={x:0,y:0}; let touchRun=false, joyId=null, joyOX=0, joyOY=0, lookId=null, lookX=0, lookY=0;
const toUI=(cx,cy)=>{const r=stage.getBoundingClientRect(),k=1280/r.width;return[(cx-r.left)*k,(cy-r.top)*k];};
const joyR=()=>60*stage.getBoundingClientRect().width/1280;
function setTouch(on){
  touchMode=on; document.body.classList.toggle('touch',on);
  if(on&&shiftLock){shiftLock=false;dragging=false;syncLock();}
  $('help').style.display=on?'none':'';
  $('lockbtn').style.display=(!on&&state==='play')?'block':'none'; $('tui').style.display=(on&&state==='play')?'block':'none';
  fit();
}
function stopJoy(){joyId=null;joy.x=joy.y=0;$('joyB').style.display=$('joyK').style.display='none';}
function placeJoy(el,cx,cy){const p=toUI(cx,cy);el.style.left=p[0]+'px';el.style.top=p[1]+'px';el.style.display='block';}
addEventListener('touchstart',()=>{if(!touchMode)setTouch(true);},{capture:true,passive:true});   // lần chạm đầu tiên -> bật giao diện cảm ứng
canvas.addEventListener('touchstart',e=>{
  e.preventDefault();                                   // chặn cuộn trang + chuột giả lập
  if(state!=='play'||modalOpen) return;
  const r=stage.getBoundingClientRect(), mid=r.left+r.width*.5;
  for(const t of e.changedTouches){
    if(t.clientX<mid&&joyId===null){joyId=t.identifier;joyOX=t.clientX;joyOY=t.clientY;placeJoy($('joyB'),joyOX,joyOY);placeJoy($('joyK'),joyOX,joyOY);}
    else if(t.clientX>=mid&&lookId===null){lookId=t.identifier;lookX=t.clientX;lookY=t.clientY;}
  }
},{passive:false});
canvas.addEventListener('touchmove',e=>{
  e.preventDefault();
  for(const t of e.changedTouches){
    if(t.identifier===joyId){
      let dx=t.clientX-joyOX, dy=t.clientY-joyOY; const R=joyR(), d=Math.hypot(dx,dy);
      if(d>R){dx*=R/d;dy*=R/d;}
      joy.x=dx/R; joy.y=dy/R; if(Math.hypot(joy.x,joy.y)<.15){joy.x=joy.y=0;}    // vùng chết
      placeJoy($('joyK'),joyOX+dx,joyOY+dy);
    } else if(t.identifier===lookId){
      if(state==='play'&&!modalOpen){
        const k=.0035*1280/Math.max(1,STW);
        yaw-=(t.clientX-lookX)*k; pitch=Math.max(-1.3,Math.min(1.3,pitch-(t.clientY-lookY)*k));
      }
      lookX=t.clientX; lookY=t.clientY;
    }
  }
},{passive:false});
const tEnd=e=>{for(const t of e.changedTouches){if(t.identifier===joyId)stopJoy(); if(t.identifier===lookId)lookId=null;}};
canvas.addEventListener('touchend',tEnd); canvas.addEventListener('touchcancel',tEnd);
function tBtn(el,down,up){
  el.addEventListener('touchstart',e=>{e.preventDefault();e.stopPropagation();down();},{passive:false});
  ['touchend','touchcancel'].forEach(n=>el.addEventListener(n,e=>{e.preventDefault();if(up)up();}));
}
tBtn($('tE'),()=>{if(state==='play'&&!transitioning)act();});
tBtn($('tRun'),()=>{touchRun=true;$('tRun').classList.add('on');},()=>{touchRun=false;$('tRun').classList.remove('on');});
setTouch(touchMode);

function hit(x,z){for(const b of obstacles){if(x>b.x1-0.35&&x<b.x2+0.35&&z>b.z1-0.35&&z<b.z2+0.35)return true;}return false;}



// ---------- Phông nền menu: tranh lâu đài ma trong rừng + mưa, dơi, mắt phát sáng, sét (nhịp sét dùng chung với hệ thống bão) ----------
const msky=$('msky'), mbg=$('mbg'), mfx=$('mfx'), mfl=$('mfl'), mimg=$('mimg'), mctx=mfx.getContext('2d');
const IMW=849, IMH=420;
const EYES=[[95,60,0],[88,283,0],[72,198,1],[99,200,1],[790,66,1],[808,158,0],[777,296,0],[640,305,0],[752,250,1],[230,288,1],[110,244,0],[648,282,1],[60,300,0],[825,230,0]]
  .map(e=>({x:e[0],y:e[1],c:e[2]?'#ffc840':'#ff2a1a',t:Math.random()*9,p:.6+Math.random()*1.4}));
const BATS=Array.from({length:9},()=>({x:Math.random()*IMW,y:30+Math.random()*150,vx:25+Math.random()*35,ph:Math.random()*6,s:.7+Math.random()*.8}));
const MRAIN=Array.from({length:220},()=>({x:Math.random(),y:Math.random(),v:1.1+Math.random()*.9,l:.025+Math.random()*.03}));
let mBolt=null, mLastBolt=0;
function menuBg(dt,on){
  mbg.style.display=on?'block':'none'; $('hud').style.display=on?'none':'';
  if(!on) return;
  const w=STW,h=STH; if(mfx.width!==w||mfx.height!==h){mfx.width=w;mfx.height=h;}
  const sc=Math.max(w/IMW,h/IMH), ox=(w-IMW*sc)/2, oy=(h-IMH*sc)/2, g=mctx;
  g.clearRect(0,0,w,h);
  const fv=flashV;
  mimg.style.filter='brightness('+(.5+fv*1.0).toFixed(2)+') contrast(1.08)';
  msky.style.opacity=(.94*(1-Math.min(1,fv*1.35))).toFixed(2);          // sét đánh -> trời sáng bừng lên, hết sét -> đen lại
  if(AC&&Math.random()<dt*.22) tone(3600+Math.random()*1800,.05,'sine',.02,6200);   // tiếng dơi rít xa
  mfl.style.opacity=Math.min(.6,fv*.6).toFixed(2);
  // tia sét thêm: mỗi lần sét đánh dựng một đường gấp khúc từ mây xuống
  if(boltT>mLastBolt+.3){ let x=w*(.1+Math.random()*.8), y=0; mBolt=[[x,y]]; while(y<h*(.45+Math.random()*.25)){x+=(Math.random()-.5)*w*.04; y+=h*(.03+Math.random()*.05); mBolt.push([x,y]);} }
  mLastBolt=boltT;
  if(mBolt&&boltT>.72&&fv>.05){ g.save(); g.lineJoin='round'; g.shadowColor='#9db8ff'; g.shadowBlur=18;
    g.strokeStyle='rgba(235,242,255,'+Math.min(1,fv+.2)+')'; g.lineWidth=Math.max(1.5,sc*1.1);
    g.beginPath(); mBolt.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])); g.stroke(); g.restore(); }
  // dơi
  BATS.forEach(b=>{ b.x+=b.vx*dt; b.ph+=dt*11; if(b.x>IMW+20){b.x=-20;b.y=30+Math.random()*150;}
    const X=ox+b.x*sc, Y=oy+(b.y+Math.sin(b.ph*.4)*6)*sc, k=b.s*sc*3.2, f=Math.sin(b.ph);
    g.fillStyle='#04030a'; g.beginPath(); g.moveTo(X,Y);
    g.quadraticCurveTo(X-k*1.2,Y-k*(1.1+f*.8),X-k*2.2,Y+k*.3); g.quadraticCurveTo(X-k*1.1,Y+k*.1,X,Y+k*.6);
    g.quadraticCurveTo(X+k*1.1,Y+k*.1,X+k*2.2,Y+k*.3); g.quadraticCurveTo(X+k*1.2,Y-k*(1.1+f*.8),X,Y); g.fill(); });
  // mắt phát sáng trong rừng (chớp mắt thỉnh thoảng)
  EYES.forEach(e=>{ const v=Math.sin(tt*e.p+e.t); if(v<-.82) return;
    const X=ox+e.x*sc, Y=oy+e.y*sc, d=3.2*sc, r=Math.max(1.4,1.3*sc);
    g.save(); g.shadowColor=e.c; g.shadowBlur=10; g.fillStyle=e.c; g.globalAlpha=.65+.35*Math.max(0,v);
    g.beginPath(); g.arc(X-d,Y,r,0,6.3); g.arc(X+d,Y,r,0,6.3); g.fill(); g.restore(); });
  // mưa
  g.strokeStyle='rgba(175,190,215,.33)'; g.lineWidth=Math.max(1,sc*.5); g.beginPath();
  MRAIN.forEach(r=>{ r.y+=r.v*dt; r.x-=.12*dt; if(r.y>1){r.y=-.05;r.x=Math.random()*1.1;} if(r.x<0)r.x+=1.05;
    g.moveTo(r.x*w,r.y*h); g.lineTo(r.x*w-r.l*w*.12,(r.y+r.l)*h); });
  g.stroke();
}
// Trốn trong tủ: hai cánh cửa 3D trước đây che kín tầm nhìn (camera nằm trong tủ) -> khi trốn, hé hai cánh ra tạo khe hở thật để thấy phòng bên ngoài
function wardDoors(sp,open){
  if(!sp||!sp.doors) return; const [l,r,m]=sp.doors, g=open?.09:0;
  l.position.x=-.37-g; r.position.x=.37+g; m.visible=!open;
}
function update(dt){
  tt+=dt;
  stormUpdate(dt); pulseClues(); rainUpdate();
  const inMenu=(state==='menu');
  if(room) room.visible=!inMenu;
  menuBg(dt,inMenu);
  if(PLAY_SRC&&!pbgm.paused){pduck+=((gh.phase!=='idle'&&state==='play'?.3:1)-pduck)*Math.min(1,dt*2);pbgm.volume=Math.max(0,Math.min(1,musicVol*.8*pduck));}
  for(let i=0;i<DUST;i++){dustPos[i*3+1]+=Math.sin(tt*.6+i)*0.0009+0.0006;dustPos[i*3]+=Math.cos(tt*.4+i*1.7)*0.0007;
    if(dustPos[i*3+1]>RH)dustPos[i*3+1]=0;}
  dustGeo.attributes.position.needsUpdate=true;
  sconceL.forEach((l,i)=>l.intensity=(0.6+0.18*Math.sin(tt*13+i*2.1)*Math.sin(tt*5.3+i))*lampF);
  if(fireMat) fireMat.opacity=.7+.2*Math.sin(tt*17)*Math.sin(tt*7.3);
  animGhost(dt);
  if(state==='scare'){ updScare(dt); return; }
  if(state!=='play') return;
  if(modalOpen&&joyId!==null) stopJoy();
  if(!modalOpen){ if(keys.ArrowLeft) yaw+=1.8*dt; if(keys.ArrowRight) yaw-=1.8*dt; }
  // Shift Lock dự phòng (không khóa được chuột): xoay camera theo vị trí chuột so với tâm khung
  // (khi không khóa được chuột, con trỏ ẩn nhưng vẫn chạm mép màn hình -> chạm mép thì tiếp tục xoay về phía đó)
  if(!modalOpen&&fakeLock()&&mouseIn&&!dragging){
    const eb=.94, f=v=>Math.abs(v)>eb?Math.sign(v)*(Math.abs(v)-eb)/(1-eb):0;
    yaw-=f(mouseX)*2.6*dt; pitch=Math.max(-1.3,Math.min(1.3,pitch-f(mouseY)*1.6*dt));
  }
  let moving=false;
  if(!modalOpen&&!hidden&&!transitioning){
    let f=0,s=0;
    if(keys.KeyW||keys.ArrowUp)f++; if(keys.KeyS||keys.ArrowDown)f--; if(keys.KeyD)s++; if(keys.KeyA)s--;
    if(touchMode&&joyId!==null){f-=joy.y; s+=joy.x;}
    if(f||s){
      moving=true; const run=keys.Space||touchRun, sp=(run?5.2:3.2)*dt, l=Math.hypot(f,s), mag=Math.min(1,l);
      const fx=-Math.sin(yaw),fz=-Math.cos(yaw),rx=Math.cos(yaw),rz=-Math.sin(yaw);
      const dx=(fx*f+rx*s)/l*sp*mag, dzz=(fz*f+rz*s)/l*sp*mag;
      if(!hit(camera.position.x+dx,camera.position.z)) camera.position.x+=dx;
      if(!hit(camera.position.x,camera.position.z+dzz)) camera.position.z+=dzz;
      bob+=dt*(run?12:9);
      stepT-=dt; if(stepT<=0){footstep(run);stepT=run?.32:.5;}
    }
    const zmin=doorOpen?-RD/2-1.5:-RD/2+0.7;
    camera.position.x=Math.max(-RW/2+0.5,Math.min(RW/2-0.5,camera.position.x));
    camera.position.z=Math.max(zmin,Math.min(RD/2-0.5,camera.position.z));
    if(doorOpen&&camera.position.z<-RD/2+0.6) camera.position.x=Math.max(-0.75,Math.min(0.75,camera.position.x));
    if(doorOpen&&camera.position.z<-RD/2-0.3&&!transitioning) nextRoom();
  }
  if(hidden&&curSpot){ yaw=Math.max(curSpot.yaw-.75,Math.min(curSpot.yaw+.75,yaw)); pitch=Math.max(-.35,Math.min(.4,pitch)); }
  if(!hidden) camera.position.y=1.6+(moving?Math.sin(bob)*0.04:0);
  if(doorOpen){ if(doorPivot.rotation.y<1.9) doorPivot.rotation.y=Math.min(1.9,doorPivot.rotation.y+dt*1.5);
    doorLight.intensity=Math.min(1.8,doorLight.intensity+dt*1.5); }

  // mắt trong bóng tối: chỉ hiện khi bạn không nhìn vào
  const fxv=-Math.sin(yaw), fzv=-Math.cos(yaw);
  watchers.forEach(w=>{
    const dx=w.g.position.x-camera.position.x, dzv=w.g.position.z-camera.position.z, d=Math.hypot(dx,dzv)||1;
    const dot=(dx*fxv+dzv*fzv)/d, on=Math.sin(tt*.5+w.off)>-0.3;
    w.g.visible=on&&dot<0.45&&!hidden;
    w.g.children.forEach(e=>e.scale.y=(Math.sin(tt*2+w.off)>0.97)?0.05:0.8);
  });

  // tương tác
  cur=null; let txt='';
  if(hidden){ txt=gh.phase==='idle'?'[E] Ra khỏi chỗ trốn':'Đừng cử động...'; }
  else if(!modalOpen&&!transitioning){
    const px=camera.position.x,pz=camera.position.z; let best=99;
    for(const o of inter){
      if(o.kind==='clue'&&solved[o.idx]) continue;
      if(o.kind==='door'&&doorOpen) continue;
      const dx=o.x-px,dzz=o.z-pz,d=Math.hypot(dx,dzz);
      if(d<o.r&&(dx*fxv+dzz*fzv)/(d||1)>0.35&&d<best){best=d;cur=o;}
    }
    if(cur) txt=cur.kind==='hide'?(cur.type==='bed'?'[E] Chui xuống gầm giường':'[E] Trốn vào tủ'):cur.kind==='door'?(solved.every(Boolean)?'[E] Nhập mật mã':'[E] Cửa (bị khóa)'):'[E] Xem manh mối';
  }
  const p=$('prompt'); p.style.display=txt?'block':'none'; p.textContent=txt;

  // sự kiện ngẫu nhiên + nhịp tim
  const ghostOn=gh.phase!=='idle';
  if(!modalOpen&&!transitioning&&!ghostOn){
    nextFlick-=dt; if(nextFlick<=0){flickT=.5;nextFlick=10+Math.random()*15;tone(120,.5,'sawtooth',.05,60);}
    evT-=dt; if(evT<=0){evT=12+Math.random()*14;tone(rnd(110,240),.8,'sawtooth',.04,rnd(60,100)); if(Math.random()<.6)whisper();}
  }
  hbT-=dt;
  if(hbT<=0){
    if(ghostOn&&gh.phase!=='leave'){const dd=Math.hypot(gh.x-camera.position.x,gh.z-camera.position.z);
      const iv=gh.phase==='warn'?.8:(gh.phase==='search'?.42:.38+.5*Math.min(1,Math.max(0,(dd-2)/12)));
      tone(55,.12,'sine',.4,40);setTimeout(()=>tone(48,.12,'sine',.32,36),150);hbT=iv;shake=Math.max(shake,.012);}
    else if(hp===1){tone(55,.12,'sine',.35,40);setTimeout(()=>tone(48,.12,'sine',.3,36),170);hbT=.85;}
    else hbT=.3;
  }
  if(droneG&&AC){const dd=ghostOn?Math.hypot(gh.x-camera.position.x,gh.z-camera.position.z):99;
    droneG.gain.setTargetAtTime(ghostOn?(.05+.12*Math.max(0,1-dd/18)):0,AC.currentTime,.3);}

  // ánh sáng: tối dần khi ma xuất hiện
  const dtarget=gh.phase==='warn'?.5:(ghostOn?.9:0); dark+=(dtarget-dark)*Math.min(1,dt*3);
  lampF=1; if(flickT>0){flickT-=dt;lampF=Math.random()<.5?.08:1;}
  if(gh.phase==='warn') lampF=(Math.sin(tt*40)>.1&&Math.random()<.55)?1:.04;
  else if(ghostOn) lampF=Math.random()<.1?.6:.05+Math.random()*.08;
  if(RF) lampF=gh.phase==='warn'?.35+.25*Math.sin(tt*2.5):(ghostOn?.12:(flickT>0?.5:1));   // chế độ giảm chớp: đèn mờ/sáng chậm, không nhấp nháy
  // Sét đánh: đèn điện trong phòng tắt phụt đúng 1 nhịp lúc tia chớp rồi sáng lại (giảm chớp: chỉ mờ đi nhẹ)
  if(boltT>0&&(1-boltT)<.22) lampF=Math.min(lampF,RF?.45:.04);
  ambL.intensity=.6*(1-dark*.7)+flashV*1.2;
  lamp.intensity=.8*lampF; lampB.intensity=.65*lampF;
  if(flameMat){const v=Math.max(.15,lampF);flameMat.color.setRGB(v,.85*v,.63*v);}
  if(!hidden) spot.intensity=2.1*(0.93+0.07*Math.sin(tt*23))*(lampF<.5?0.5:1);

  updGhost(dt);
}

let last=performance.now();
function loop(now){
  requestAnimationFrame(loop);
  const dt=Math.min(0.05,(now-last)/1000); last=now;
  update(dt);
  camera.rotation.set(pitch,yaw,Math.sin(tt*.7)*0.004);
  if(shake>0){camera.rotation.z+=(Math.random()-.5)*shake;camera.rotation.x+=(Math.random()-.5)*shake*.4;shake=Math.max(0,shake-dt*.6);}
  renderer.render(scene,camera);
}
applyQuality(true);
buildRoom(); camera.position.set(0,1.6,RD/2-2);
musicStart();
requestAnimationFrame(loop);
})();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# STREAMLIT
# ---------------------------------------------------------------------------
# Khung game luôn 16:9 theo chiều rộng trang
st.markdown(
    """
<style>
.block-container{padding:3.2rem 1rem 0 1rem !important;max-width:100% !important;}
iframe[title="streamlit.components.v1.html"]{
    width:100% !important;height:auto !important;aspect-ratio:16/9;
    max-height:calc(100vh - 4rem);border:0;background:#000;}
</style>
""",
    unsafe_allow_html=True,
)

MENU_BG = "data:image/jpeg;base64,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"

_html = (GAME_HTML.replace("__DATA__", build_data())
         .replace("__MENUBG__", MENU_BG)
         .replace("__MUSIC__", load_mp3(MUSIC_FILE, PLAY_MUSIC_FILE, True))
         .replace("__MUSIC2__", load_mp3(PLAY_MUSIC_FILE))
         .replace("__CATCH__", load_mp3(CATCH_FILE))
         .replace("__GHOST__", load_mp3(GHOST_FILE))
         .replace("__STEP__", load_mp3(STEP_FILE))
         .replace("__SCLIPS__", json.dumps(STEP_CLIPS))
         .replace("__THUNDER__", load_asset(THUNDER_FILE, "audio/mpeg"))
         .replace("__RAIN__", load_asset(RAIN_FILE, "audio/wav"))
         .replace("__TCLIPS__", json.dumps(THUNDER_CLIPS)))
if not load_mp3(MUSIC_FILE, PLAY_MUSIC_FILE, True):
    st.warning(f"Không tìm thấy file nhạc '{MUSIC_FILE}'. Hãy đặt nó cùng thư mục với app.py để có nhạc ở menu.")
if not load_mp3(PLAY_MUSIC_FILE):
    st.warning(f"Không tìm thấy file nhạc '{PLAY_MUSIC_FILE}'. Hãy đặt nó cùng thư mục với app.py để có nhạc nền khi chơi.")
components.html(_html, height=720, scrolling=False)
st.download_button("Tải game (.html) để chơi độc lập", _html, file_name="escape.html", mime="text/html")
