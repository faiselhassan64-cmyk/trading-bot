import os, base64, json, io
from PIL import Image, ImageDraw
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def annotate_image(original_bytes, data):
    img = Image.open(io.BytesIO(original_bytes)).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([(0, int(h*0.15)), (w, int(h*0.35))], fill=(255,0,0,60), outline=(255,0,0), width=3)
    draw.text((20, int(h*0.16)), f"مقاومة {data.get('resistance')} - بيع آمن", fill="red")
    y_support = int(h*0.62)
    draw.line([(0, y_support), (w, y_support)], fill="cyan", width=3)
    draw.text((20, y_support-25), f"دعم {data.get('support')}", fill="cyan")
    out = io.BytesIO()
    img.save(out, format="JPEG")
    out.seek(0)
    return out

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    f = await photo.get_file()
    raw = await f.download_as_bytearray()
    b64 = base64.b64encode(raw).decode()
    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":[{"type":"text","text":"حلل الشارت و رجع JSON فيه support,resistance,trend,sell_zone,buy_zone,when_up,when_down,break_up,break_down"},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}])
    try:
        data = json.loads(res.choices[0].message.content)
    except:
        await update.message.reply_text(res.choices[0].message.content)
        return
    annotated = annotate_image(bytes(raw), data)
    caption = f"📊 {data.get('trend')}\n🔵 دعم: {data.get('support')}\n🔴 مقاومة: {data.get('resistance')}\n🟢 يطلع: {data.get('when_up')}\n🔻 ينزل: {data.get('when_down')}"
    await update.message.reply_photo(photo=annotated, caption=caption)

app = ApplicationBuilder().token(os.environ.get("BOT_TOKEN")).build()
app.add_handler(MessageHandler(filters.PHOTO, handle))
app.run_polling()
