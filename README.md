# artale_dc_msg
頻道販售 喊話

安裝教學
1.python https://www.python.org/downloads/

2.tesseract(OCR)

下載網址:
https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe

安裝路徑:
C:\Program Files\Tesseract-OCR\tesseract.exe

環境變數設定 (command 命令提示自元)
set PATH=%PATH%;"C:\Program Files\Tesseract-OCR"

執行檔案
python paste.py

## 設定教學
* 目前設定為 中文辨識(chi_tra) ，請先將 setting\lang\chi_tra.traineddata 放入 C:\Program Files\Tesseract-OCR\tessdata
* 選擇需要的頻道 (不要有特殊符號)，判定偵測有無效請在執行後 debug.png 確認
* 輸入文字說明
* 儲存設定: 設定檔 (.json)  文字說明(.txt)
![設定畫面](pic/setting.png)