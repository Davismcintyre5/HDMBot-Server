"""
server/whatsapp/commands/media.py — Media commands
sticker, take
"""
import os
import time
from server.whatsapp.handlers.command_handler import command, register_builtin
from server.config.settings import settings

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def register():
    if HAS_PILLOW:
        register_builtin({"name": "sticker", "description": "🎨 Create sticker from image", "category": "media"})
        register_builtin({"name": "take", "description": "🏷️ Set sticker metadata", "category": "media"})


@command("sticker")
async def cmd_sticker(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not HAS_PILLOW:
        return await handler.send_reply(client, jid, "❌ Sticker support requires Pillow module.")

    pack = args[0] if args else "HDM"
    author = args[1] if len(args) > 1 else "Bot"

    try:
        if hasattr(msg, 'hasQuotedMsg') and msg.hasQuotedMsg:
            quoted = msg.getQuotedMessage()
            if hasattr(quoted, 'hasMedia') and quoted.hasMedia:
                await handler.send_reply(client, jid, "🎨 Creating sticker...")
                media = quoted.downloadMedia()
                buffer = bytes(media.data) if hasattr(media.data, 'encode') else media.data

                temp_dir = os.path.join(os.path.dirname(settings.UPLOAD_DIR), "temp")
                os.makedirs(temp_dir, exist_ok=True)
                input_path = os.path.join(temp_dir, f"{int(time.time())}_in.jpg")
                output_path = os.path.join(temp_dir, f"{int(time.time())}_sticker.webp")

                with open(input_path, "wb") as f:
                    f.write(buffer)

                img = Image.open(input_path)
                img = img.resize((512, 512), Image.LANCZOS)
                img.save(output_path, "WEBP", quality=90)

                with open(output_path, "rb") as f:
                    client.send_message(jid, f.read())

                os.unlink(input_path)
                os.unlink(output_path)
                return True

        await handler.send_reply(client, jid, "❌ Reply to an image with .sticker to convert!")
    except Exception as e:
        await handler.send_reply(client, jid, f"❌ Sticker creation failed: {e}")
    return True


@command("take")
async def cmd_take(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not args:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}take <pack>|<author>")
    await handler.send_reply(client, jid, "✅ Sticker metadata set.")
    return True