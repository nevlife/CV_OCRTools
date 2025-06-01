import os
import sys
import glob
from pathlib import Path
import cv2
import shutil
import argparse

import pytesseract
from dewarp.image import WarpedImage
from dewarp.options.core import Config

#윈도우 teesract 경로
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
#mac teesract 경로
pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/Cellar/tesseract/5.5.1/bin/tesseract"

def get_next_result_directory(output_dir, output_name):
    existing_dirs = glob.glob(str(output_dir / f"{output_name}*"))
    
    filtered_dirs = []
    for d in existing_dirs:
        if os.path.isdir(d):
            filtered_dirs.append(d)
    
    if not filtered_dirs:
        return 1
    
    numbers = []
    for dir_path in filtered_dirs:
        dir_name = os.path.basename(dir_path)
        try:
            num = int(dir_name.replace(output_name, ""))
            numbers.append(num)
        except ValueError:
            continue
    
    if not numbers:
        return 1
    
    return max(numbers) + 1


def apply_ocr_with_debug(image_path, output_dir, lang='kor+eng'):

    try:
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")
        
        debug_dir = Path(output_dir) / "ocr_debug"
        debug_dir.mkdir(exist_ok=True)
        
        # 1. 원본 이미지 저장
        cv2.imwrite(str(debug_dir / "1_original.png"), img)
        
        # 2. 그레이스케일 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(str(debug_dir / "2_grayscale.png"), gray)
        
        # 3. 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        cv2.imwrite(str(debug_dir / "3_denoised.png"), denoised)
        
        # 4. 대비 향상
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        cv2.imwrite(str(debug_dir / "4_contrast_enhanced.png"), enhanced)
        
        # 5. 이진화
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite(str(debug_dir / "5_binary.png"), binary)
        
        # Tesseract 페이지 분할 시각화
        # 6. 페이지 분석 결과 시각화 (시각화용 이미지 생성)
        page_img = img.copy()
        
        # Tesseract의 --psm 옵션 설명
        # 1: 자동 페이지 분할, OSD 적용
        # 3: 자동 페이지 분할, OSD 없음 (기본값)
        # 11: 텍스트 블록으로 취급, OSD 없음
        
        # 7. Tesseract 데이터 추출 (블록, 단락, 라인, 단어, 문자 정보)
        data = pytesseract.image_to_data(enhanced, lang=lang, output_type=pytesseract.Output.DICT)
        
        # 8. 텍스트 블록 시각화
        blocks_img = img.copy()
        n_boxes = len(data['level'])
        
        
        for i in range(n_boxes):
            level = data['level'][i]
            # 레벨 1: 페이지, 2: 블록, 3: 단락, 4: 라인, 5: 단어
            
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        
            if level == 2:
                cv2.rectangle(blocks_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
        cv2.imwrite(str(debug_dir / "6_text_blocks.png"), blocks_img)
        
        # 9. 텍스트 라인 시각화
        lines_img = img.copy()
        for i in range(n_boxes):
            level = data['level'][i]
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            if level == 4:
                cv2.rectangle(lines_img, (x, y), (x + w, y + h), (0, 0, 255), 1)
                # 기준선 표시 (라인의 약 3/4 지점)
                baseline_y = y + int(h * 0.75)
                cv2.line(lines_img, (x, baseline_y), (x + w, baseline_y), (255, 0, 0), 1)
                
        cv2.imwrite(str(debug_dir / "7_text_lines.png"), lines_img)
        
        # 10. 단어 시각화
        words_img = img.copy()
        for i in range(n_boxes):
            level = data['level'][i]
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            if level == 5:
                cv2.rectangle(words_img, (x, y), (x + w, y + h), (0, 255, 255), 1)
                
        cv2.imwrite(str(debug_dir / "8_words.png"), words_img)
        
        # 11. 특수 문자 인식 결과 시각화
        symbols_img = img.copy()
        
        # 신뢰도가 높은 단어만
        for i in range(n_boxes):
            level = data['level'][i]
            text = data['text'][i]
            conf = int(data['conf'][i])
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            if level == 5 and text and conf > 60:  # 신뢰도 60% 이상만만
                cv2.putText(symbols_img, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
        cv2.imwrite(str(debug_dir / "9_recognized_text.png"), symbols_img)
        
        
        text = pytesseract.image_to_string(enhanced, lang=lang)
        
        # 텍스트 파일 저장
        output_txt_path = Path(output_dir) / "ocr_result.txt"
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # HTML 포맷?의 OCR 결과
        hocr_output = Path(output_dir) / "ocr_result.html"
        hocr_data = pytesseract.image_to_pdf_or_hocr(enhanced, extension='hocr', lang=lang)
        with open(hocr_output, 'wb') as f:
            f.write(hocr_data)
            
        print(f"OCR 저장 경로: {output_txt_path}")
        print(f"OCR 디버깅 경로로: {debug_dir}")
        
        return text, debug_dir
        
    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {e}")
        return None, None


def main(
    input_dir = "./input/image.png",
    output_dir = "./output",
    output_name = "result",
):
    
    input_file = input_dir
    output_dir = output_dir
    output_name = output_name
    
    input_path = Path(input_file).resolve()
    
    if not input_path.exists():
        print(f"파일 못 찾음: {input_path}")
        return 1
    
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(exist_ok=True, parents=True)

    result_num = get_next_result_directory(output_dir=output_dir, output_name=output_name)
    print(f"result_num: {result_num}")
    result_dir = output_dir / f"{output_name}{result_num}"
    result_dir.mkdir(exist_ok=True)
    
    img = cv2.imread(str(input_path))
    if img is None:
        print(f"이미지 못 찾음: {input_path}")
        return 1
    
    print(f"이미지 크기: {img.shape[1]}x{img.shape[0]}")
    
    config = Config()
    config.DEBUG_LEVEL = 3  # 디버그 레벨 0 ~ 3
    #config.DEBUG_OUTPUT = "both"  # 화면과 파일에 디버그 출력
    #config.OUTPUT_ZOOM = 1.0  # 출력 이미지 확대/축소 비율
    config.NO_BINARY = False  # True: 그레이스케일 유지, False: 이진화 수행
    
    original_cwd = os.getcwd()
    os.chdir(result_dir)
    
    warped_img = WarpedImage(str(input_path), config=config)
    
    if warped_img.written:        
        input_copy_path = result_dir / f"원본_{input_path.name}"
        shutil.copy2(input_path, input_copy_path)
        
        # OCR 적용
        result_img_path = result_dir / warped_img.outfile
        ocr_text, debug_dir = apply_ocr_with_debug(result_img_path, result_dir)
        
        # 결과 시각화
        result = cv2.imread(str(warped_img.outfile))
        
        window_name = f"result{result_num}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, result)
        
        print("아무 키나 누르면 창이 닫힙니다...")
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("디워핑 처리가 실패. 텍스트 또는 라인이 충분히 감지되지 않음.")
    
    # 원래 작업 디렉토리로 복원
    os.chdir(original_cwd)
    
    print(f"처리 완료")
    return 0

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=str, default="./input/image.png")
    parser.add_argument("--output-dir", type=str, default="./output")
    parser.add_argument("--output-name", type=str, default="result")
    opt = parser.parse_args()
    print(opt)
    return opt
    
if __name__ == "__main__":
    opt = parse_args()
    main(**vars(opt))
    #sys.exit(main())