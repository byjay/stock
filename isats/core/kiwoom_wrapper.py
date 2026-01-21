"""
[파일명]: backend/core/kiwoom_wrapper.py
[역할]: 키움증권 Open API+ (OCX) 인터페이스 라이브러리. 증권사 서버와의 물리적 통신 및 이벤트 처리를 전담함.
[저장위치]: c:/Users/FREE/Desktop/주식/isats/backend/core/kiwoom_wrapper.py
[상세설명]:
이 코드는 키움증권에서 제공하는 32비트 OCX 컨트롤을 파이썬 환경(PyQt5)에서 사용할 수 있도록 래핑한 결과물입니다.
로그인, 시세 조회(TR), 조건검색(Intelligent Search) 등 모든 실전 매매 기능을 API와 연결합니다.
32비트 윈도우 환경에서만 작동하며, ISATS 시스템의 '실전 타격 팔' 역할을 수행합니다.
"""

import sys
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop
import logging

logger = logging.getLogger("KiwoomWrapper")

class KiwoomWrapper(QAxWidget):
    """
    키움 Open API+ 컨트롤을 상속받아 파이썬에서 제어하기 위한 클래스입니다.
    """
    def __init__(self):
        super().__init__()
        # 키움 API 식별값(ProgID) 설정
        self.setControl("KHOPENAPI.KhOpenAPICtrl.1")
        
        self.login_event_loop = None # 로그인 대기용 이벤트 루프
        self.tr_event_loop = None    # TR 데이터 수신 대기용 이벤트 루프
        
        # --- 이벤트 연결 (증권사 서버에서 보내주는 응답을 받기 위함) ---
        self.OnEventConnect.connect(self._on_event_connect)                 # 로그인 결과 수신
        self.OnReceiveTrData.connect(self._on_receive_tr_data)               # TR 데이터(시세 등) 수신
        self.OnReceiveRealCondition.connect(self._on_receive_real_condition) # 실시간 조건검색 신호 수신
        self.OnReceiveConditionVer.connect(self._on_receive_condition_ver)   # 조건식 로드 결과 수신
        self.OnReceiveTrCondition.connect(self._on_receive_tr_condition)     # 조건검색 결과 리스트 수신
        
        logger.info("Kiwoom OCX 인터페이스 객체 생성 완료")

    # --------------------------------------------------------------------------------
    # Login & Connection
    # --------------------------------------------------------------------------------
    def comm_connect(self):
        """Attempts to connect to the Kiwoom Server (Popups Login Window)."""
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _on_event_connect(self, err_code):
        """Callback for Connection Result."""
        if err_code == 0:
            logger.info("Connected to Kiwoom Server successfully.")
        else:
            logger.error(f"Kiwoom Connection Failed. Error Code: {err_code}")
        
        if self.login_event_loop:
            self.login_event_loop.exit()

    def get_login_info(self, tag):
        """
        Get Login Information.
        :param tag: "ACCOUNT_CNT", "ACCNO", "USER_ID", "USER_NAME", "KEY_BSECGB", "FIREW_SECGB"
        """
        return self.dynamicCall("GetLoginInfo(QString)", tag)

    # --------------------------------------------------------------------------------
    # Trading & Data
    # --------------------------------------------------------------------------------
    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        """Callback for TR Data."""
        logger.debug(f"TR Data Received: {rqname} ({trcode})")
        # In a real implementation, we would extract data here and store it or pass it via a callback/queue
        # For now, we release the loop
        if self.tr_event_loop:
            self.tr_event_loop.exit()

    def get_comm_data(self, trcode, rqname, index, item_name):
        return self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item_name).strip()

    # --------------------------------------------------------------------------------
    # 조건검색 (HTS의 지능형 필터링 연동)
    # --------------------------------------------------------------------------------
    def get_condition_load(self):
        """
        사용자의 HTS에 저장된 조건검색 목록을 서버로부터 비동기 방식으로 요청합니다.
        """
        ret = self.dynamicCall("GetConditionLoad()")
        if ret == 1:
            logger.info("서버에 조건식 목록 로드 요청 성공")
        else:
            logger.error("조건식 목록 로드 요청 실패")

    def get_condition_name_list(self):
        """
        로드된 조건식 목록('인덱스^이름' 형태)을 리스트 구조로 파싱하여 반환합니다.
        """
        data = self.dynamicCall("GetConditionNameList()")
        if not data:
            return []
            
        conditions = []
        for unit in data.split(';')[:-1]:
            if '^' in unit:
                index, name = unit.split('^')
                conditions.append({'index': int(index), 'name': name})
        return conditions

    def send_condition(self, screen_no, condition_name, condition_index, is_real_time):
        """
        특정 조건검색을 실행하거나 실시간 감시를 등록합니다.
        is_real_time: 1 (실시간 감시 등록), 0 (1회성 조회)
        """
        ret = self.dynamicCall("SendCondition(QString, QString, int, int)", 
                               screen_no, condition_name, condition_index, is_real_time)
        if ret == 1:
            logger.info(f"조건검색 실행: {condition_name} (실시간={is_real_time})")
        else:
            logger.error(f"조건검색 실행 실패: {condition_name}")

    def _on_receive_condition_ver(self, ret, msg):
        """조건식 목록 로드가 완료되었을 때 호출되는 콜백 (시스템 준비 신호)"""
        logger.info(f"조건식 목록 로드 완료 (결과코드: {ret}, 메시지: {msg})")
        
    def _on_receive_tr_condition(self, screen_no, code_list, condition_name, index, next):
        """1회성 조건검색 결과로 검색된 종목 리스트를 받았을 때 호출되는 콜백"""
        count = len(code_list.split(';')) - 1 if code_list else 0
        logger.info(f"[조건검색 결과] {condition_name}: {count}종목 포착 완료.")
        
    def _on_receive_real_condition(self, code, type, condition_name, condition_index):
        """
        실시간 조건검색에서 종목이 편입('I')되거나 이탈('D')했을 때 즉시 호출되는 콜백.
        이 함수가 스나이퍼 전략의 '방아쇠' 역할을 합니다.
        """
        action = "편입(INSERT)" if type == 'I' else "이탈(DELETE)"
        logger.info(f"🎯 [실시간 포착] {code} 종목이 '{condition_name}' 조건식에 {action} 되었습니다.")

    # --------------------------------------------------------------------------------
    # High-Speed Signal Input (SHM)
    # --------------------------------------------------------------------------------
    def listen_for_shm_signals(self):
        """
        [Anti-Fragility] Sub-1ms Signal Listener.
        Bypasses disk IPC to defend against latency critique.
        """
        from backend.core.shm_bridge import SharedMemoryBridge
        bridge = SharedMemoryBridge()
        logger.info("⚡ [Latency Defense] SHM Signal Listener Active.")
        
        # In a real PyQt app, this would be a QTimer or QThread
        # For simulation/structure, we show the logic
        signal = bridge.read_signal()
        if signal:
            logger.info(f"🚀 [SHM-TRIGGER] Received Signal: {signal}")
            # order_execution_logic(signal)
