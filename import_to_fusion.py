"""
ENDOCRAB Fusion 360 Launcher
============================
이 스크립트는 두 가지 방법으로 사용할 수 있습니다:

방법 1 (권장): 직접 빌더 실행
  → Fusion 360 > Scripts & Add-ins > + > src/build_endocrab_model.py 등록 후 실행
  → 파라메트릭 어셈블리가 직접 생성됩니다.

방법 2: STEP 파일 임포트
  → build123d로 생성된 STEP 파일을 가져옵니다.
"""

import adsk.core, adsk.fusion, traceback
import os
import sys

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct

        if not design or not isinstance(design, adsk.fusion.Design):
            ui.messageBox('Fusion 360 활성 문서(Design)를 먼저 열어주세요.')
            return

        # 방법 1: ENDOCRAB 빌더 직접 실행 시도
        builder_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "src", "build_endocrab_model.py"
        )

        if os.path.exists(builder_path):
            # 빌더 모듈의 디렉토리를 sys.path에 추가
            builder_dir = os.path.dirname(builder_path)
            if builder_dir not in sys.path:
                sys.path.insert(0, builder_dir)

            import build_endocrab_model
            build_endocrab_model.run(context)
            return

        # 방법 2: STEP 파일 가져오기 (Fallback)
        step_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "output", "endo_bracket.step"
        )

        if not os.path.exists(step_path):
            ui.messageBox(
                f'ENDOCRAB 빌더 또는 STEP 파일을 찾을 수 없습니다.\n\n'
                f'빌더: {builder_path}\n'
                f'STEP: {step_path}\n\n'
                f'src/build_endocrab_model.py를 Fusion 360 스크립트로 직접 등록하세요.'
            )
            return

        import_manager = app.importManager
        step_options = import_manager.createSTEPImportOptions(step_path)
        root_comp = design.rootComponent
        import_manager.importToTarget(step_options, root_comp)

        ui.messageBox(f'🎉 STEP 모델 가져오기 성공!\n\n경로: {step_path}')

    except:
        if ui:
            ui.messageBox('오류 발생:\n{}'.format(traceback.format_exc()))
