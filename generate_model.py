import os
import sys
from build123d import *

# Windows 콘솔 인코딩 방어
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def create_endo_bracket(
    length: float = 80.0,
    width: float = 50.0,
    thickness: float = 10.0,
    hole_radius: float = 8.0,
    post_height: float = 20.0,
    fillet_radius: float = 4.0
) -> Part:
    """
    build123d를 이용한 파라메트릭 의료/메카트로닉스 브래킷 생성 함수
    """
    print(f"[build123d] 3D 형상 연산 시작 (길이:{length}mm, 너비:{width}mm, 두께:{thickness}mm)...")

    # 1. Builder Mode (Context Manager) 사용
    with BuildPart() as bracket:
        # 베이스 2D 평면 스케치
        with BuildSketch(Plane.XY):
            Rectangle(length, width)
            # 양 끝에 고정용 구멍 2개 추가 (Subtractive)
            with Locations((-length / 3, 0), (length / 3, 0)):
                Circle(hole_radius, mode=Mode.SUBTRACT)
        
        # 3D 돌출
        extrude(amount=thickness)

        # 상단 마운팅 기둥 추가
        top_face = bracket.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top_face):
            Circle(width / 4)
            Circle(hole_radius / 2, mode=Mode.SUBTRACT)  # 기둥 중앙 관통홀
        extrude(amount=post_height, mode=Mode.ADD)

        # 수직 모서리 필렛(라운딩) 처리
        vert_edges = bracket.edges().filter_by(Axis.Z)
        fillet(vert_edges, radius=fillet_radius)

    return bracket.part

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # 3D 파트 생성
    part = create_endo_bracket()

    # 1. STEP 파일 내보내기 (Fusion 360 연동용 정밀 CAD 포맷)
    step_path = os.path.join(output_dir, "endo_bracket.step")
    export_step(part, step_path)
    print(f"[SUCCESS] STEP 파일 내보내기 완료: {step_path}")

    # 2. STL 파일 내보내기 (3D 프린팅용 메쉬 포맷)
    stl_path = os.path.join(output_dir, "endo_bracket.stl")
    export_stl(part, stl_path)
    print(f"[SUCCESS] STL 파일 내보내기 완료: {stl_path}")

    # 3. 2D SVG 투상도 내보내기 (레이저 커팅/도면용)
    svg_path = os.path.join(output_dir, "endo_bracket.svg")
    exporter = ExportSVG()
    exporter.add_shape(part)
    exporter.write(svg_path)
    print(f"[SUCCESS] SVG 도면 내보내기 완료: {svg_path}")

    print("\n[COMPLETE] 모든 CAD 데이터 생성이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()
