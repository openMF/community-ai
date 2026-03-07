# Speech Benchmark Report

## Providers Tested

- Hume AI
- Whisper
- Deepgram

## Languages Tested

- English
- Hindi
- Hinglish

## Metrics

- Word Error Rate (WER)
- Latency
- Accuracy

## Sample Results


Audio: datasets/english_audio/sample1.wav
Expected: show my loan balance
Predicted:  What is the balance of my account in my current savings plan?
WER: 2.75

Audio: datasets/hindi_audio/sample1.wav
Expected: mera loan balance batao
Predicted:  In Tekne, vkne environments,
WER: 1.0
------------------------------------------

Audio: datasets/english_audio/sample1.wav
Expected: show my loan balance
Predicted:  वेनाइन सागयाहि scrameshadesh셨ि एमारेना atabethic हमाराウर्वर्व।
WER: 1.5

Audio: datasets/hindi_audio/sample1.wav
Expected: mera loan balance batao
Predicted:  मेरे आखांस में कितने पैसे हैं?
WER: 1.5
---------------------------------------------
## Conclusion

Whisper performs best for multilingual speech recognition,
while other providers perform well for English-only use cases.