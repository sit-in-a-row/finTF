import { router_main } from "../../router.js";
import { create_sideBar } from "../../utils/sideBar.js";
import { checkDuplication, createElement } from "../../utils/utils.js";

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

    stock_forecast_wrapper.appendChild(infinite_carousel);

    var chat_input = createElement('textarea', 'stock_forecast_chat_input', 'stock_forecast_chat_input');
    chat_input.placeholder = '확인하고자 하는 종목명, 혹은 티커를 입력해주세요.';
    stock_forecast_wrapper.appendChild(chat_input);

    stock_forecast_container.appendChild(stock_forecast_wrapper);

    document.body.appendChild(stock_forecast_container);

    // Start the carousel animation
    startInfiniteCarousel();
}

function startInfiniteCarousel() {
    const track = document.querySelector('.carousel_track');
    const images = document.querySelectorAll('.carousel_img');
    const imgWidth = images[0].getBoundingClientRect().width + 16; // 이미지 크기 + margin
    let currentPosition = 0;

    function moveCarousel() {
        currentPosition -= 1; // 부드럽게 1px씩 이동

        // Loop back seamlessly
        if (Math.abs(currentPosition) >= imgWidth * (images.length - 7)) {
            currentPosition = 0; // Reset position to start
        }

        track.style.transform = `translateX(${currentPosition}px)`;
        requestAnimationFrame(moveCarousel);
    }

    requestAnimationFrame(moveCarousel);
}
