### English Commands
1. Check my account balance  
2. Transfer five hundred rupees to Ramesh  
3. Show my last five transactions  
4. Block my debit card  
5. What is my loan balance  
6. Deposit two thousand rupees  
7. Withdraw three hundred rupees  
8. Show my savings account balance  
9. Transfer money to Anita  
10. How much money is in my account  

### Hindi Commands
1. मेरा खाता बैलेंस बताओ  
2. रमेश को पाँच सौ रुपये भेजो  
3. मेरे आखिरी पाँच ट्रांजैक्शन दिखाओ  
4. मेरा डेबिट कार्ड ब्लॉक करो  
5. मेरे लोन का बैलेंस क्या है  
6. दो हजार रुपये जमा करो  
7. तीन सौ रुपये निकालो  

(Similar commands used for other languages)

---

## 9. Preliminary Results

### English Dataset

| Audio     | Error Type                     | WER   |
|----------|------------------------------|------|
| eng1.wav | punctuation difference        | 0.25 |
| eng2.wav | number formatting            | 0.5  |
| eng3.wav | punctuation difference        | 0.2  |
| eng4.wav | wrong transcription           | 1.0  |
| eng5.wav | punctuation difference        | 0.2  |
| eng6.wav | number formatting            | 0.75 |
| eng7.wav | number formatting            | 0.75 |
| eng8.wav | punctuation difference        | 0.2  |
| eng9.wav | punctuation difference        | 0.25 |
| eng10.wav| punctuation difference        | 0.1429 |

**Average WER (English): 0.425**

---

### Hindi Dataset

| Audio     | Error Type                          | WER   |
|----------|------------------------------------|------|
| hin1.wav | Spelling Difference                 | 0.25 |
| hin2.wav | Numeric Conversion Error            | 0.5  |
| hin3.wav | Wrong Sentence                      | 1.0  |
| hin4.wav | Swapped Transcription               | 1.0  |
| hin5.wav | Spelling Difference                 | 0.3333 |
| hin6.wav | Numeric Conversion Error            | 0.8  |
| hin7.wav | Completely Wrong                    | 1.0  |
| hin8.wav | Spelling Difference                 | 0.3333 |
| hin9.wav | Spelling Variation                  | 0.4  |
| hin10.wav| Punctuation Difference              | 0.1667 |

**Average WER (Hindi): 0.5783**

---

### Spanish Dataset

| Audio      | Error Type              | WER   |
|-----------|------------------------|------|
| span1.wav | case difference         | 0.125 |
| span2.wav | punctuation difference  | 0.4   |
| span3.wav | numeric conversion      | 1.0   |
| span4.wav | punctuation difference  | 0.5   |
| span5.wav | case difference         | 0.1429 |
| span6.wav | punctuation difference  | 0.3333 |
| span7.wav | case difference         | 0.1111 |
| span8.wav | punctuation difference  | 0.5   |
| span9.wav | case difference         | 0.1111 |
| span10.wav| punctuation difference  | 0.3333 |

**Average WER (Spanish): 0.356**

---

### French Dataset

| Audio        | Error Type              | WER   |
|-------------|------------------------|------|
| french1.wav | punctuation difference  | 0.25 |
| french2.wav | wrong sentence          | 1.0  |
| french3.wav | numeric conversion      | 1.0  |
| french4.wav | numeric conversion      | 1.0  |
| french5.wav | punctuation difference  | 0.2857 |
| french6.wav | punctuation difference  | 0.3333 |
| french7.wav | punctuation difference  | 0.2222 |
| french8.wav | punctuation difference  | 0.5  |
| french10.wav| punctuation difference  | 0.3333 |

**Average WER (French): 0.547**

---

## 10. Overall Language Comparison

| Language | Average WER |
|----------|------------|
| English  | 0.424 |
| Hindi    | 0.578 |
| Spanish  | 0.356 |
| French   | 0.547 |

---

