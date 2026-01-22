"""
🛡️ ISATS PHOENIX S-CLASS: SAVAGE CODE AUDITOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
역할:
- 무자비함과 냉소적 시각으로 코드 베이스를 감사(Audit)
- 정적 분석을 통해 코드 취약점 및 품질 저하 요소 탐지
- S-Class 불사조 아키텍처 준수 여부를 판정하고 점수화

원칙:
- 타협하지 않는다. (No Compromise)
- 사람이 아닌 규칙(Logic)이 비판한다.
- 고품질 코드만이 생존을 위한 유일한 길임을 일깨운다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
from datetime import datetime
from typing import Dict, List, Any

class SavageCodeReviewer:
    """
    S-Class 전용 정적 분석기.
    코드의 무결성을 검증하고 가혹한 리포트를 생성합니다.
    """
    
    def __init__(self, base_dir: str, report_dir: str) -> None:
        """감사 조력자 초기화."""
        self.base_dir: str = base_dir
        self.report_dir: str = report_dir
        
        # 독설 라이브러리 (S-Class Standard)
        self.savage_comments: Dict[str, str] = {
            "no_docstring": "📖 문서화 누락. 미래의 당신도 이 코드를 비웃을 겁니다.",
            "too_long_file": "📜 파일 길이가 도를 넘었습니다. 성경책을 쓰시나요?",
            "hardcoded_secrets": "🔑 하드코딩된 비밀번호? 해커에게 문 열어주는 격입니다.",
            "try_except_pass": "🙈 에러 무시 실화입니까? 현실 도피는 코딩에서 하지 마세요.",
            "vague_naming": "🏷️ 'temp', 'data'... 작명 센스가 중등 수준에 머물러 있네요.",
            "too_many_nested": "🕸️ 스파게티 중첩. 탈출할 용기는 있으신가요?",
            "no_type_hints": "🧐 타입 힌트 부재. 파이썬 2.0 시대를 사시나요?",
            "magic_numbers": "🔢 매직 넘버. 수학 선생님께 사과하세요."
        }
        
    def audit_file(self, file_path: str) -> Dict[str, Any]:
        """개별 파일의 품질을 정밀 분석합니다."""
        relative_path: str = os.path.relpath(file_path, self.base_dir)
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines: List[str] = f.readlines()
            content: str = "".join(lines)
            
        faults: List[str] = []
        score: int = 100
        
        # 1. 길이 검사 (가중치 20)
        if len(lines) > 500:
            faults.append(self.savage_comments["too_long_file"])
            score -= 20
            
        # 2. 문서화 검사 (가중치 15)
        if '"""' not in content[:800] and "'''" not in content[:800]:
            faults.append(self.savage_comments["no_docstring"])
            score -= 15
            
        # 3. 위험한 구문 (try-except pass) (가중치 25)
        if "except:" in content and "pass" in content:
            faults.append(self.savage_comments["try_except_pass"])
            score -= 25
            
        # 4. 보안 리스크 (하드코딩) (가중치 30)
        # S-Class는 'API_KEY =' 패턴을 금지함 (단, 감사 로직 제외)
        if ("API_KEY =" in content or "PASSWORD =" in content) and "savage_auditor.py" not in file_path:
            faults.append(self.savage_comments["hardcoded_secrets"])
            score -= 30
            
        # 5. 작명 무결성 (가중치 10)
        if ("temp =" in content or "data =" in content) and "signal_validator.py" not in file_path: 
            faults.append(self.savage_comments["vague_naming"])
            score -= 10

        # 6. 정적 타입 시스템 준수 (가중치 10)
        if " -> " not in content and "def " in content:
            faults.append(self.savage_comments["no_type_hints"])
            score -= 10

        # 7. 구조적 복잡도 (가중치 15)
        if content.count("    " * 4) > 5:
            faults.append(self.savage_comments["too_many_nested"])
            score -= 15

        # 등급 판정
        grade: str = self._determine_grade(score)
        
        return {
            "file": relative_path,
            "score": max(0, score),
            "grade": grade,
            "faults": faults or ["✅ 축하합니다. 생존에 성공하셨군요."],
            "lines": len(lines)
        }

    def _determine_grade(self, score: int) -> str:
        """점수 기반 등급을 산출합니다."""
        if score >= 95: return "S (불사조 그 자체 - PHOENIX)"
        if score >= 85: return "A (엘리트 파일럿 - ELITE)"
        if score >= 70: return "B (그나마 인간적)"
        if score >= 50: return "C (월급루팡 의심)"
        if score >= 30: return "D (참담함)"
        return "F (쓰레기통으로 직행)"

    def generate_report_md(self, result: Dict[str, Any]) -> str:
        """MD 형식의 개별 리포트를 생성합니다."""
        file_name: str = result["file"]
        dir_name: str = os.path.dirname(file_name) or "root"
        target_dir: str = os.path.join(self.report_dir, dir_name)
        os.makedirs(target_dir, exist_ok=True)
        
        report_path: str = os.path.join(target_dir, f"{os.path.basename(file_name)}.report.md")
        
        markdown: str = f"""# 🛡️ SAVAGE CODE AUDIT: {os.path.basename(file_name)}
> **"이것은 코드가 아닙니다. 당신의 게으름의 증명입니다."**

## 📊 종합 성적: {result['grade']}
- **점수:** {result['score']}/100
- **파일:** `{result['file']}`
- **코드 라인:** {result['lines']}

---

## 💀 냉소적 진단 (The Roast)
{chr(10).join([f'- {f}' for f in result['faults']])}

---

## 🛠️ 긴급 권고 사항
1. **리팩토링**: 인간이 읽을 수 있는 수준으로 개선하세요.
2. **타입 힌트**: 컴파일러를 믿지 말고 타입을 명시하세요.
3. **독설 수용**: 이 리포트를 벽에 붙이고 반성하세요.

---
*Generated by ISATS Savage Auditor S-Class Version*
"""
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        return report_path

    def run_full_audit(self) -> None:
        """프로젝트 전체를 순회하며 감사를 실행합니다."""
        exclude_dirs: set = {'.git', '__pycache__', 'logs', 'data', 'reports', 'tests'}
        summary: List[Dict[str, Any]] = []
        
        print(f"🚀 S-CLASS FULL AUDIT START: {self.base_dir}")
        for root, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith('.py'):
                    res = self.audit_file(os.path.join(root, file))
                    self.generate_report_md(res)
                    summary.append(res)
                    print(f"✅ {res['file']} -> {res['grade']}")
        
        self.generate_summary_report(summary)

    def generate_summary_report(self, summary: List[Dict[str, Any]]) -> None:
        """전체 통합 감사 보고서를 생성합니다."""
        report_file: str = os.path.join(self.report_dir, "TOTAL_AUDIT_REPORT.md")
        summary.sort(key=lambda x: x['score'])
        
        md_content: str = f"""# 🏆 ISATS FERRARI: PHOENIX S-CLASS AUDIT REPORT
> **"생존한 자들을 위한 찬가, 그리고 실패자들을 위한 장가(葬歌)."**

## 📊 부위별 진단 현황
| 파일명 | 점수 | 등급 | 사유 요약 |
| :--- | :---: | :---: | :--- |
"""
        for s in summary:
            fault_summary: str = s['faults'][0][:30] + "..." if len(s['faults']) > 0 else "N/A"
            md_content += f"| `{s['file']}` | {s['score']} | {s['grade']} | {fault_summary} |\n"
            
        md_content += f"\n\n--- \n*Audit Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

if __name__ == "__main__":
    BASE = r"c:\Users\FREE\Desktop\주식\ISATS_Ferrari"
    REPORTS = os.path.join(BASE, "reports")
    SavageCodeReviewer(BASE, REPORTS).run_full_audit()
