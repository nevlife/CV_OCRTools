import cv2
import numpy as np
import pytesseract
import os

# Tesseract 경로 지정 (윈도우 환경)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def order_points(pts):
    """
    4개의 점(pts: shape=(4,2))을
    (top-left, top-right, bottom-right, bottom-left) 순으로 정렬
    """
    rect = np.zeros((4, 2), dtype="float32")
    s    = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def preprocess_image_with_visualization(image,
                                        show_steps=True,
                                        wait_key=0):
    """
    영수증 검출을 위한 이미지 전처리 + 시각화 + OCR
    Returns:
      original: 원본 BGR 이미지
      gray: 그레이스케일
      closed_edges: 8단계 닫힘 연산 결과
      result_images: 단계별 이미지 dict
      ocr_edges_text: 6단계 엣지 원근 변환 후 OCR 결과(str)
      ocr_scan_text: 9단계 스캔(warped) 이미지 OCR 결과(str)
    """
    result_images = {}
    ocr_edges_text = ""
    ocr_scan_text  = ""

    # 1. 원본
    original = image.copy()
    result_images["1. 원본 이미지"] = original

    # 2. 그레이
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result_images["2. 그레이스케일"] = gray

    # 3. CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    clahe_img = clahe.apply(gray)
    result_images["3. CLAHE 대비 향상"] = clahe_img

    # 4. Gaussian Blur
    blurred = cv2.GaussianBlur(clahe_img, (5,5), 0)
    result_images["4. 가우시안 블러"] = blurred

    # 5. Adaptive Threshold (Otsu 대신)
    binary = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15, C=5)
    result_images["5. 이진화 (Adaptive)"] = binary

    # 6. Canny Edge
    edges = cv2.Canny(binary, 30, 150)
    result_images["6. 캐니 엣지 검출"] = edges

    # -- 6단계 엣지 warp & OCR --
    # 추후에 계산될 M, maxW, maxH를 임시 보관할 변수
    warped_edges = None
    # M, maxW, maxH 정의 전용 플래그
    has_warp_matrix = False

    # 이하 7,8단계를 거친 뒤 9단계에서 M을 얻은 뒤 다시 돌아와 6단계 warp 수행

    # 7. Dilate
    kernel = np.ones((5,5), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations=2)
    result_images["7. 팽창 연산"] = dilated_edges

    # 8. Close
    closed_edges = cv2.morphologyEx(
        dilated_edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    result_images["8. 닫힘 연산"] = closed_edges

    # 8.1 Invert for black-area contours
    closed_inv = cv2.bitwise_not(closed_edges)
    result_images["8.1 뒤집힌 이미지"] = closed_inv

    # 9. Contour 탐색 → M 계산 → scan warp → OCR
    contours, _ = cv2.findContours(
        closed_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    warped_scan = None
    for cnt in contours[:5]:
        area = cv2.contourArea(cnt)
        if area < 1000:
            continue

        peri  = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        # 4점 근사 확인
        if len(approx) == 4:
            pts  = approx.reshape(4,2).astype("float32")
            rect = order_points(pts)

            # 대상 크기 계산
            (tl, tr, br, bl) = rect
            widthA  = np.linalg.norm(br - bl)
            widthB  = np.linalg.norm(tr - tl)
            maxW    = int(max(widthA, widthB))
            heightA = np.linalg.norm(tr - br)
            heightB = np.linalg.norm(tl - bl)
            maxH    = int(max(heightA, heightB))

            # 목적 좌표 설정
            dst = np.array([
                [0, 0],
                [maxW-1, 0],
                [maxW-1, maxH-1],
                [0, maxH-1]
            ], dtype="float32")

            # 변환 행렬 & scan warp
            M = cv2.getPerspectiveTransform(rect, dst)
            warped_scan = cv2.warpPerspective(image, M, (maxW, maxH))
            result_images["9. 스캔된 영수증 (원근 변환)"] = warped_scan

            # OCR: scan image
            ocr_scan_text = pytesseract.image_to_string(
                warped_scan, lang='kor+eng',
                config='--oem 1 --psm 3')
            print("[OCR @ Step9]\n", ocr_scan_text)

            # 여기에 6단계 엣지 warp도 수행
            warped_edges = cv2.warpPerspective(edges, M, (maxW, maxH))
            result_images["6. 스캔된 엣지 원근 변환"] = warped_edges
            ocr_edges_text = pytesseract.image_to_string(
                warped_edges, lang='kor+eng',
                config='--oem 1 --psm 3')
            print("[OCR @ Step6 on warped edges]\n", ocr_edges_text)

            has_warp_matrix = True
            break

    # 디버그 시각화 (상위 컨투어 + approx)
    debug_vis = cv2.cvtColor(closed_inv, cv2.COLOR_GRAY2BGR)
    for i, cnt in enumerate(contours[:5]):
        peri   = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        cv2.drawContours(debug_vis, [cnt], -1, (0,200,200), 2)
        for p in approx.reshape(-1,2):
            cv2.circle(debug_vis, tuple(p), 5, (0,0,255), -1)
    result_images["DEBUG: Contours"] = debug_vis

    # 단계별 결과 표시
    if show_steps:
        for title, img in result_images.items():
            cv2.imshow(title, img)
        cv2.waitKey(wait_key)
        if wait_key == 0:
            cv2.destroyAllWindows()

    return (original, gray, closed_edges, result_images,
            ocr_edges_text, ocr_scan_text)

# 스크립트 실행 예
def main():
    img_path = './data/image/receipt_00000.png'
    img = cv2.imread(img_path)
    if img is None:
        print("이미지 로드 실패:", img_path)
        return

    (orig, gray, closed,
     steps, ocr6, ocr9) = preprocess_image_with_visualization(
        img, show_steps=True, wait_key=0)

    # OCR 텍스트 결과 파일로 저장
    with open('./data/debug/ocr_results.txt', 'w', encoding='utf-8') as f:
        f.write("=== OCR on warped edges (Step6) ===\n")
        f.write(ocr6 + "\n\n")
        f.write("=== OCR on final scan (Step9) ===\n")
        f.write(ocr9 + "\n")
    print("OCR 결과 저장: ./data/debug/ocr_results.txt")

if __name__ == '__main__':
    main()
