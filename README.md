# CV_OCRTools

문서 이미지 교정 및 OCR(광학 문자 인식)을 위한 컴퓨터 비전 도구 모음입니다.

## 개요

CV_OCRTools는 문서 이미지 처리와 텍스트 추출을 위한 통합 솔루션입니다. 주요 기능은 다음과 같습니다:

1. **디워핑 (Page Dewarping)**: 휘어진 책이나 문서 이미지를 평평하게 교정
2. **OCR 처리**: 교정된 이미지에서 텍스트 추출 (한국어 + 영어 지원)
3. **이미지 전처리**: 대비 개선, 노이즈 제거, 이진화 등의 전처리 기능 제공

이 도구는 특히 휘어진 책 페이지, 구겨진 문서, 곡면을 가진 영수증 등의 이미지를 처리하는 데 유용합니다.

## 설치 요구사항

### 필수 패키지

이 프로젝트를 실행하기 위해 다음 패키지가 필요합니다:

```
numpy
opencv-python
scipy
pytesseract
Pillow
msgspec
```

### Tesseract OCR 설정

OCR 기능을 사용하려면 Tesseract OCR을 설치하고 경로를 설정해야 합니다:

1. [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) 설치
2. 한국어 언어 팩 설치
3. `main.py` 파일의 다음 경로를 본인의 Tesseract 설치 경로로 수정:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

## 프로젝트 구조

```
CV_OCRTools/
│
├── main.py                # 메인 실행 파일
├── test.py                # 테스트 및 디버깅 유틸리티
│
├── input/                 # 입력 이미지 폴더
│   ├── test1.jpg
│   ├── test2.jpg
│   └── ...
│
└── dewarp/               # 디워핑 관련 모듈
    ├── __init__.py
    ├── image.py           # 이미지 처리 핵심 클래스
    ├── dewarp.py          # 디워핑 알고리즘
    ├── contours.py        # 윤곽선 검출
    ├── spans.py           # 텍스트 라인 분석
    ├── options/           # 설정 옵션
    │   └── core.py        # 기본 설정 클래스
    └── ...
```

## 사용 방법

### 기본 사용

```python
python main.py
```

기본적으로 `./input/test1.jpg` 파일을 처리하고 결과를 `./output/` 디렉토리에 저장합니다.

### 코드에서 사용하기

```python
from dewarp.image import WarpedImage
from dewarp.options.core import Config

# 설정 생성
config = Config()
config.DEBUG_LEVEL = 3  # 디버그 레벨 (0-3)
config.NO_BINARY = False  # 이진화 여부

# 이미지 디워핑 처리
warped_img = WarpedImage("path/to/image.jpg", config=config)

# 결과 확인
if warped_img.written:
    print(f"처리 완료: {warped_img.outfile}")
```

### 영수증 이미지 처리 (test.py)

`test.py` 파일은 영수증과 같은 문서의 교정 및 OCR 처리를 위한 추가 기능을 제공합니다:

```python
python test.py
```

## 주요 기능

### 1. 이미지 디워핑 (WarpedImage 클래스)

- 페이지 경계 감지
- 텍스트 라인 분석
- 3차원 모델 기반 이미지 교정
- 다양한 디버깅 레벨 지원

### 2. OCR 처리

- 한국어/영어 텍스트 인식
- 교정 이미지에서 텍스트 추출
- 결과 텍스트 파일 저장

### 3. 이미지 전처리 (test.py)

- 대비 향상 (CLAHE)
- 가우시안 블러
- 적응형 이진화
- 엣지 검출
- 형태학적 연산 (팽창, 닫힘)

## 설정 옵션

`Config` 클래스를 통해 다양한 설정을 조정할 수 있습니다:

```python
config = Config()

# 카메라 설정
config.FOCAL_LENGTH = 1.2  # 카메라 초점 거리

# 출력 설정
config.OUTPUT_ZOOM = 1.0  # 출력 이미지 확대/축소 비율
config.OUTPUT_DPI = 300  # 출력 이미지 DPI
config.NO_BINARY = False  # True: 그레이스케일 유지, False: 이진화 수행

# 디버그 설정
config.DEBUG_LEVEL = 3  # 디버그 레벨 (0-3)
config.DEBUG_OUTPUT = "file"  # 디버그 출력 방식 ("screen", "file", "both")

# 디스플레이 설정
config.SCREEN_MAX_W = 1280  # 최대 화면 폭
config.SCREEN_MAX_H = 700  # 최대 화면 높이
```

## 향후 개선 계획

- 다중 이미지 일괄 처리 기능
- GUI 인터페이스 추가
- 더 많은 언어 지원
- 표 구조 인식 기능 개선
- PDF 변환 및 병합 기능

## 참고

이 프로젝트는 다음 기술을 활용합니다:
- OpenCV: 이미지 처리 및 컴퓨터 비전
- Tesseract OCR: 광학 문자 인식
- Scipy: 최적화 및 수학적 연산
- msgspec: 구조체 정의 및 메타데이터 관리
