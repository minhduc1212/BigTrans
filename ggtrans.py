from deep_translator import GoogleTranslator, MicrosoftTranslator

# Khởi tạo translator dịch từ tự động nhận diện sang Tiếng Việt
translator = GoogleTranslator(source='auto', target='vi')

text = "The protagonist suddenly transmigrated into a cultivation world."

# Thực hiện dịch
translated_text = translator.translate(text)

print(translated_text) 