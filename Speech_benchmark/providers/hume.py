from hume import HumeClient
from hume.models.config import LanguageConfig
import os

API_KEY = os.getenv("r8xUoG25n3jrxrYyn5GHwFqPiWMjmFyXIW72EtptUBDpBaiU")

client = HumeClient(API_KEY)

def transcribe(audio_path):

    try:
        config = LanguageConfig()

        response = client.language.predict(
            config=config,
            file=audio_path
        )

        text = response[0].results.predictions[0].text
        return text

    except Exception as e:
        print("Hume error:", e)
        return ""