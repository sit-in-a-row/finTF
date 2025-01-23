import { router_main } from "../../router.js";
import { create_sideBar } from "../../utils/sideBar.js";
import { checkDuplication, createElement } from "../../utils/utils.js";

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
]

export function stock_forecast_main() {
    checkDuplication('landing_main');
    checkDuplication('proj_intro_container');
    checkDuplication('stock_forecast_container');

    const checkSideBar = document.getElementById('sideBar_container');
    if (!checkSideBar) {
        create_sideBar();
    }

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

    // ===== 캐러셀 코드 시작 ===== //
    // Infinite carousel
    var infinite_carousel = createElement('div', 'stock_forecast_carousel', 'stock_forecast_carousel');
    var carousel_track = createElement('div', 'carousel_track', 'carousel_track');

    // Duplicate the last few images to the start
    for (let i = carousel_img_list.length - 1; i >= carousel_img_list.length - 2; i--) {
        var duplicate_img_start = createElement('img', `carousel_img_dup_start_${i}`, 'carousel_img');
        duplicate_img_start.src = carousel_img_list[i];
        carousel_track.insertBefore(duplicate_img_start, carousel_track.firstChild);
    }

    // Original images
    for (let i = 0; i < carousel_img_list.length; i++) {
        var carousel_img = createElement('img', `carousel_img_${i}`, 'carousel_img');
        carousel_img.src = carousel_img_list[i];
        carousel_track.appendChild(carousel_img);
    }

    // Duplicate the first few images to the end
    for (let i = 0; i < 7; i++) {
        var duplicate_img_end = createElement('img', `carousel_img_dup_end_${i}`, 'carousel_img');
        duplicate_img_end.src = carousel_img_list[i];
        carousel_track.appendChild(duplicate_img_end);
    }

    infinite_carousel.appendChild(carousel_track);

    // ===== 캐러셀 코드 끝 ===== //

    stock_forecast_wrapper.appendChild(infinite_carousel);

    var chat_input = createElement('textarea', 'stock_forecast_chat_input', 'stock_forecast_chat_input');
    chat_input.placeholder = '확인하고자 하는 종목명, 혹은 티커를 입력해주세요.';
    stock_forecast_wrapper.appendChild(chat_input);

    stock_forecast_container.appendChild(stock_forecast_wrapper);

    document.body.appendChild(stock_forecast_container);

    // Start the carousel animation
    startInfiniteCarousel();

    // Initialize chat input
    init_chat();
}

function startInfiniteCarousel() {
    const track = document.querySelector('.carousel_track');
    const images = document.querySelectorAll('.carousel_img');
    const imgWidth = images[0].getBoundingClientRect().width + 10; // 이미지 크기 + margin
    let currentPosition = 0;

    function moveCarousel() {
        currentPosition -= 1; // 부드럽게 1px씩 이동

        // Loop back seamlessly
        if (Math.abs(currentPosition) >= (imgWidth) * (images.length / 2)) {
            currentPosition = 0; // Reset position to start
        }

        track.style.transform = 'translateX(`${currentPosition}px`)';
        requestAnimationFrame(moveCarousel);
    }

    requestAnimationFrame(moveCarousel);
}

function init_chat() {
    const chatInput = document.querySelector('#stock_forecast_chat_input');
    const chatWrapper = document.getElementById('stock_forecast_chat_wrapper');
    const wrapper = document.getElementById('stock_forecast_wrapper');

    const logo = document.getElementById('stock_forecast_PI_logo');
    const carousel = document.getElementById('stock_forecast_carousel');

    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // 줄바꿈 방지

            const userInput = chatInput.value.trim(); // 입력값에서 공백 제거
            if (userInput === '') return; // 빈 입력은 무시

            user_chat_count += 1; // 유저 채팅 수 트래킹

            if (!chat_start) {
                chat_start = true;
                chatWrapper.style.display = 'flex';
                wrapper.removeChild(logo);
                wrapper.removeChild(carousel);
            }

            console.log(userInput); // 입력된 텍스트 출력

            // 유저 채팅 띄우기
            const userChat = createElement('div', `user_chat_${user_chat_count}`, 'user_chat');
            userChat.innerText = userInput;
            chatWrapper.appendChild(userChat);

            // 답변 채팅 띄우기
            const answerChatWrapper = createElement('div', `answer_chat_${user_chat_count}`, 'answer_chat');

            const chatbotIcon = createElement('img', 'chatbot_icon', 'chatbot_icon');
            chatbotIcon.src = '../../../assets/logos/chatbot_icon.svg';
            answerChatWrapper.appendChild(chatbotIcon);

            const chatbotText = createElement('div', `answer_chat_text_${user_chat_count}`, 'answer_chat_text');
            chatbotText.innerText = chatbot_answer(userInput);
            answerChatWrapper.appendChild(chatbotText);

            chatWrapper.appendChild(answerChatWrapper);

            chatInput.value = ''; // 입력창 초기화
        }
    });
}

// 추후 챗봇 구현하고 api로 땡겨오는 함수
function chatbot_answer(user_input) {
    return '아직은 챗봇 기능이 완성되지 않았습니다.'
}