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
#pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/Cellar/tesseract/5.5.1/bin/tesseract"

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


def perform_ocr(image_path, output_dir, lang='kor+eng', oem=2, psm=6):
    config = f'--oem {oem} --psm {psm}'
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
        #page_img = img.copy()
        
        # Tesseract의 --psm 옵션 설명
        # 1: 자동 페이지 분할, OSD 적용
        # 3: 자동 페이지 분할, OSD 없음 (기본값)
        # 11: 텍스트 블록으로 취급, OSD 없음
        
        # 7. Tesseract 데이터 추출 (블록, 단락, 라인, 단어, 문자 정보)
        data = pytesseract.image_to_data(
            enhanced, 
            lang=lang, 
            output_type=pytesseract.Output.DICT,
            config=config  # LSTM 모델 사용 및 단일 텍스트 블록으로 처리
        )
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
        
        
        text = pytesseract.image_to_string(
            enhanced, 
            lang=lang,
            config=config  # LSTM 모델 사용 및 단일 텍스트 블록으로 처리
        )
        # 텍스트 파일 저장
        output_txt_path = Path(output_dir) / "ocr_result.txt"
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # HTML 포맷?의 OCR 결과
        hocr_output = Path(output_dir) / "ocr_result.html"
        hocr_data = pytesseract.image_to_pdf_or_hocr(
            enhanced, 
            extension='hocr', 
            lang=lang,
            config=config  # LSTM 모델 사용
        )
        with open(hocr_output, 'wb') as f:
            f.write(hocr_data)
            
        print(f"OCR 저장 경로: {output_txt_path}")
        print(f"OCR 디버깅 경로로: {debug_dir}")
        
        return text, debug_dir
        
    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {e}")
        return None, None

def main(
    input="./input/image.png",  # 입력 이미지 파일 경로
    output="./output",  # 출력 디렉토리 경로
    name="result",  # 결과 폴더 이름
    focal=1.2,  # 카메라의 정규화된 초점거리
    tw=15,  # 검출할 텍스트 윤곽선의 최소 폭 (축소된 픽셀 단위)
    th=2,  # 검출할 텍스트 윤곽선의 최소 높이 (축소된 픽셀 단위)
    ta=1.5,  # 텍스트 윤곽선의 최소 가로세로 비율 (폭/높이)
    tk=10,  # 검출할 텍스트 윤곽선의 최대 두께 (축소된 픽셀 단위)
    debug=3,  # 디버그 레벨 0 ~ 3
    debug_out="both",  # 디버그 출력 방식: "file", "screen", "both"
    eo=1.0,  # 스팬 내에서 윤곽선들의 최대 수평 겹침 (축소된 픽셀 단위)
    el=100.0,  # 윤곽선들을 연결하는 에지의 최대 길이 (축소된 픽셀 단위)
    ec=10.0,  # 에지의 각도 변화에 대한 비용 (길이 대비 각도의 가중치)
    ea=7.5,  # 윤곽선들 사이에서 허용되는 최대 각도 변화 (도 단위)
    sw=1280,  # 화면 표시용 최대 폭 (픽셀)
    sh=700,  # 화면 표시용 최대 높이 (픽셀)
    mx=50,  # 좌우 가장자리에서 무시할 픽셀 수 (축소된 이미지 기준)
    my=20,  # 상하 가장자리에서 무시할 픽셀 수 (축소된 이미지 기준)
    wz=55,  # 적응형 임계값 처리에 사용할 윈도우 크기 (축소된 픽셀 단위)
    zoom=1.0,  # 원본 이미지 대비 출력 이미지의 확대율
    dpi=300,  # PNG 파일의 명시적 DPI 값 (메타데이터만)
    decimate=16,  # 이미지 리매핑 시 다운스케일링 인수
    no_bin=0,  # True: 그레이스케일 유지, False: 이진화 수행
    pdf=False,  # 처리된 이미지들을 PDF로 병합 여부 (미구현)
    rv_idx=(0,3),  # 매개변수 벡터에서 회전 벡터(rvec)의 인덱스 범위
    tv_idx=(3,6),  # 매개변수 벡터에서 이동 벡터(tvec)의 인덱스 범위
    cv_idx=(6,8),  # 매개변수 벡터에서 큐빅 기울기의 인덱스 범위
    span_w=30,  # 스팬의 최소 폭 (축소된 픽셀 단위)
    span_step=20,  # 스팬을 따라 샘플링할 때의 픽셀 간격 (축소된 픽셀 단위)
):    
        
    input_path = Path(input).resolve()
    output_dir = Path(output).resolve()
    output_name = name
    
    if not input_path.exists():
        print(f"파일 못 찾음: {input_path}")
        return 1
    
    output_dir.mkdir(exist_ok=True, parents=True)
    result_num = get_next_result_directory(output_dir=output_dir, output_name=output_name)
    result_dir = output_dir / f"{output_name}{result_num}"
    result_dir.mkdir(exist_ok=True)
    
    img = cv2.imread(str(input_path))
    if img is None:
        print(f"이미지 못 찾음: {input_path}")
        return 1
    
    print(f"이미지 크기: {img.shape[1]}x{img.shape[0]}")
    
    config = Config()
    config.FOCAL_LENGTH = focal  # 카메라의 정규화된 초점거리

    config.TEXT_MIN_WIDTH = tw  # 검출할 텍스트 윤곽선의 최소 폭 (축소된 픽셀 단위)
    config.TEXT_MIN_HEIGHT = th  # 검출할 텍스트 윤곽선의 최소 높이 (축소된 픽셀 단위)
    config.TEXT_MIN_ASPECT = ta  # 텍스트 윤곽선의 최소 가로세로 비율 (폭/높이)
    config.TEXT_MAX_THICKNESS = tk  # 검출할 텍스트 윤곽선의 최대 두께 (축소된 픽셀 단위)

    config.DEBUG_LEVEL = debug  # 디버그 레벨 0 ~ 3
    config.DEBUG_OUTPUT = debug_out  # 디버그 출력 방식: "file", "screen", "both"

    config.EDGE_MAX_OVERLAP = eo  # 스팬 내에서 윤곽선들의 최대 수평 겹침 (축소된 픽셀 단위)
    config.EDGE_MAX_LENGTH = el  # 윤곽선들을 연결하는 에지의 최대 길이 (축소된 픽셀 단위)
    config.EDGE_ANGLE_COST = ec  # 에지의 각도 변화에 대한 비용 (길이 대비 각도의 가중치)
    config.EDGE_MAX_ANGLE = ea  # 윤곽선들 사이에서 허용되는 최대 각도 변화 (도 단위)

    config.SCREEN_MAX_W = sw  # 화면 표시용 최대 폭 (픽셀)
    config.SCREEN_MAX_H = sh  # 화면 표시용 최대 높이 (픽셀)
    config.PAGE_MARGIN_X = mx  # 좌우 가장자리에서 무시할 픽셀 수 (축소된 이미지 기준)
    config.PAGE_MARGIN_Y = my  # 상하 가장자리에서 무시할 픽셀 수 (축소된 이미지 기준)

    config.ADAPTIVE_WINSZ = wz  # 적응형 임계값 처리에 사용할 윈도우 크기 (축소된 픽셀 단위)

    config.OUTPUT_ZOOM = zoom  # 원본 이미지 대비 출력 이미지의 확대율
    config.OUTPUT_DPI = dpi  # PNG 파일의 명시적 DPI 값 (메타데이터만)
    config.REMAP_DECIMATE = decimate  # 이미지 리매핑 시 다운스케일링 인수
    config.NO_BINARY = no_bin  # True: 그레이스케일 유지, False: 이진화 수행

    config.CONVERT_TO_PDF = pdf  # 처리된 이미지들을 PDF로 병합 여부 (미구현)

    config.RVEC_IDX = rv_idx  # 매개변수 벡터에서 회전 벡터(rvec)의 인덱스 범위
    config.TVEC_IDX = tv_idx  # 매개변수 벡터에서 이동 벡터(tvec)의 인덱스 범위
    config.CUBIC_IDX = cv_idx  # 매개변수 벡터에서 큐빅 기울기의 인덱스 범위

    config.SPAN_MIN_WIDTH = span_w  # 스팬의 최소 폭 (축소된 픽셀 단위)
    config.SPAN_PX_PER_STEP = span_step  # 스팬을 따라 샘플링할 때의 픽셀 간격 (축소된 픽셀 단위)

    
    original_cwd = os.getcwd()
    os.chdir(result_dir)
    
    warped_img = WarpedImage(str(input_path), config=config)
    
    if warped_img.written:        
        input_copy_path = result_dir / f"원본_{input_path.name}"
        shutil.copy2(input_path, input_copy_path)
        
        # OCR 적용
        result_img_path = result_dir / warped_img.outfile
        ocr_text, debug_dir = perform_ocr(result_img_path, result_dir)

        result = cv2.imread(str(warped_img.outfile))
        
        window_name = f"result"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, result)
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("디워핑 처리가 실패. 텍스트 또는 라인이 충분히 감지되지 않음.")
        
    os.chdir(original_cwd)
    
    print(f"처리 완료")
    return 0

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", "-i", type=str, default="./input/test1.jpg", help="input: 입력 이미지 파일 경로")
    parser.add_argument("--output", "-o", type=str, default="./output", help="output: 출력 디렉토리")
    parser.add_argument("--name", "-n", type=str, default="result", help="name: 결과 폴더명 접두사")
    
    parser.add_argument("--focal", "-f", type=float, default=1.2, help="focal_length: 카메라의 정규화된 초점거리")
    
    parser.add_argument("--tw", type=int, default=15, help="text_min_width: 텍스트 윤곽선 최소 폭 (픽셀)")
    parser.add_argument("--th", type=int, default=2, help="text_min_height: 텍스트 윤곽선 최소 높이 (픽셀)")
    parser.add_argument("--ta", type=float, default=1.5, help="text_min_aspect: 텍스트 최소 가로세로 비율")
    parser.add_argument("--tk", type=int, default=10, help="text_max_thickness: 텍스트 최대 두께 (픽셀)")

    parser.add_argument("--debug", "-d", type=int, default=3, choices=[0, 1, 2, 3], help="debug_level: 디버그 레벨 (0=없음, 1=기본, 2=중간, 3=상세)")
    parser.add_argument("--debug-out", type=str, default="both", choices=["file", "screen", "both"], help="debug_output: 디버그 출력 방식")

    parser.add_argument("--eo", type=float, default=1.0, help="edge_max_overlap: 윤곽선 최대 수평 겹침 (픽셀)")
    parser.add_argument("--el", type=float, default=150.0, help="edge_max_length: 에지 최대 연결 길이 (픽셀)")
    parser.add_argument("--ec", type=float, default=10.0, help="edge_angle_cost: 에지 각도 변화 비용 계수")
    parser.add_argument("--ea", type=float, default=15.0, help="edge_max_angle: 허용 최대 각도 변화 (도)")
    
    parser.add_argument("--sw", type=int, default=1280, help="screen_max_w: 화면 표시용 최대 폭 (픽셀)")
    parser.add_argument("--sh", type=int, default=700, help="screen_max_h: 화면 표시용 최대 높이 (픽셀)")
    parser.add_argument("--mx", type=int, default=10, help="page_margin_x: 좌우 가장자리 무시 영역 (픽셀)")
    parser.add_argument("--my", type=int, default=5, help="page_margin_y: 상하 가장자리 무시 영역 (픽셀)")
    
    parser.add_argument("--wz", type=int, default=35, help="adaptive_winsz: 적응형 임계값 윈도우 크기 (픽셀)")
    
    parser.add_argument("--zoom", "-z", type=float, default=1.0, help="output_zoom: 출력 이미지 확대/축소 비율")
    parser.add_argument("--dpi", type=int, default=300, help="output_dpi: PNG 파일 DPI 메타데이터")
    parser.add_argument("--decimate", type=int, default=16, help="remap_decimate: 리매핑시 다운스케일링 인수")
    parser.add_argument("--no-bin", type=int, default=0, help="no_binary: 이진화 비활성화 (그레이스케일 유지)")
    
    parser.add_argument("--pdf", "-p", action="store_true", help="convert_to_pdf: 결과를 PDF로 변환 (미구현)")
    
    parser.add_argument("--rv-idx", type=int, nargs=2, default=[0, 3], help="rvec_idx: 회전벡터 매개변수 인덱스 범위 (시작, 끝)")
    parser.add_argument("--tv-idx", type=int, nargs=2, default=[3, 6], help="tvec_idx: 이동벡터 매개변수 인덱스 범위 (시작, 끝)")
    parser.add_argument("--cv-idx", type=int, nargs=2, default=[6, 8], help="cubic_idx: 큐빅 기울기 인덱스 범위 (시작, 끝)")

    parser.add_argument("--span-w", type=int, default=30, help="span_min_width: 스팬의 최소 폭 (픽셀)")
    parser.add_argument("--span-step", type=int, default=20, help="span_px_per_step: 스팬 샘플링 간격 (픽셀)")
    
    opt = parser.parse_args()
    print(opt)
    return opt

if __name__ == "__main__":
    opt = parse_args()
    main(**vars(opt))
    #sys.exit(main())