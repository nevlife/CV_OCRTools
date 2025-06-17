# CV_OCRTools

문서 이미지 교정(Page Dewarping) 및 OCR(광학 문자 인식)을 위한 컴퓨터 비전 도구입니다. 휘어진 책 페이지, 구겨진 문서, 곡면 영수증 등의 이미지를 처리할 수 있습니다.

## 주요 기능

- 3D 모델 기반 페이지 교정 알고리즘
- 한국어 + 영어 OCR 처리
- 단계별 디버깅 이미지 생성
- 상세한 매개변수 조정 옵션
- 다양한 문서 타입 지원

## 설치

```bash
git clone https://github.com/nevlife/CV_OCRTools.git
cd CV_OCRTools
pip install -r requirements.txt
```

### Tesseract OCR 설정

**Windows:**
1. [Tesseract 설치 프로그램](https://github.com/UB-Mannheim/tesseract/wiki) 다운로드
2. 설치 시 한국어 언어 팩 선택
3. `main.py`에서 경로 확인:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-kor
```

## 사용법

### 기본 실행

```bash
# 기본 실행 (./input/test1.jpg 처리)
python main.py

# 특정 이미지 처리
python main.py --input ./path/to/image.jpg

# 출력 디렉토리 지정
python main.py --input ./image.jpg --output ./results --name scan
```

### 주요 옵션

```bash
python main.py [옵션들]
```

**기본 옵션:**
- `--input, -i`: 입력 이미지 파일 경로
- `--output, -o`: 출력 디렉토리 (기본값: `./output`)
- `--name, -n`: 결과 폴더명 접두사 (기본값: `result`)
- `--debug, -d`: 디버그 레벨 0-3 (기본값: 3)
- `--focal, -f`: 카메라 초점거리 (기본값: 1.2)

**텍스트 검출 설정:**
- `--tw`: 텍스트 윤곽선 최소 폭 (기본값: 15)
- `--th`: 텍스트 윤곽선 최소 높이 (기본값: 2)
- `--ta`: 텍스트 최소 가로세로 비율 (기본값: 1.5)
- `--tk`: 텍스트 최대 두께 (기본값: 10)

**에지 연결 설정:**
- `--eo`: 윤곽선 최대 수평 겹침 (기본값: 1.0)
- `--el`: 에지 최대 연결 길이 (기본값: 150.0)
- `--ec`: 에지 각도 변화 비용 (기본값: 10.0)
- `--ea`: 허용 최대 각도 변화 (기본값: 15.0)

### 사용 예제

```bash
# 휘어진 책 페이지 처리
python main.py --input book_page.jpg --focal 1.5 --debug 3

# 영수증 처리 (민감한 설정)
python main.py --input receipt.jpg --tw 10 --th 1 --ta 1.0

# 빠른 처리
python main.py --input document.jpg --debug 1 --decimate 32
```

## 프로젝트 구조

```
CV_OCRTools/
├── input/                      # 입력 이미지 폴더
├── output/                     # 출력 결과 폴더
│   └── result1/
│       ├── 원본_*.jpg          # 원본 이미지 복사본
│       ├── output.png          # 디워핑된 결과
│       ├── ocr_result.txt      # OCR 텍스트 결과
│       ├── ocr_result.html     # HTML 형식 OCR 결과
│       └── ocr_debug/          # OCR 단계별 이미지
├── dewarp/                     # 디워핑 핵심 모듈
│   ├── image.py                # 메인 WarpedImage 클래스
│   ├── dewarp.py               # 디워핑 알고리즘
│   ├── contours.py             # 윤곽선 검출
│   ├── spans.py                # 텍스트 라인 분석
│   └── options/core.py         # Config 클래스
├── main.py                     # 메인 실행 파일
├── test.py                     # 영수증 특화 테스트
└── requirements.txt            # 패키지 의존성
```

## 고급 설정

### Config 클래스 직접 사용

```python
from dewarp.image import WarpedImage
from dewarp.options.core import Config

config = Config()
config.FOCAL_LENGTH = 1.2
config.OUTPUT_ZOOM = 1.0
config.OUTPUT_DPI = 300
config.NO_BINARY = False  # True: 그레이스케일, False: 이진화
config.DEBUG_LEVEL = 3
config.DEBUG_OUTPUT = "file"  # "screen", "file", "both"

warped_img = WarpedImage("path/to/image.jpg", config=config)

if warped_img.written:
    print(f"처리 완료: {warped_img.outfile}")
else:
    print("처리 실패: 텍스트가 충분히 감지되지 않음")
```

### 주요 매개변수

| 매개변수 | 설명 | 권장값 |
|---------|------|---------|
| `FOCAL_LENGTH` | 카메라 정규화 초점거리 | 1.0-2.0 |
| `TEXT_MIN_WIDTH` | 텍스트 윤곽선 최소 폭 | 10-20 |
| `TEXT_MIN_HEIGHT` | 텍스트 윤곽선 최소 높이 | 1-5 |
| `ADAPTIVE_WINSZ` | 적응형 임계값 윈도우 크기 | 25-55 |
| `REMAP_DECIMATE` | 리매핑 다운스케일링 인수 | 8-32 |

## 성능 최적화

**빠른 처리:**
```bash
python main.py --debug 0 --decimate 32 --wz 25
```

**높은 품질:**
```bash
python main.py --debug 3 --decimate 8 --zoom 1.5 --dpi 600
```

**작은 텍스트 처리:**
```bash
python main.py --tw 5 --th 1 --ta 1.0 --tk 5
```

## 문제 해결

### 디워핑 처리가 실패하는 경우

"디워핑 처리가 실패. 텍스트 또는 라인이 충분히 감지되지 않음." 오류가 발생할 때:

- 텍스트 검출 민감도 높이기: `--tw 5 --th 1`
- 디버그 모드로 중간 과정 확인: `--debug 3`
- 이미지 전처리 윈도우 크기 조정: `--wz 35`

### Tesseract 경로 오류

- Windows: Tesseract가 `C:\Program Files\Tesseract-OCR\`에 설치되었는지 확인
- macOS: `which tesseract`로 경로 확인 후 `main.py` 수정
- Linux: `sudo apt-get install tesseract-ocr` 재실행

### OCR 결과가 부정확한 경우

- 이미지 품질 향상: `--zoom 1.5 --dpi 600`
- 이진화 비활성화: `--no-bin 1`
- 다른 초점거리 시도: `--focal 1.5` 또는 `--focal 0.8`

### 메모리 부족 오류

- 처리 속도 향상: `--decimate 32`
- 화면 출력 크기 제한: `--sw 800 --sh 600`
- 디버그 레벨 낮추기: `--debug 1`

## 지원되는 이미지 형식

- **입력**: JPG, PNG, BMP, TIFF
- **출력**: PNG (기본), 설정에 따라 그레이스케일 또는 이진화