import { router_main } from "../../router.js";
import { clear_page } from "../../utils/clear_page.js";
import { create_sideBar } from "../../utils/sideBar.js";
import { checkDuplication, createElement } from "../../utils/utils.js";

// 이동평균(smoothing) 함수: windowSize 기간 동안의 평균을 계산합니다.
function smoothData(data, windowSize) {
    const smoothed = [];
    for (let i = 0; i < data.length; i++) {
        let sum = 0;
        let count = 0;
        for (let j = Math.max(0, i - windowSize + 1); j <= i; j++) {
            sum += data[j];
            count++;
        }
        smoothed.push(sum / count);
    }
    return smoothed;
}

export function profit_main() {
    console.log("profit_main 함수 시작");
    clear_page();

    // =============================
    // 1. 전체 컨테이너 및 레이아웃 구성
    // =============================
    const profit_container = createElement('div', 'profit_container', 'profit_container');
    const profit_wrapper = createElement('div', 'profit_wrapper', 'profit_wrapper');
    profit_container.appendChild(profit_wrapper);
    console.log("profit_container와 profit_wrapper 생성 완료");

    // 페이지 타이틀
    const profit_title = createElement('img', 'profit_title', 'profit_title');
    profit_title.src = '../../../assets/imgs/profit/title.svg';
    profit_wrapper.appendChild(profit_title);
    console.log("페이지 타이틀 추가됨");

    // 메인 레이아웃
    const profit_main_area = createElement('div', 'profit_main_area', 'profit_main_area');

    // 왼쪽 영역 (조회 옵션)
    const profit_left_area = createElement('div', 'profit_left_area', 'profit_left_area');

    // 분기 선택
    const quarterSelect = createElement('select', 'quarter_select', 'quarter_select');
    quarterSelect.innerHTML = `
        <option value="">분기 선택</option>
        <option value="Q1">Q1</option>
        <option value="Q2">Q2</option>
        <option value="Q3">Q3</option>
        <option value="Q4">Q4</option>
    `;
    console.log("분기 선택 요소 생성 및 옵션 추가");

    // 종목 선택
    const tickerSelect = createElement('select', 'ticker_select', 'ticker_select');
    tickerSelect.innerHTML = `<option value="">종목 선택</option>`;
    console.log("종목 선택 요소 생성 및 기본 옵션 추가");

    // 조회 버튼
    const searchButton = createElement('button', 'search_button', 'search_button');
    searchButton.textContent = '조회';
    console.log("조회 버튼 생성");

    // 왼쪽 영역에 옵션 추가
    profit_left_area.appendChild(quarterSelect);
    profit_left_area.appendChild(tickerSelect);
    profit_left_area.appendChild(searchButton);

    // 오른쪽 영역 (차트 & 정보)
    const profit_right_area = createElement('div', 'profit_right_area', 'profit_right_area');

    // 차트 캔버스 (수익률 추이 차트)
    const chartContainer = createElement('canvas', 'tradeChart', 'tradeChart');

    // 포트폴리오 정보 영역
    const portfolioInfo = createElement('div', 'portfolio_info', 'portfolio_info');
    portfolioInfo.innerHTML = `<h3>포트폴리오 성과</h3>`;

    // 종목별 정보 영역
    const tickerInfo = createElement('div', 'ticker_info', 'ticker_info');
    tickerInfo.innerHTML = `<h3>종목별 정보</h3>`;

    profit_right_area.appendChild(chartContainer);
    profit_right_area.appendChild(portfolioInfo);
    profit_right_area.appendChild(tickerInfo);

    // 전체 레이아웃 조립
    profit_main_area.appendChild(profit_left_area);
    profit_main_area.appendChild(profit_right_area);
    profit_wrapper.appendChild(profit_main_area);
    document.body.appendChild(profit_container);
    console.log("전체 레이아웃이 document.body에 추가됨");

    // =============================
    // 2. 종목 선택 옵션 업데이트 함수 (분기 선택에 따라)
    // =============================
    function updateTickerOptions(selectedQuarter) {
        console.log("updateTickerOptions 호출됨 - 선택된 분기:", selectedQuarter);
        // 기본 옵션: "모든 종목"
        tickerSelect.innerHTML = `<option value="all">모든 종목</option>`;

        fetch('/pipeline/portfolio_quarter_results_log.json')
            .then(response => response.json())
            .then(data => {
                console.log("portfolio_quarter_results_log.json 데이터:", data);
                if (data[selectedQuarter]) {
                    Object.keys(data[selectedQuarter]).forEach(ticker => {
                        if (ticker !== "_total") {
                            const option = document.createElement('option');
                            option.value = ticker;
                            option.textContent = ticker;
                            tickerSelect.appendChild(option);
                            console.log("추가된 종목 옵션:", ticker);
                        }
                    });
                } else {
                    console.warn("선택된 분기에 해당하는 데이터가 없습니다:", selectedQuarter);
                }
            })
            .catch(error => {
                console.error("portfolio_quarter_results_log.json fetch 오류:", error);
            });
    }

    // 분기 선택 변경 시 종목 목록 업데이트
    quarterSelect.addEventListener('change', function() {
        console.log("분기 선택 변경됨:", this.value);
        updateTickerOptions(this.value);
    });

    // =============================
    // 3. 조회 버튼 클릭 시 데이터 fetch 및 업데이트
    // =============================
    searchButton.addEventListener('click', () => {
        const selectedQuarter = quarterSelect.value;
        const selectedTicker = tickerSelect.value;
        console.log("조회 버튼 클릭 - 선택된 분기:", selectedQuarter, ", 선택된 종목:", selectedTicker);

        if (!selectedQuarter || !selectedTicker) {
            console.warn("분기와 종목 모두 선택되지 않음.");
            alert("분기와 종목을 선택하세요.");
            return;
        }

        // (1) 포트폴리오 데이터 업데이트
        fetch('/pipeline/portfolio_quarter_results_log.json')
            .then(response => response.json())
            .then(portfolioData => {
                console.log("portfolio_quarter_results_log.json fetch 성공:", portfolioData);
                const portfolioInfoData = selectedTicker === "all" 
                    ? portfolioData[selectedQuarter] 
                    : { [selectedTicker]: portfolioData[selectedQuarter][selectedTicker] };
                console.log("업데이트할 포트폴리오 데이터:", portfolioInfoData);
                updatePortfolioInfo(portfolioInfoData);
            })
            .catch(error => {
                console.error("portfolio_quarter_results_log.json fetch 오류:", error);
            });

        // (2) 종목별 데이터 업데이트
        fetch('/pipeline/ticker_quarter_results_log.json')
            .then(response => response.json())
            .then(tickerData => {
                console.log("ticker_quarter_results_log.json fetch 성공:", tickerData);
                const tickerInfoData = selectedTicker === "all" 
                    ? tickerData[selectedQuarter] 
                    : { [selectedTicker]: tickerData[selectedQuarter][selectedTicker] };
                console.log("업데이트할 종목별 데이터:", tickerInfoData);
                updateTickerInfo(tickerInfoData);
            })
            .catch(error => {
                console.error("ticker_quarter_results_log.json fetch 오류:", error);
            });
        
        // (3) 일별 수익률 데이터 업데이트 (차트)
        // 수익률 추이 차트를 그리기 위해 daily_profit_rate_log.json 파일을 사용합니다.
        fetch('/pipeline/daily_profit_rate_log.json')
            .then(response => response.json())
            .then(dailyProfitData => {
                console.log("daily_profit_rate_log.json fetch 성공:", dailyProfitData);
                updateProfitRateChart(dailyProfitData, selectedTicker, selectedQuarter);
            })
            .catch(error => {
                console.error("daily_profit_rate_log.json fetch 오류:", error);
            });
    });

    // =============================
    // 4. 포트폴리오 정보 업데이트 함수
    // =============================
    function updatePortfolioInfo(info) {
        console.log("포트폴리오 정보 업데이트 - data:", info);
        portfolioInfo.innerHTML = "<h3>포트폴리오 성과</h3>"; // 초기화

        Object.keys(info).forEach(ticker => {
            if (ticker === "_total") return; // 총합 정보는 제외
            const div = document.createElement("div");
            div.innerHTML = `
                <h4>종목: ${ticker}</h4>
                <p>수익: ${Math.round(info[ticker].profit).toLocaleString()}원</p>
                <p>수익률: ${Math.round(info[ticker].profit_rate.toFixed(2))}%</p>
            `;
            portfolioInfo.appendChild(div);
            console.log("포트폴리오 정보에 추가됨:", ticker);
        });
    }

    // =============================
    // 5. 종목별 정보 업데이트 함수
    // =============================
    function updateTickerInfo(info) {
        console.log("종목별 정보 업데이트 - data:", info);
        tickerInfo.innerHTML = "<h3>종목별 정보</h3>"; // 초기화

        Object.keys(info).forEach(ticker => {
            const div = document.createElement("div");
            div.innerHTML = `
                <h4>종목: ${ticker}</h4>
                <p>최종 평가액: ${info[ticker].final_value.toLocaleString()}원</p>
                <p>마지막 거래 가격: ${info[ticker].last_trade_price.toLocaleString()}원</p>
            `;
            tickerInfo.appendChild(div);
            console.log("종목별 정보에 추가됨:", ticker);
        });
    }

    // =============================
    // 6. 일별 수익률 추이 차트 업데이트 함수 (선택한 분기에 해당하는 날짜만 사용, smoothing 적용)
    // =============================
    function updateProfitRateChart(dailyProfitData, selectedTicker, selectedQuarter) {
        // 분기에 해당하는 달을 정의 (Q1: 01~03, Q2: 04~06, Q3: 07~09, Q4: 10~12)
        const quarterMonths = {
            "Q1": ["01", "02", "03"],
            "Q2": ["04", "05", "06"],
            "Q3": ["07", "08", "09"],
            "Q4": ["10", "11", "12"]
        };

        // 전체 날짜(키)를 오름차순 정렬
        const allDates = Object.keys(dailyProfitData).sort();
        // 선택한 분기에 해당하는 달만 필터링 (날짜 형식은 "YYYYMMDD"라고 가정)
        const selectedMonths = quarterMonths[selectedQuarter] || [];
        const filteredDates = allDates.filter(date => {
            const month = date.substr(4, 2);
            return selectedMonths.includes(month);
        });

        const labels = filteredDates;  
        const profitRates = filteredDates.map(date => {
            const dayData = dailyProfitData[date];
            if (selectedTicker === "all") {
                return dayData["_total"] !== undefined ? dayData["_total"] : 0;
            } else {
                return dayData[selectedTicker] !== undefined ? dayData[selectedTicker] : 0;
            }
        });
        console.log("차트 날짜 (선택된 분기):", labels);
        console.log("원본 차트 수익률 데이터:", profitRates);

        // smoothing 처리: 예를 들어, 3일 이동평균 사용 (windowSize는 필요에 따라 조정 가능)
        const windowSize = 3;
        const smoothedProfitRates = smoothData(profitRates, windowSize);
        console.log("smoothing 처리된 수익률 데이터:", smoothedProfitRates);

        // 차트 생성 영역
        const ctx = document.getElementById("tradeChart").getContext("2d");
        // 기존 차트 인스턴스가 있다면 파괴
        if (window.tradeChartInstance) {
            window.tradeChartInstance.destroy();
            console.log("기존 차트 인스턴스 파괴됨");
        }

        // Chart.js를 사용하여 선(Line) 차트 생성 (smoothing 처리된 데이터 사용)
        window.tradeChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "수익률 추이",
                    data: smoothedProfitRates,
                    borderColor: "#B50000",
                    fill: false
                }]
            },
            options: {
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "날짜"
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: "수익률 (%)"
                        }
                    }
                }
            }
        });
        console.log("수익률 추이 차트 생성됨");
    }
}
