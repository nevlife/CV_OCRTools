
import os
import sys
import glob
from pathlib import Path
import cv2
import numpy as np
import shutil
import pytesseract
from dewarp.image import WarpedImage
from dewarp.options.core import Config

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def get_next_result_directory(output_dir):
    # 기존 result 디렉토리 찾기
    existing_dirs = glob.glob(str(output_dir / "result*"))
    
    existing_dirs = [d for d in existing_dirs if os.path.isdir(d)]
    
    if not existing_dirs:
        return 1
    
    numbers = []
    for dir_path in existing_dirs:
        dir_name = os.path.basename(dir_path)
        try:
            num = int(dir_name.replace("result", ""))
            numbers.append(num)
        except ValueError:
            continue
    
    if not numbers:
        return 1
    
    return max(numbers) + 1


def apply_ocr(image_path, output_txt_path, lang='kor+eng'):
    """
    이미지에 OCR을 적용하여 텍스트를 추출하고 파일로 저장합니다.
    
    Args:
        image_path: OCR을 적용할 이미지 파일 경로
        output_txt_path: 추출된 텍스트를 저장할 파일 경로
        lang: OCR 언어 설정 (기본값: 한국어+영어)
    
    Returns:
        추출된 텍스트
    """
    try:
        # 이미지 로드
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")
        
        # 이미지 전처리 (필요시 조정)
        # 그레이스케일 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 노이즈 제거 (필요시 주석 해제)
        # gray = cv2.medianBlur(gray, 3)
        
        # 대비 향상 (필요시 주석 해제)
        # gray = cv2.equalizeHist(gray)
        
        # OCR 적용
        print(f"OCR 처리 중... ({lang})")
        text = pytesseract.image_to_string(gray, lang=lang)
        
        # 결과 저장
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"OCR 텍스트가 저장되었습니다: {output_txt_path}")
        return text
        
    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {e}")
        return None


def main():
    input_file = "./input/test1.jpg"
    output_dir = "./output"
    
    input_path = Path(input_file).resolve()
    print(f"입력 파일 경로: {input_path}")
    
    if not input_path.exists():
        print(f"오류: 파일을 찾을 수 없습니다 - {input_path}")
        return 1
    
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(exist_ok=True, parents=True)
    print(f"기본 출력 디렉토리: {output_dir}")
    
    # 결과별 디렉토리 생성 (result1, result2, ...)
    result_num = get_next_result_directory(output_dir)
    result_dir = output_dir / f"result{result_num}"
    result_dir.mkdir(exist_ok=True)
    print(f"현재 결과 디렉토리: {result_dir}")
    
    img = cv2.imread(str(input_path))
    if img is None:
        print(f"오류: 이미지를 로드할 수 없습니다. 파일 형식이 올바른지 확인하세요 - {input_path}")
        return 1
    
    # 이미지 정보 출력
    print(f"이미지 크기: {img.shape[1]}x{img.shape[0]}")
    
    # 설정 객체 생성
    config = Config()
    config.DEBUG_LEVEL = 2  # 디버그 레벨 (0-3)
    config.DEBUG_OUTPUT = "both"  # 화면과 파일에 디버그 출력
    config.OUTPUT_ZOOM = 1.0  # 출력 이미지 확대/축소 비율
    config.NO_BINARY = False  # True: 그레이스케일 유지, False: 이진화 수행
    
    print(f"페이지 디워핑 시작: {input_path}")
    
    # 현재 작업 디렉토리를 결과 디렉토리로 변경(결과가 여기에 저장됨)
    original_cwd = os.getcwd()
    os.chdir(result_dir)
    
    # 이미지 로드 및 디워핑 수행
    warped_img = WarpedImage(str(input_path), config=config)
    
    if warped_img.written:
        output_path = Path(warped_img.outfile)
        print(f"성공: 결과 이미지가 저장되었습니다 - {result_dir / output_path}")
        
        # 원본 파일 복사 (선택 사항)
        input_copy_path = result_dir / f"원본_{input_path.name}"
        shutil.copy2(input_path, input_copy_path)
        print(f"원본 이미지 복사됨: {input_copy_path}")
        
        # OCR 적용
        result_img_path = result_dir / warped_img.outfile
        txt_output_path = result_dir / f"ocr_result.txt"
        ocr_text = apply_ocr(result_img_path, txt_output_path)
        
        # 텍스트 미리보기 출력 (최대 300자)
        if ocr_text:
            preview = ocr_text[:300]
            if len(ocr_text) > 300:
                preview += "..."
            print("\n----- OCR 텍스트 미리보기 -----")
            print(preview)
            print("------------------------------\n")
        
        # 결과 시각화
        result = cv2.imread(str(warped_img.outfile))
        
        window_name = f"디워핑 결과 (result{result_num})"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, result)
        print("아무 키나 누르면 창이 닫힙니다...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("경고: 디워핑 처리가 실패했습니다. 텍스트 또는 라인이 충분히 감지되지 않았습니다.")
    
    # 원래 작업 디렉토리로 복원
    os.chdir(original_cwd)
    
    # 처리 완료 메시지
    print(f"\n처리 완료: 결과는 '{result_dir}' 디렉토리에 저장되었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())