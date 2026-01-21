import os
import sys
import subprocess
import time
from datetime import datetime

# ==========================================
# 🩺 ISATS v2.x SYSTEM DIAGNOSTIC SCANNER
# ==========================================

TARGET_DIR = "ISATS_Ferrari"
REPORT_FILE = "SYSTEM_AUDIT_REPORT.md"

def log_to_md(f, header, content, status="❌ ERROR"):
    """마크다운 리포트에 로그 기록"""
    icon = "✅" if status == "PASS" else "❌"
    f.write(f"## {icon} {header}\n\n")
    if content:
        f.write(f"```text\n{content}\n```\n\n")
    else:
        f.write("Status: OK (No errors detected)\n\n")
    f.flush()

def check_syntax_and_import(file_path):
    """
    1. 문법 체크 (compilation)
    2. 임포트 체크 (ModuleNotFoundError 확인)
    """
    try:
        # 1. 문법만 체크
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, file_path, 'exec')
    except Exception as e:
        return f"Syntax Error:\n{str(e)}"

    # 2. 임포트 및 초기화 체크 (Dry Run)
    try:
        # 실행 디렉토리를 프로젝트 루트로 잡아야 import 경로가 안 꼬임
        abs_target_dir = os.path.abspath(TARGET_DIR).replace("\\", "/")
        
        # 파일명을 모듈명으로 변환 (예: core/engine.py -> core.engine)
        rel_path = os.path.relpath(file_path, TARGET_DIR)
        module_name = rel_path.replace(os.sep, '.').replace('.py', '')
        
        # 임포트 테스트 명령어
        cmd = [sys.executable, "-c", f"import sys; sys.path.append('{abs_target_dir}'); import {module_name}"]
        
        # 프로젝트 루트에서 실행
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            # 특정 모듈(notifier 등)에서 발생하는 런타임 에러나 임포트 에러 캡처
            return f"Import/Runtime Error (Code {result.returncode}):\n{result.stderr}\n{result.stdout}"
            
    except Exception as e:
        return f"Execution Check Failed:\n{str(e)}"

    return None

def main():
    print(f"🕵️ [Audit] '{TARGET_DIR}' 시스템 정밀 진단 시작...")
    
    # 리포트 파일 초기화
    with open(REPORT_FILE, "w", encoding="utf-8") as report:
        report.write(f"# 🩺 ISATS System Audit Report\n")
        report.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.write(f"**Target:** `{TARGET_DIR}`\n")
        report.write("---\n\n")

        # 1. 파일 목록 수집
        all_files = []
        for root, dirs, files in os.walk(TARGET_DIR):
            for file in files:
                if file.endswith(".py") and "__init__" not in file:
                    all_files.append(os.path.join(root, file))

        print(f"🔍 총 {len(all_files)}개의 파이썬 모듈 발견. 검사 진행 중...\n")

        error_count = 0
        pass_count = 0

        for file_path in all_files:
            relative_path = os.path.relpath(file_path, os.getcwd())
            print(f"   👉 Checking: {relative_path} ... ", end="")
            
            error_msg = check_syntax_and_import(file_path)
            
            if error_msg:
                print("❌ FAIL")
                log_to_md(report, f"File: `{relative_path}`", error_msg, status="FAIL")
                error_count += 1
            else:
                print("✅ PASS")
                pass_count += 1
                
        # 요약 섹션 추가
        report.write("\n---\n")
        report.write("## 📊 Summary\n")
        report.write(f"- **Total Files:** {len(all_files)}\n")
        report.write(f"- **Passed:** {pass_count}\n")
        report.write(f"- **Failed:** {error_count}\n")
        
        if error_count > 0:
            report.write("\n> ⚠️ **Action Required:** 위 에러 로그를 복사하여 AI 개발자에게 수정 요청하십시오.\n")

    print("\n" + "="*50)
    print(f"🎉 진단 완료!")
    print(f"   - 성공: {pass_count}개")
    print(f"   - 실패: {error_count}개")
    print(f"📄 상세 리포트 생성됨: {REPORT_FILE}")
    print("="*50)

if __name__ == "__main__":
    main()
