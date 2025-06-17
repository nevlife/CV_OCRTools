# 🔧 CV_OCRTools

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.11+-green.svg)](https://opencv.org/)
[![Tesseract](https://img.shields.io/badge/Tesseract-OCR-red.svg)](https://github.com/tesseract-ocr/tesseract)

**휘어진 문서를 평평하게 만들고 텍스트를 추출하는 고급 컴퓨터 비전 도구**

문서 이미지 교정(Page Dewarping) 및 OCR(광학 문자 인식)을 위한 통합 솔루션입니다. 특히 휘어진 책 페이지, 구겨진 문서, 곡면 영수증 등의 이미지를 처리하는 데 최적화되어 있습니다.

## ✨ 주요 특징

- 🔄 **고급 디워핑**: 3D 모델 기반 페이지 교정 알고리즘
- 🔍 **다단계 OCR**: 9단계 시각적 처리 과정으로 높은 정확도
- 🌏 **다국어 지원**: 한국어 + 영어 동시 인식
- ⚙️ **풍부한 설정**: 20+ 매개변수로 세밀한 조정 가능
- 🐛 **강력한 디버깅**: 단계별 중간 결과 이미지 생성
- 📱 **다양한 문서**: 책, 영수증, 신문, 잡지 등 지원

## 🚀 빠른 시작

### 설치

```bash
# 저장소 클론
git clone https://github.com/nevlife/CV_OCRTools.git
cd CV_OCRTools

# 의존성 설치
pip install -r requirements.txt
```

### Tesseract OCR 설정

#### Windows
1. [Tesseract 설치 프로그램](https://github.com/UB-Mannheim/tesseract/wiki) 다운로드
2. 설치 시 한국어 언어 팩 선택
3. `main.py`에서 경로 확인:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

#### macOS
```bash
brew install tesseract tesseract-lang
```
`main.py`에서 경로 수정:
```python
pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/Cellar/tesseract/5.5.1/bin/tesseract"
```

#### Linux
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-kor
```

### 기본 사용법

```bash
# 기본 실행 (./input/test1.jpg 처리)
python main.py

# 특정 이미지 처리
python main.py --input ./path/to/your/image.jpg

# 출력 디렉토리 지정
python main.py --input ./image.jpg --output ./results --name scan
```

## 📖 상세 사용법

### 명령줄 인터페이스

```bash
python main.py [옵션들]
```

#### 핵심 옵션
- `--input, -i`: 입력 이미지 파일 경로
- `--output, -o`: 출력 디렉토리 (기본값: `./output`)
- `--name, -n`: 결과 폴더명 접두사 (기본값: `result`)
- `--debug, -d`: 디버그 레벨 0-3 (기본값: 3)
- `--focal, -f`: 카메라 초점거리 (기본값: 1.2)

#### 텍스트 검출 설정
- `--tw`: 텍스트 윤곽선 최소 폭 (기본값: 15)
- `--th`: 텍스트 윤곽선 최소 높이 (기본값: 2)
- `--ta`: 텍스트 최소 가로세로 비율 (기본값: 1.5)
- `--tk`: 텍스트 최대 두께 (기본값: 10)

#### 에지 연결 설정
- `--eo`: 윤곽선 최대 수평 겹침 (기본값: 1.0)
- `--el`: 에지 최대 연결 길이 (기본값: 150.0)
- `--ec`: 에지 각도 변화 비용 (기본값: 10.0)
- `--ea`: 허용 최대 각도 변화 (기본값: 15.0)

### 사용 예제

#### 휘어진 책 페이지 처리
```bash
python main.py --input book_page.jpg --focal 1.5 --debug 3
```

#### 영수증 처리 (더 민감한 설정)
```bash
python main.py --input receipt.jpg --tw 10 --th 1 --ta 1.0
```

#### 큰 문서 처리 (빠른 처리)
```bash
python main.py --input document.jpg --debug 1 --decimate 32
```

## 🏗️ 프로젝트 구조

```
CV_OCRTools/
│
├── 📁 input/                    # 입력 이미지 폴더
│   ├── test1.jpg
│   └── ...
│
├── 📁 output/                   # 출력 결과 폴더
│   └── result1/
│       ├── 원본_test1.jpg       # 원본 이미지 복사본
│       ├── output.png           # 디워핑된 결과
│       ├── ocr_result.txt       # OCR 텍스트 결과
│       ├── ocr_result.html      # HTML 형식 OCR 결과
│       └── 📁 ocr_debug/        # OCR 단계별 이미지
│           ├── 1_original.png
│           ├── 2_grayscale.png
│           ├── ...
│           └── 9_recognized_text.png
│
├── 📁 dewarp/                   # 디워핑 핵심 모듈
│   ├── image.py                 # 메인 WarpedImage 클래스
│   ├── dewarp.py                # 디워핑 알고리즘
│   ├── contours.py              # 윤곽선 검출
│   ├── spans.py                 # 텍스트 라인 분석
│   ├── 📁 options/              # 설정 관리
│   │   └── core.py              # Config 클래스
│   └── ...
│
├── main.py                      # 메인 실행 파일
├── test.py                      # 영수증 특화 테스트
├── requirements.txt             # 패키지 의존성
└── README.md                    # 이 파일
```

## 🔧 고급 설정

### Config 클래스 직접 사용

```python
from dewarp.image import WarpedImage
from dewarp.options.core import Config

# 설정 객체 생성
config = Config()

# 카메라 설정
config.FOCAL_LENGTH = 1.2

# 출력 설정
config.OUTPUT_ZOOM = 1.0
config.OUTPUT_DPI = 300
config.NO_BINARY = False  # True: 그레이스케일, False: 이진화

# 디버그 설정
config.DEBUG_LEVEL = 3
config.DEBUG_OUTPUT = "file"  # "screen", "file", "both"

# 화면 설정
config.SCREEN_MAX_W = 1280
config.SCREEN_MAX_H = 700

# 이미지 처리
warped_img = WarpedImage("path/to/image.jpg", config=config)

if warped_img.written:
    print(f"처리 완료: {warped_img.outfile}")
else:
    print("처리 실패: 텍스트가 충분히 감지되지 않음")
```

### 매개변수 세부 설명

| 매개변수 | 설명 | 권장값 |
|---------|------|---------|
| `FOCAL_LENGTH` | 카메라 정규화 초점거리 | 1.0-2.0 |
| `TEXT_MIN_WIDTH` | 텍스트 윤곽선 최소 폭 | 10-20 |
| `TEXT_MIN_HEIGHT` | 텍스트 윤곽선 최소 높이 | 1-5 |
| `ADAPTIVE_WINSZ` | 적응형 임계값 윈도우 크기 | 25-55 |
| `REMAP_DECIMATE` | 리매핑 다운스케일링 인수 | 8-32 |

## 🎯 성능 최적화 팁

### 빠른 처리가 필요한 경우
```bash
python main.py --debug 0 --decimate 32 --wz 25
```

### 높은 품질이 필요한 경우
```bash
python main.py --debug 3 --decimate 8 --zoom 1.5 --dpi 600
```

### 작은 텍스트 처리
```bash
python main.py --tw 5 --th 1 --ta 1.0 --tk 5
```

## 🐛 트러블슈팅

### 자주 발생하는 문제들

#### 1. "디워핑 처리가 실패. 텍스트 또는 라인이 충분히 감지되지 않음."
**해결책:**
- 텍스트 검출 민감도 높이기: `--tw 5 --th 1`
- 디버그 모드로 중간 과정 확인: `--debug 3`
- 이미지 전처리 윈도우 크기 조정: `--wz 35`

#### 2. Tesseract 경로 오류
**해결책:**
- Windows: Tesseract가 `C:\Program Files\Tesseract-OCR\`에 설치되었는지 확인
- macOS: `which tesseract`로 경로 확인 후 `main.py` 수정
- Linux: `sudo apt-get install tesseract-ocr` 재실행

#### 3. OCR 결과가 부정확함
**해결책:**
- 이미지 품질 향상: `--zoom 1.5 --dpi 600`
- 이진화 비활성화: `--no-bin 1`
- 다른 초점거리 시도: `--focal 1.5` 또는 `--focal 0.8`

#### 4. 메모리 부족 오류
**해결책:**
- 처리 속도 향상: `--decimate 32`
- 화면 출력 크기 제한: `--sw 800 --sh 600`
- 디버그 레벨 낮추기: `--debug 1`

## 📊 지원되는 이미지 형식

- **입력**: JPG, PNG, BMP, TIFF
- **출력**: PNG (기본), 설정에 따라 그레이스케일 또는 이진화

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🙏 감사의 말

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - 강력한 OCR 엔진
- [OpenCV](https://opencv.org/) - 컴퓨터 비전 라이브러리
- [mzucker/page_dewarp](https://github.com/mzucker/page_dewarp) - 페이지 디워핑 알고리즘 참조

## 📞 지원

문제가 발생하거나 질문이 있으시면:
- [Issues](https://github.com/nevlife/CV_OCRTools/issues) 페이지에서 버그 리포트 또는 기능 요청
- 문서의 트러블슈팅 섹션 확인

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요!