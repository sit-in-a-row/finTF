import { router_main } from "../../router.js";
import { clear_page } from "../../utils/clear_page.js";
import { create_sideBar } from "../../utils/sideBar.js";
import { checkDuplication, createElement } from "../../utils/utils.js";

// 전역 변수 (날짜와 에이전트 유형, 시간대 토글 선택)
let selected_date = '';
let selected_agent_type = '';
let selected_toggle = '';

const toggle_list = [
    ['Analyst', 'Portfolio Manager', 'Trader'],
    ['개장 이전', '오전장', '중간점', '오후장', '폐장 이후']
];

export function report_main() {
    clear_page();

    var report_container = createElement('div', 'report_container', 'report_container');
    var report_wrapper = createElement('div', 'report_wrapper', 'report_wrapper');
    report_container.appendChild(report_wrapper);

    // 페이지 타이틀 생성
    var report_title = createElement('img', 'report_title', 'report_title');
    report_title.src = '../../../assets/imgs/report/title.svg';
    report_wrapper.appendChild(report_title);

    // 프로그레스바 생성
    var info_bar_container = createElement('div', 'info_bar_container', 'info_bar_container');
    var info_bar_text = createElement('div', 'info_bar_text', 'info_bar_text');
    info_bar_text.innerText = '정보를 불러오는 중입니다...';
    var info_bar_bar = createElement('div', 'info_bar_bar', 'info_bar_bar');
    info_bar_container.appendChild(info_bar_text);
    info_bar_container.appendChild(info_bar_bar);
    report_wrapper.appendChild(info_bar_container);

    // 메인 박스들 생성
    var report_main_area = createElement('div', 'report_main_area', 'report_main_area');

    // 왼쪽 영역 생성
    var report_left_area = createElement('div', 'report_left_area', 'report_left_area');

    // report_calendar 영역: 항상 보이는 date input 추가
    var report_calendar = createElement('div', 'report_calendar', 'report_calendar');
    var dateInput = createElement('input', 'report_date_input', 'report_date_input');
    dateInput.type = 'date';
    // 날짜 변경 시 selected_date 업데이트 후 tryLookupPageId() 호출
    dateInput.addEventListener('change', (event) => {
        console.log("선택한 날짜:", event.target.value);
        selected_date = event.target.value;
        tryLookupPageId();
    });
    report_calendar.appendChild(dateInput);
    report_left_area.appendChild(report_calendar);

    // 토글 리스트 생성 (에이전트 유형 및 시간대)
    var report_toggle_list = createElement('div', 'report_toggle_list', 'report_toggle_list');
    for (let i = 0; i < toggle_list[0].length; i++) {
        var report_toggle_details_tag = createElement('details', `report_toggle_details_tag_${i}`, 'report_toggle_details_tag_');
        var report_toggle_title = createElement('summary', `report_toggle_title_${i}`, 'report_toggle_title');
        report_toggle_title.innerText = toggle_list[0][i];
        report_toggle_details_tag.appendChild(report_toggle_title);

        var report_toggle_ul_tag = createElement('div', `report_toggle_ul_tag_${i}`, 'report_toggle_ul_tag_');
        report_toggle_details_tag.appendChild(report_toggle_ul_tag);
        
        for (let j = 0; j < toggle_list[1].length; j++) {
            var report_toggle_li_tag = createElement('div', `report_toggle_li_tag_${i}_${j}`, 'report_toggle_li_tag');
            report_toggle_li_tag.innerText = toggle_list[1][j];
            // 클릭 시: 에이전트 유형(상단의 i번째 항목)과 토글 시간대 (t_${j+1})를 저장
            report_toggle_li_tag.addEventListener('click', () => {
                console.log(toggle_list[0][i]);
                console.log(`t_${j+1}`);
                selected_agent_type = toggle_list[0][i]; // 예: "Analyst"
                selected_toggle = `t_${j+1}`;             // 예: "t_2"
                tryLookupPageId();
            });
            report_toggle_ul_tag.appendChild(report_toggle_li_tag);
        }
        report_toggle_list.appendChild(report_toggle_details_tag);
    }
    report_left_area.appendChild(report_toggle_list);

    // 오른쪽 영역 생성
    var report_right_area = createElement('div', 'report_right_area', 'report_right_area');
    // report_right_area_temp는 초기 안내 문구용으로 생성 (id로 접근)
    var report_right_area_temp = createElement('div', 'report_right_area_temp', 'report_right_area_temp');
    report_right_area_temp.innerHTML = '조회를 원하는 날짜와 에이전트 유형을 선택해주세요.<br>2023년 중 개장일에 대해 조회가 가능합니다.';
    report_right_area.appendChild(report_right_area_temp);

    report_main_area.appendChild(report_left_area);
    report_main_area.appendChild(report_right_area);
    report_wrapper.appendChild(report_main_area);

    // 바디에 추가
    document.body.appendChild(report_container);
}

/**
 * 선택된 날짜, 에이전트 유형, 토글 값이 모두 있으면,
 * fetch()를 사용하여 JSON 파일을 읽어 조합한 키에 해당하는 페이지 id를 추출한 후,
 * 해당 pageId를 바탕으로 /get_page_text 엔드포인트에 요청하여 노션 페이지의 텍스트를 가져옵니다.
 * - 만약 정상적으로 텍스트를 받아왔다면, report_right_area_temp는 숨기고 report_right_area에 텍스트를 표시합니다.
 * - 만약 JSON에 id가 없으면, report_right_area_temp의 문구를 "조회할 수 있는 보고서가 없습니다."로 변경하고,
 *   report_right_area의 내용을 초기화합니다.
 */
function tryLookupPageId() {
    if (!selected_date || !selected_agent_type || !selected_toggle) return;

    // "2023-01-03" → "20230103"
    let formattedDate = selected_date.replace(/-/g, "");

    // 외부 JSON의 섹션(키) 결정:
    // - 토글이 "t_1"이면 "t_1"
    // - 토글이 "t_2", "t_3", "t_4"이면 "t_2"
    // - 토글이 "t_5"이면 "t_5"
    let outerKey = "";
    if (selected_toggle === "t_1") {
        outerKey = "t_1";
    } else if (selected_toggle === "t_2" || selected_toggle === "t_3" || selected_toggle === "t_4") {
        outerKey = "t_2";
    } else if (selected_toggle === "t_5") {
        outerKey = "t_5";
    }

    // 내부 키 결정: 에이전트 유형에 따라 접미사를 결정
    let agentSuffix = "";
    let agentLower = selected_agent_type.toLowerCase();
    if (agentLower === "analyst") {
        agentSuffix = "analyst_rp";
    } else if (agentLower === "portfolio manager") {
        agentSuffix = "portfolio_report";
    } else if (agentLower === "trader") {
        // 토글이 t_1 또는 t_5일 경우 "trader_report", 그 외에는 "trader_log"
        if (selected_toggle === "t_1" || selected_toggle === "t_5") {
            agentSuffix = "trader_report";
        } else {
            agentSuffix = "trader_log";
        }
    }

    // 최종 키 조합:
    // - 토글이 t_2~t_4이면: {formattedDate}_t_2_t_4_{agentSuffix}
    // - 그 외에는: {formattedDate}_{selected_toggle}_{agentSuffix}
    let fullKey = "";
    if (selected_toggle === "t_2" || selected_toggle === "t_3" || selected_toggle === "t_4") {
        fullKey = `${formattedDate}_t_2_t_4_${agentSuffix}`;
    } else {
        fullKey = `${formattedDate}_${selected_toggle}_${agentSuffix}`;
    }

    // fetch()를 사용하여 JSON 파일을 읽어 notionPageIds 딕셔너리를 얻은 후,
    // outerKey 섹션 내에서 fullKey에 해당하는 페이지 id를 추출
    fetch("../../../pipeline/notion_page_ids.json")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            let pageId = data[outerKey] ? data[outerKey][fullKey] : null;
            if (pageId) {
                console.log("페이지 id:", pageId);
                // 보고서가 있다면, 기존 오른쪽 영역 내용을 초기화
                const reportRightArea = document.getElementsByClassName('report_right_area')[0];
                if (reportRightArea) {
                    reportRightArea.innerText = "";
                }
                // report_right_area_temp 숨김
                const reportRightAreaTemp = document.getElementById('report_right_area_temp');
                if (reportRightAreaTemp) {
                    reportRightAreaTemp.style.display = 'none';
                }
                // pageId가 존재하면 /get_page_text 엔드포인트에 요청하여 노션 페이지 텍스트 가져오기
                return fetch(`http://localhost:1234/get_page_text?pageId=${pageId}`);
            } else {
                console.log("해당 키에 해당하는 페이지 id가 없습니다. (키:", fullKey, ")");
                // 보고서가 없으면, 오른쪽 영역의 내용을 초기화하고 report_right_area_temp에 문구 표시
                const reportRightArea = document.getElementsByClassName('report_right_area')[0];
                if (reportRightArea) {
                    reportRightArea.innerText = "";
                }
                const reportRightAreaTemp = document.getElementById('report_right_area_temp');
                if (reportRightAreaTemp) {
                    reportRightAreaTemp.style.display = 'block';
                    reportRightAreaTemp.innerText = "조회할 수 있는 보고서가 없습니다.";
                }
            }
        })
        .then(response => {
            if (response) {
                if (!response.ok) {
                    throw new Error(`HTTP error when fetching page text! status: ${response.status}`);
                }
                return response.json();
            }
        })
        .then(data => {
            if (data) {
                console.log("노션 페이지 텍스트:", data.text);
                // 노션 페이지 텍스트를 받아왔으면,
                // report_right_area_temp를 숨기고, report_right_area에 텍스트 표시
                const reportRightAreaTemp = document.getElementById('report_right_area_temp');
                if (reportRightAreaTemp) {
                    reportRightAreaTemp.style.display = 'none';
                }
                const reportRightArea = document.getElementsByClassName('report_right_area')[0];
                if (reportRightArea) {
                    reportRightArea.innerText = data.text;
                }
            }
            else {
                const reportRightArea = document.getElementsByClassName('report_right_area')[0];
                reportRightArea.innerText = "조회할 수 있는 보고서가 없습니다.";
            }
        })
        .catch(error => {
            console.error("오류 발생:", error);
        });
}
