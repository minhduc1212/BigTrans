import sys
import translators as ts

# Ensure UTF-8 console output for Windows terminal compatibility
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Define your text
text_to_translate = "我在这里得到了紫色水晶"

try:
    result = ts.translate_text(
        text_to_translate, 
        translator='youdao', 
        from_language='zh-CHS', 
        to_language='vi'
    )
    print(result)
except Exception as e:
    print(f"Error occurred: {e}")