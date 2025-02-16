import { router_main } from "../../router.js";
import { create_sideBar } from "../../utils/sideBar.js";
import { checkDuplication, createElement } from "../../utils/utils.js";
import { clear_page } from "../../utils/clear_page.js";

var chat_start = false;
var user_chat_count = 0;

const carousel_img_list = [
    '../../../assets/imgs/stock_forecast/carousel_celltrion.svg',
    '../../../assets/imgs/stock_forecast/carousel_hmc.svg',
    '../../../assets/imgs/stock_forecast/carousel_kakao.svg',
    '../../../assets/imgs/stock_forecast/carousel_kia.svg',
    '../../../assets/imgs/stock_forecast/carousel_posco.svg',
    '../../../assets/imgs/stock_forecast/carousel_samsung.svg',
    '../../../assets/imgs/stock_forecast/carousel_skhy.svg'
];

export function stock_forecast_main() {
    chat_start = false;
    clear_page();

    var stock_forecast_container = createElement('div', 'stock_forecast_container', 'stock_forecast_container');
    var stock_forecast_wrapper = createElement('div', 'stock_forecast_wrapper', 'stock_forecast_wrapper');

    var top_title = createElement('img', 'stock_forecast_top_title', 'stock_forecast_top_title');
    top_title.src = '../../../assets/imgs/stock_forecast/title.svg';
    stock_forecast_wrapper.appendChild(top_title);

    var PI_logo = createElement('img', 'stock_forecast_PI_logo', 'stock_forecast_PI_logo');
    PI_logo.src = '../../../assets/logos/logo_wo_background.svg';
    stock_forecast_wrapper.appendChild(PI_logo);

    var chat_wrapper = createElement('div', 'stock_forecast_chat_wrapper', 'stock_forecast_chat_wrapper');
    stock_forecast_wrapper.appendChild(chat_wrapper);

    var infinite_carousel = createElement('div', 'stock_forecast_carousel', 'stock_forecast_carousel');
    var carousel_track = createElement('div', 'carousel_track', 'carousel_track');

    for (let i = carousel_img_list.length - 1; i >= carousel_img_list.length - 2; i--) {
        var duplicate_img_start = createElement('img', `carousel_img_dup_start_${i}`, 'carousel_img');
        duplicate_img_start.src = carousel_img_list[i];
        carousel_track.insertBefore(duplicate_img_start, carousel_track.firstChild);
    }

    for (let i = 0; i < carousel_img_list.length; i++) {
        var carousel_img = createElement('img', `carousel_img_${i}`, 'carousel_img');
        carousel_img.src = carousel_img_list[i];
        carousel_track.appendChild(carousel_img);
    }

    for (let i = 0; i < 7; i++) {
        var duplicate_img_end = createElement('img', `carousel_img_dup_end_${i}`, 'carousel_img');
        duplicate_img_end.src = carousel_img_list[i];
        carousel_track.appendChild(duplicate_img_end);
    }

    infinite_carousel.appendChild(carousel_track);
    stock_forecast_wrapper.appendChild(infinite_carousel);

    var chat_input = createElement('textarea', 'stock_forecast_chat_input', 'stock_forecast_chat_input');
    chat_input.placeholder = '관심 종목의 종목명을 입력하면, 종목에 대한 분석 의견을 알려드릴게요!';
    stock_forecast_wrapper.appendChild(chat_input);

    stock_forecast_container.appendChild(stock_forecast_wrapper);
    document.body.appendChild(stock_forecast_container);

    startInfiniteCarousel();
    init_chat();
}

function startInfiniteCarousel() {
    const track = document.querySelector('.carousel_track');
    const images = document.querySelectorAll('.carousel_img');
    const imgWidth = images[0].getBoundingClientRect().width + 10;
    let currentPosition = 0;

    function moveCarousel() {
        currentPosition -= 1;
        if (Math.abs(currentPosition) >= (imgWidth) * (images.length / 2)) {
            currentPosition = 0;
        }
        track.style.transform = `translateX(${currentPosition}px)`;
        requestAnimationFrame(moveCarousel);
    }

    requestAnimationFrame(moveCarousel);
}

async function init_chat() {
    const chatInput = document.querySelector('#stock_forecast_chat_input');
    const chatWrapper = document.getElementById('stock_forecast_chat_wrapper');
    const wrapper = document.getElementById('stock_forecast_wrapper');

    const logo = document.getElementById('stock_forecast_PI_logo');
    const carousel = document.getElementById('stock_forecast_carousel');

    chatInput.addEventListener('keypress', async (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            const userInput = chatInput.value.trim();
            if (userInput === '') return;
            chatInput.value = '';
            user_chat_count += 1;

            if (!chat_start) {
                chat_start = true;
                chatWrapper.style.display = 'flex';
                wrapper.removeChild(logo);
                wrapper.removeChild(carousel);
            }

            // 사용자의 채팅 내용 표시
            console.log(userInput);
            const userChat = createElement('div', `user_chat_${user_chat_count}`, 'user_chat');
            userChat.innerText = userInput;
            chatWrapper.appendChild(userChat);
            chatWrapper.scrollTop = chatWrapper.scrollHeight;

            // 챗봇 응답 대기 UI 구성
            const answerChatWrapper = createElement('div', `answer_chat_${user_chat_count}`, 'answer_chat');
            const chatbotIcon = createElement('img', 'chatbot_icon', 'chatbot_icon');
            chatbotIcon.src = '../../../assets/logos/chatbot_icon.svg';
            answerChatWrapper.appendChild(chatbotIcon);

            const chatbotText = createElement('div', `answer_chat_text_${user_chat_count}`, 'answer_chat_text');
            chatbotText.innerText = '응답 대기 중...';
            answerChatWrapper.appendChild(chatbotText);
            chatWrapper.appendChild(answerChatWrapper);

            try {
                // 백엔드의 /get_raw_info 엔드포인트에 요청
                const response = await fetch("http://localhost:1234/get_raw_info", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ user_input: userInput })
                });
                console.log('정보 요청중');
                const data = await response.json();
                // 최종 응답은 data.result에 담겨 있다고 가정
                let answer = data.result;
                console.log("최종 응답:", answer);

                answer = answer.replaceAll('\n', '<br>');

                chatbotText.innerHTML = answer;
                chatbotText.style.lineHeight = '2vw';
                chatWrapper.scrollTop = chatWrapper.scrollHeight;

            } catch (error) {
                console.error("Error fetching answer:", error);
                chatbotText.innerText = "에러 발생: 답변을 가져올 수 없습니다.";
            }
        }
    });
}
