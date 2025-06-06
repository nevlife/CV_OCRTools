# CV_OCRTools

컴퓨터 비전 기반 문서 이미지 교정 및 OCR 통합 도구

## 🚀 주요 기능

**CV_OCRTools**는 휘어진 문서나 책 이미지를 자동으로 교정하고 텍스트를 추출하는 완전 자동화된 솔루션입니다.

- **🔧 자동 이미지 교정**: 휘어진 책, 구겨진 문서, 곡면 영수증을 평평하게 변환
- **📝 다국어 OCR**: 한국어 + 영어 텍스트 동시 인식 
- **🎯 고정밀 처리**: 3차원 페이지 모델 기반 perspective 교정
- **⚙️ 세밀한 제어**: 50+ 매개변수로 다양한 문서 유형에 최적화
- **🔍 디버그 지원**: 단계별 처리 과정 시각화 및 분석

## 📋 사용 사례

- 휘어진 책 페이지 스캔 교정
- 접힌 문서나 영수증 복원
- 카메라로 촬영한 문서의 OCR 전처리
- 대량 문서 자동화 처리 파이프라인

## 🛠 설치

### 1. 저장소 클론 및 패키지 설치

```bash
git clone https://github.com/nevlife/CV_OCRTools.git
cd CV_OCRTools
pip install -r requirements.txt
```

### 2. Tesseract OCR 설치

#### Windows
```bash
# Tesseract 다운로드 및 설치
# https://github.com/UB-Mannheim/tesseract/wiki
# 한국어 언어팩 포함하여 설치
```

#### Linux
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-kor
```

#### macOS
```bash
brew install tesseract tesseract-lang
```

### 3. Tesseract 경로 설정

`main.py` 파일에서 본인의 Tesseract 설치 경로로 수정:

```python
# Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# macOS
pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/bin/tesseract"
```

## 🚀 빠른 시작

### 단일 이미지 처리

```bash
# 기본 실행 (input 폴더의 이미지 처리)
python main.py

# 특정 이미지 처리
python main.py --input ./my_image.jpg --output ./results

# 디워핑 없이 OCR만 실행
python main.py --input ./image.jpg --warp False
```

### 폴더 내 모든 이미지 일괄 처리

```bash
python main.py --input ./input_folder --output ./output_folder --name batch_result
```

### 고급 설정

```bash
# 고품질 처리 (세밀한 텍스트 검출)
python main.py --tw 10 --th 1 --ta 1.2 --debug 3

# 빠른 처리 (대용량 문서용)
python main.py --tw 20 --th 3 --ta 2.0 --decimate 8
```

## 📁 프로젝트 구조

```
CV_OCRTools/
├── main.py              # 메인 실행 파일 (CLI + OCR 통합)
├── test.py              # 영수증 전용 처리 스크립트
├── requirements.txt     # 의존성 패키지
├── input/              # 입력 이미지 폴더
├── output/             # 처리 결과 출력 폴더
├── test_parameter/     # 테스트 매개변수 설정
└── dewarp/            # 핵심 이미지 교정 모듈
    ├── image.py       # WarpedImage 클래스 (메인 처리)
    ├── dewarp.py      # 3D 페이지 모델 교정
    ├── contours.py    # 텍스트 윤곽선 검출
    ├── spans.py       # 텍스트 라인 분석
    ├── options/       # 설정 관리
    └── debug_utils/   # 디버그 도구
```

## 🎛 주요 매개변수

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--tw` | 15 | 텍스트 윤곽선 최소 폭 (작을수록 작은 글씨 검출) |
| `--th` | 2 | 텍스트 윤곽선 최소 높이 |
| `--ta` | 1.5 | 텍스트 최소 가로세로 비율 |
| `--focal` | 1.2 | 카메라 초점거리 (원근 보정 강도) |
| `--debug` | 0 | 디버그 레벨 (0-3, 3이 가장 상세) |
| `--zoom` | 1.0 | 출력 이미지 확대율 |
| `--wz` | 55 | 적응형 임계값 윈도우 크기 |

## 💻 코드 사용 예제

### 기본 이미지 처리

```python
from dewarp.image import WarpedImage
from dewarp.options.core import Config

# 설정 초기화
config = Config()
config.DEBUG_LEVEL = 2
config.OUTPUT_ZOOM = 1.5

# 이미지 교정 처리
warped_img = WarpedImage("document.jpg", config=config)

if warped_img.written:
    print(f"교정 완료: {warped_img.outfile}")
    # OCR 처리는 main.py의 perform_ocr 함수 참조
```

### OCR 단독 처리

```python
import pytesseract
import cv2

# 이미지 로드
img = cv2.imread("document.jpg")

# OCR 실행
text = pytesseract.image_to_string(
    img, 
    lang='kor+eng',
    config='--oem 1 --psm 3'
)

print(text)
```

## 🔧 고급 활용

### 영수증 특화 처리

`test.py`는 영수증 이미지에 특화된 전처리 파이프라인을 제공합니다:

- CLAHE 대비 향상
- 적응형 이진화
- 컨투어 기반 자동 영역 검출
- 원근 변환 및 OCR

```bash
python test.py  # ./data/image/receipt_00000.png 처리
```

### 배치 처리 스크립트

```python
import os
from pathlib import Path
from main import process_single_image
from dewarp.options.core import Config

config = Config()
config.DEBUG_LEVEL = 1

input_dir = Path("./documents")
output_dir = Path("./results")

for img_file in input_dir.glob("*.jpg"):
    process_single_image(
        input_path=img_file,
        output_dir=output_dir,
        output_name=f"processed_{img_file.stem}",
        warp=True,
        config=config
    )
```

## 📊 출력 파일

처리 완료 후 다음 파일들이 생성됩니다:

```
output/result_1/
├── corrected_image.png    # 교정된 이미지
├── ocr_result.txt         # 추출된 텍스트
├── ocr_result.html        # HTML 형식 OCR 결과
├── original_input.jpg     # 원본 이미지 백업 (debug 모드)
└── ocr_debug/            # OCR 단계별 시각화 (debug 모드)
    ├── 6_text_blocks.png
    ├── 7_text_lines.png
    ├── 8_words.png
    └── 9_recognized_text.png
```

## 🎯 성능 최적화 팁

### 빠른 처리를 위한 설정

```bash
python main.py --decimate 8 --tw 20 --debug 0
```

### 고품질 처리를 위한 설정

```bash
python main.py --decimate 4 --tw 8 --th 1 --zoom 1.5 --debug 3
```

### 메모리 절약

```bash
python main.py --sw 800 --sh 600 --no-bin 0
```

## 🤝 기여

문제 신고나 기능 제안은 Issues를 통해 해주세요. Pull Request도 환영합니다!

## 📚 참고 자료

- [Tesseract OCR 문서](https://tesseract-ocr.github.io/)
- [OpenCV 문서](https://docs.opencv.org/)
- 프로젝트는 문서 이미지 교정 연구를 기반으로 개발되었습니다.
