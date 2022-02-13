"""图片套娃
1. 发送  要我一直+{图片}
2. 发送 套娃 {文字1} {图片} {文字2}
文字1和文字2都是可选的
"""
from io import BytesIO
from pathlib import Path

import httpx
from botoy import GroupMsg, S, decorators
from botoy.parser import group as gp
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = str(Path(__file__).parent.absolute() / "msyh.ttc")


def img_gen(inp, word1="要我一直", word2=f"吗"):
    ori = inp.size[0]

    # 输入图
    le = len(word1) + len(word2) + 1
    word_y = 150

    inp_x = le * 100
    ori /= inp_x
    inp_y = int(inp_x * inp.size[1] / inp.size[0])
    inp = inp.resize((inp_x, inp_y), Image.ANTIALIAS)

    # 输出图
    outp_x = inp_x
    outp_y = inp_y + word_y
    outp = Image.new("RGBA", (outp_x, outp_y), (255, 255, 255, 255))
    outp.paste(inp, (0, 0))

    # 贴字
    font = ImageFont.truetype(FONT_PATH, 100)
    outp_draw = ImageDraw.Draw(outp)
    outp_draw.text((0, inp_y), word1, (0, 0, 0, 255), font)
    outp_draw.text(
        (int(outp_x / le * (le - len(word2))), inp_y), word2, (0, 0, 0, 255), font
    )

    # 小图长宽
    outp_small_x = outp_x
    outp_small_y = outp_y
    # 小图位于输出图的方位
    ratio_x = (len(word1) + 0.5) / le
    ratio_y = (outp_y - word_y / 2) / outp_y
    # 小图起始
    last_x = 0
    last_y = 0
    while True:
        # 小图中心坐标
        outp_small_cen_x = int(last_x + outp_small_x * ratio_x)
        outp_small_cen_y = int(last_y + outp_small_y * ratio_y)
        # print(f"outp_small_cen=({outp_small_cen_x},{outp_small_cen_y})")

        outp_small_x = int(outp_small_x / le)
        outp_small_y = int(outp_small_y / le)
        if outp_small_y > outp_small_x:
            outp_small_x = int(outp_small_x / (outp_y / outp_x))
            outp_small_y = int(outp_small_y / (outp_y / outp_x))
        if min(outp_small_x, outp_small_y) < 3:
            break
        outp_small = outp.resize((outp_small_x, outp_small_y), Image.ANTIALIAS)
        # print(f"outp_small=({outp_small_x},{outp_small_y})")

        # 小图左上角坐标
        outp_small_cor_x = int(outp_small_cen_x - outp_small_x / 2)
        outp_small_cor_y = int(outp_small_cen_y - outp_small_y / 2)
        # print(f"outp_small_cor=({outp_small_cor_x},{outp_small_cor_y})\n")

        outp.paste(outp_small, (outp_small_cor_x, outp_small_cor_y))

        last_x = outp_small_cor_x
        last_y = outp_small_cor_y

    outp = outp.resize((int(outp_x * ori), int(outp_y * ori)), Image.ANTIALIAS)
    return outp


def get_pic(pic_url):
    resp_cont = httpx.get(pic_url, timeout=10).content
    pic = Image.open(BytesIO(resp_cont)).convert("RGBA")
    return pic


def yaowoyizhi(pic_url, word1="要我一直", word2="吗"):
    img = img_gen(get_pic(pic_url), word1, word2)
    b = BytesIO()

    img = img.convert("RGB")
    img.save(b, format="JPEG")
    return b


@decorators.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    pic_data = gp.pic(ctx)
    if not pic_data:
        return

    text = pic_data.Content.strip().replace("\r", " ")  # qq出来有时候有这玩意儿
    pic_url = pic_data.GroupPic[0].Url

    pic = None

    if text.startswith("要我一直"):
        pic = yaowoyizhi(pic_url)

    elif text.startswith("套娃"):
        items = [i.strip() for i in text[2:].split(" ") if i]
        if len(items) == 0:
            pic = yaowoyizhi(pic_url)
        elif len(items) == 1:
            pic = yaowoyizhi(pic_url, items[0], "")
        else:
            pic = yaowoyizhi(pic_url, items[0], items[1])

    if pic:
        S.image(pic)
